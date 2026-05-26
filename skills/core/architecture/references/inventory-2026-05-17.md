# Tool Inventory — 2026-05-17

Snapshot do arsenal completo após reconstrução do ecossistema.

## System Tools
| Tool | Version | Source |
|------|---------|--------|
| Python | 3.14.4 | apt |
| Node | 22.22.3 | local |
| Brave | 148.1.90 | apt |
| ffmpeg | 8.0.1 | apt |
| tesseract | 5.4.1 | snap |
| redis-server | 8.6.3 | snap |
| WhatsApp Desktop | 1.2.1 | snap |
| Telegram Desktop | latest | snap |
| himalaya | 1.2.0 | cargo |
| agent-browser | 0.27.0 | npm |
| ydotool | 1.0.4 | apt |
| nvcc | CUDA 12.4 | apt |

## Python Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| llama-cpp-python | 0.3.23 | Local LLM (CUDA) |
| torch | 2.12.0 | Deep learning |
| ultralytics | 8.4.51 | YOLO vision |
| transformers | 5.8.1 | HuggingFace models |
| opencv-python-headless | 4.13.0 | Computer vision |
| pillow | 12.1.1 | Image processing |
| pytesseract | 0.3.13 | OCR |
| mss | 10.2.0 | Screenshots |
| pynput | 1.8.2 | Input simulation |
| pyautogui | 0.9.54 | GUI automation |
| playwright | 1.59.0 | Browser CDP |
| telethon | 1.43.2 | Telegram API |
| pyrogram | 2.0.106 | Telegram API alt |
| fastapi | 0.136.1 | API server |
| uvicorn | 0.47.0 | ASGI server |
| redis | 7.4.0 | Cache/Broker |
| chromadb | 1.5.9 | Vector DB |
| lancedb | 0.30.2 | Vector DB |
| rich | latest | Terminal UI |
| loguru | 0.7.3 | Logging |
| numpy | 2.4.5 | Numeric |
| requests | 2.32.5 | HTTP |

## Hardware
- GPU: NVIDIA GTX 1650 Mobile (4GB VRAM)
- CPU: AMD Renoir (integrated) + NVIDIA
- RAM: 6.6 GiB
- Disk: 468G (184G used)
- Display: Wayland, 2 monitors (1920+1920)

## Known Issues
- ydotool daemon needs `input` group + relogin
- WhatsApp Web blocks Brave User-Agent
- Gmail/Outlook need app-specific passwords
- Telegram needs API_ID/API_HASH from my.telegram.org
- /tmp is tmpfs (3.3GB) — use TMPDIR=~/tmp for large pip installs
