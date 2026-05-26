#!/usr/bin/python3
"""
SSC Pipeline — Download + Transcrição + Extração de Regras
Fase 1: Baixa TODOS os vídeos do canal SSC (Telegram)
Fase 2: Transcreve via faster-whisper (CPU, modelo tiny)
Fase 3: Extrai conceitos SMC/ICT e regras aplicáveis ao bot

Uso:
  python3 ssc_pipeline.py --all        # Pipeline completo
  python3 ssc_pipeline.py --download   # Só baixar
  python3 ssc_pipeline.py --transcribe # Só transcrever
  python3 ssc_pipeline.py --extract    # Só extrair regras
"""
import subprocess, json, os, sys, asyncio
from pathlib import Path
from datetime import datetime

HOME = Path.home()
VIDEO_DIR = HOME / '.hermes' / 'ssc_videos'
AUDIO_DIR = HOME / '.hermes' / 'ssc_audio'
TRANSCRIPT_DIR = HOME / '.hermes' / 'ssc_transcripts'
RULES_PATH = HOME / '.hermes' / 'forex' / 'ssc_rules.json'

for d in [VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


async def download_all():
    """FASE 1: Baixa todas as mídias do canal SSC."""
    from telethon import TelegramClient
    client = TelegramClient(str(HOME / 'roberto3'), 2040, 'b18441a1ff607e10a989891a5462e627')
    await client.start(phone='+5531982125758')

    messages = await client.get_messages(-1001868821926, limit=200)
    media = [m for m in messages if m.media]

    print(f"FASE 1: Download — {len(media)} mídias")
    count = 0
    for m in media:
        filename = None
        try:
            doc = m.media.document
            for attr in doc.attributes:
                name = getattr(attr, 'file_name', None)
                if name:
                    filename = name
                    break
        except:
            pass

        if not filename:
            ext = '.mp4' if 'video' in str(type(m.media)).lower() else '.jpg'
            filename = f"ssc_{m.id}_{m.date.strftime('%Y%m%d')}{ext}"

        path = VIDEO_DIR / filename
        if path.exists():
            continue

        try:
            result = await client.download_media(m, file=str(VIDEO_DIR))
            if result:
                count += 1
                if count % 5 == 0:
                    print(f"  [{count}/{len(media)}] {Path(result).name[:50]}")
        except Exception as e:
            print(f"  ERRO {filename[:40]}: {e}")

    print(f"FASE 1: {count} baixados (novos)")
    await client.disconnect()


def transcribe_all():
    """FASE 2: Transcreve vídeos com faster-whisper (tiny, CPU)."""
    from faster_whisper import WhisperModel

    videos = sorted([v for v in VIDEO_DIR.glob('*')
                     if v.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov')])

    print(f"\nFASE 2: Transcrição — {len(videos)} vídeos")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")

    results = []
    for i, video in enumerate(videos):
        name = video.stem[:50]
        transcript_json = TRANSCRIPT_DIR / f"{video.stem}.json"

        if transcript_json.exists():
            try:
                data = json.loads(transcript_json.read_text())
                results.append(data)
                print(f"  [{i + 1}/{len(videos)}] {name} — já transcrito ({len(data.get('text', ''))} chars)")
                continue
            except:
                pass

        audio = AUDIO_DIR / f"{video.stem}.wav"
        print(f"  [{i + 1}/{len(videos)}] {name}")

        subprocess.run([
            'ffmpeg', '-y', '-i', str(video),
            '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            str(audio)
        ], capture_output=True, timeout=120)

        if not audio.exists() or audio.stat().st_size < 1000:
            print(f"    ERRO: áudio falhou")
            continue

        try:
            segments, info = model.transcribe(str(audio), language="pt", beam_size=5)
            text = " ".join(seg.text for seg in segments)

            data = {
                "video": video.name,
                "text": text,
                "language": info.language,
                "duration": info.duration,
                "chars": len(text)
            }
            transcript_json.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            results.append(data)
            print(f"    OK: {len(text)} chars, lang={info.language}")
        except Exception as e:
            print(f"    ERRO: {e}")
            continue

    print(f"FASE 2: {len(results)} transcritos")
    return results


def extract_rules(transcripts):
    """FASE 3: Extrai conceitos SMC/ICT e regras numéricas."""
    import re

    print(f"\nFASE 3: Extração de regras")
    full_text = " ".join(t.get("text", "") for t in transcripts)

    rules = {
        "source": "SSC Channel",
        "extracted_at": datetime.now().isoformat(),
        "videos_processed": len(transcripts),
        "total_chars": len(full_text),
        "concepts": {},
        "trading_rules": []
    }

    concept_patterns = {
        "CRT": r'(?i)(CRT|Candle Range Theor\w+|candle range)',
        "FVG": r'(?i)(FVG|Fair Value Gap|gap de valor)',
        "CHoCH": r'(?i)(CHoCH|Change of Character|mudança de caráter|quebra de estrutura)',
        "sweep": r'(?i)(sweep|stop hunt|liquidez|liquidity grab)',
        "estrutura": r'(?i)(estrutura\s+correta|market structure|estrutura de mercado)',
        "temporalidade": r'(?i)(temporalidade|timeframe|time frame|\bM5\b|\bM15\b|\bH1\b)',
        "fluxo": r'(?i)(fluxo|flow|ordem flow|order flow)',
        "range": r'(?i)(range|consolida[çc][ãa]o|acumula[çc][ãa]o|distribui[çc][ãa]o)',
        "rompimento": r'(?i)(rompimento|quebra|break|BOS|break of structure)',
        "entrada": r'(?i)(entrada|entry|setup|gatilho|trigger)',
        "risco": r'(?i)(stop loss|SL|take profit|TP|risco|risk|gest[ãa]o)',
    }

    for concept, pattern in concept_patterns.items():
        matches = re.findall(pattern, full_text)
        if matches:
            snippets = []
            for m in matches[:5]:
                idx = full_text.find(m)
                if idx >= 0:
                    snippet = full_text[max(0, idx - 80):idx + len(m) + 200]
                    snippets.append(snippet.strip()[:300])
            rules["concepts"][concept] = {"count": len(matches), "examples": snippets}

    numbers = re.findall(r'(\d+)[\s]*pip', full_text.lower())
    rr_values = re.findall(r'(\d+)[\s:]*[\/]?\s*(\d+)[\s]*RR', full_text.lower())

    if numbers:
        rules["pip_values"] = [int(n) for n in numbers[:10]]
    if rr_values:
        rules["rr_values"] = [f"{a}:{b}" for a, b in rr_values[:5]]

    RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RULES_PATH.write_text(json.dumps(rules, ensure_ascii=False, indent=2))
    print(f"FASE 3: Regras salvas em {RULES_PATH}")

    for concept, data in sorted(rules["concepts"].items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"  {concept:15s}: {data['count']:4d} menções")

    return rules


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--download', action='store_true')
    p.add_argument('--transcribe', action='store_true')
    p.add_argument('--extract', action='store_true')
    p.add_argument('--all', action='store_true')
    args = p.parse_args()

    if args.all or not any([args.download, args.transcribe, args.extract]):
        args.download = args.transcribe = args.extract = True

    if args.download:
        asyncio.run(download_all())

    transcripts = []
    if args.transcribe:
        transcripts = transcribe_all()

    if args.extract:
        if not transcripts:
            for jf in TRANSCRIPT_DIR.glob('*.json'):
                try:
                    transcripts.append(json.loads(jf.read_text()))
                except:
                    pass
        rules = extract_rules(transcripts)
        print(f"\n{'=' * 60}")
        print(f"PIPELINE COMPLETO — {rules['videos_processed']} vídeos")
        print(f"Conceitos: {len(rules['concepts'])} | Menções: {sum(c['count'] for c in rules['concepts'].values())}")
        print(f"Regras: {RULES_PATH}")
