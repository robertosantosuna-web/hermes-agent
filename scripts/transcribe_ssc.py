#!/usr/bin/python3
"""
Transcreve vídeos do SSC e extrai conceitos SMC/ICT.
Usa faster-whisper (local, GPU ou CPU).
"""
import subprocess, os, sys, json, re
from pathlib import Path
from datetime import datetime

VIDEO_DIR = Path.home() / '.hermes' / 'ssc_videos'
AUDIO_DIR = Path.home() / '.hermes' / 'ssc_audio'
TRANSCRIPT_DIR = Path.home() / '.hermes' / 'ssc_transcripts'

def extract_audio(video_path, audio_path):
    """Extrai áudio do vídeo com ffmpeg."""
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode == 0

def transcribe_audio(audio_path, model_size="medium"):
    """Transcreve áudio com faster-whisper."""
    from faster_whisper import WhisperModel
    
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(audio_path), language="pt", beam_size=5)
    
    text = " ".join(seg.text for seg in segments)
    return {
        "text": text,
        "language": info.language,
        "duration": info.duration
    }

def extract_concepts(text):
    """Extrai conceitos SMC/ICT do texto transcrito."""
    concepts = {
        "CRT": [],
        "FVG": [],
        "CHoCH": [],
        "ICT": [],
        "estrutura": [],
        "liquidez": [],
        "temporalidade": [],
    }
    
    patterns = {
        "CRT": r'(?i)(CRT|Candle Range Theor\w+|candle range)',
        "FVG": r'(?i)(FVG|Fair Value Gap|gap de valor)',
        "CHoCH": r'(?i)(CHoCH|Change of Character|mudança de caráter|quebra de estrutura)',
        "ICT": r'(?i)(ICT|Inner Circle|Smart Money)',
        "estrutura": r'(?i)(estrutura correta|estrutura de mercado|market structure)',
        "liquidez": r'(?i)(liquidez|liquidity|sweep|stop hunt)',
        "temporalidade": r'(?i)(temporalidade|timeframe|time frame|M5|M15|H1)',
    }
    
    for concept, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            # Extrair frases ao redor
            for m in matches:
                idx = text.find(m)
                if idx >= 0:
                    snippet = text[max(0,idx-100):idx+len(m)+200]
                    concepts[concept].append(snippet.strip())
    
    return concepts

def process_all():
    """Processa todos os vídeos baixados."""
    if not VIDEO_DIR.exists():
        print("Nenhum vídeo baixado ainda")
        return
    
    videos = sorted(VIDEO_DIR.glob("*"))
    videos = [v for v in videos if v.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.ogg')]
    
    if not videos:
        print("Nenhum vídeo encontrado em", VIDEO_DIR)
        return
    
    print(f"Processando {len(videos)} vídeos...")
    
    all_concepts = {k: [] for k in ["CRT","FVG","CHoCH","ICT","estrutura","liquidez","temporalidade"]}
    all_texts = []
    
    for i, video in enumerate(videos):
        name = video.stem[:50]
        audio_path = AUDIO_DIR / f"{video.stem}.wav"
        transcript_path = TRANSCRIPT_DIR / f"{video.stem}.json"
        
        print(f"\n[{i+1}/{len(videos)}] {name}")
        
        # Pular se já transcrito
        if transcript_path.exists():
            data = json.loads(transcript_path.read_text())
            text = data.get("text", "")
            print(f"  Já transcrito: {len(text)} chars")
        else:
            # Extrair áudio
            print("  Extraindo áudio...")
            if not extract_audio(video, audio_path):
                print("  ERRO: falha na extração de áudio")
                continue
            
            # Transcrever
            print(f"  Transcrevendo ({audio_path.stat().st_size//1024}KB)...")
            try:
                result = transcribe_audio(audio_path)
                text = result["text"]
                print(f"  OK: {len(text)} chars, lang={result['language']}")
                
                # Salvar transcrição
                TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
                transcript_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"  ERRO transcrição: {e}")
                continue
        
        if text:
            all_texts.append(text)
            concepts = extract_concepts(text)
            for k, v in concepts.items():
                if v:
                    all_concepts[k].extend(v)
                    print(f"  {k}: {len(v)} menções")
    
    # Sumário
    print(f"\n{'='*60}")
    print("SUMÁRIO SSC")
    print(f"Vídeos processados: {len(all_texts)}")
    for concept, mentions in all_concepts.items():
        if mentions:
            print(f"\n--- {concept} ({len(mentions)}) ---")
            for m in mentions[:3]:
                print(f"  • {m[:150]}...")
    
    # Salvar sumário
    summary_path = Path.home() / '.hermes' / 'ssc_summary.json'
    summary = {
        "processed_at": datetime.now().isoformat(),
        "videos_processed": len(all_texts),
        "concepts": {k: len(v) for k, v in all_concepts.items()},
        "total_mentions": sum(len(v) for v in all_concepts.values())
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nSumário salvo: {summary_path}")

if __name__ == '__main__':
    process_all()
