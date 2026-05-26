---
name: voice-cloning
description: Clonagem de voz com Coqui TTS XTTS v2. Clone fiel com apenas 6s de áudio, +17 línguas. Motor instalado em ~/rvc/venv, scripts em ~/voice_dataset/. Suporte a GPU (GTX 1650 4GB) e CPU.
category: creative
---

# Voice Cloning — XTTS v2

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│                 Coqui TTS XTTS v2                │
│            (tts_models/multilingual/             │
│             multi-dataset/xtts_v2)               │
│                                                  │
│  Input: áudio referência 6s+ + texto             │
│  Output: WAV com voz clonada                     │
│  VRAM: ~1.9GB (GPU) / CPU mode                   │
│  Línguas: pt, en, es, fr, de, it + 11 mais      │
└──────────────────────────────────────────────────┘
```

## Instalação

Local: `/home/roberto/rvc/venv`
Python: 3.11.15
PyTorch: 2.6.0+cu124 (CUDA)

Pacotes críticos:
- `TTS==0.22.0` (Coqui TTS)
- `transformers==4.36.2`
- `torch==2.6.0+cu124`
- `torchaudio==2.6.0+cu124`

## Scripts

### `voice_cloner.py` — Clone de voz interativo

```bash
# Ativar venv
source /home/roberto/rvc/venv/bin/activate

# Modo interativo (recomendado)
python3 /home/roberto/voice_dataset/voice_cloner.py -i

# Linha de comando
python3 /home/roberto/voice_dataset/voice_cloner.py \
  "Olá, esta é minha voz clonada!" \
  --ref /home/roberto/voice_dataset/raw/roberto_ref.wav \
  --out /tmp/minha_voz.wav \
  --lang pt
```

### `record_voice_dataset.py` — Gravação de dataset

```bash
python3 /home/roberto/voice_dataset/record_voice_dataset.py          # Guiada (frases)
python3 /home/roberto/voice_dataset/record_voice_dataset.py --check  # Verificar qualidade
python3 /home/roberto/voice_dataset/record_voice_dataset.py --split  # Segmentar dataset
python3 /home/roberto/voice_dataset/record_voice_dataset.py --free 5 # Gravação livre 5min
```

## Dependências

Modelo baixado: `~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/`

## Monkey-patches aplicados

1. `TTS/utils/io.py`: `torch.load(..., weights_only=False)` + `add_safe_globals([XttsConfig])`
2. `TTS/utils/manage.py`: `ModelManager.ask_tos` bypassed

## Pitfalls

1. XTTS v2 em GPU usa ~1.9GB VRAM. Com 4GB total, evite rodar outros modelos simultaneamente.
2. Áudio de referência ideal: 6-30 segundos, sem ruído, voz clara, WAV mono.
3. Primeira carga do modelo é lenta (~30s), depois fica em memória.
4. **transformers**: versões >4.36.2 quebram `BeamSearchScorer`. Pin exato: `transformers==4.36.2`.
5. **torchaudio**: deve bater com a versão CUDA do PyTorch. Se `libcudart.so` der erro, reinstalar: `pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu124 torchaudio`.
6. **torch.load**: PyTorch 2.6+ usa `weights_only=True` como padrão. Modelos antigos precisam de patch: adicionar `add_safe_globals([XttsConfig])` + `weights_only=False` em `TTS/utils/io.py`.
7. **Licença Coqui**: bypass com monkey-patch em `TTS.utils.manage.ModelManager.ask_tos` antes de importar TTS.
8. **ANTI-WASTE**: Verificar compatibilidade Python + VRAM + deps ANTES de instalar. RVC falhou 10+ tentativas (requer Python 3.10, não 3.11). Sempre prefira ferramenta compatível com o ambiente atual.
9. Se VRAM estourar (OOM), usar `gpu=False` para CPU mode (muito mais lento).
