# Full Tool Inventory — ENTIDADE Arsenal

Status 2026-05-17. Ambiente: Linux 7.0.0-15, Wayland, NVIDIA GTX 1650 4GB.

## Python Libraries (27)

| Library | Version | Category |
|---------|---------|----------|
| pillow | 12.1.1 | Image processing |
| opencv-python-headless | 4.13.0 | Computer vision |
| numpy | 2.4.5 | Numeric computing |
| pytesseract | 0.3.13 | OCR wrapper |
| tesserocr | 2.10.0 | OCR native bindings |
| mss | 10.2.0 | Screenshots (X11, broken on Wayland) |
| pyautogui | 0.9.54 | GUI automation |
| pynput | 1.8.2 | Keyboard/mouse input |
| playwright | 1.59.0 | Browser CDP automation |
| requests | 2.32.5 | HTTP |
| fastapi | 0.136.1 | API framework |
| uvicorn | 0.47.0 | ASGI server |
| redis | 7.4.0 | Redis client |
| telethon | 1.43.2 | Telegram API |
| pyrogram | 2.0.106 | Telegram API alt |
| transformers | 5.8.1 | HuggingFace models |
| torch | 2.12.0 | Deep learning (CUDA) |
| ultralytics | 8.4.51 | YOLO vision models |
| chromadb | 1.5.9 | Vector database |
| lancedb | 0.30.2 | Vector database |
| llama-cpp-python | 0.3.23 | Local LLM (CUDA) |
| rich | OK | Terminal UI |
| loguru | 0.7.3 | Logging |
| pygetwindow | 0.0.9 | Window info |
| img2pdf | 0.6.3 | Image to PDF |
| wand | 0.7.0 | ImageMagick bindings |

## System Tools (12)

| Tool | Version | Source |
|------|---------|--------|
| ffmpeg | 8.0.1 | apt |
| tesseract | 5.4.1 | snap |
| brave-browser | 148.1 | apt |
| microsoft-edge | 148.0 | apt |
| telegram-desktop | snap | snap |
| whatsapp-desktop-linux | 1.2.1 | snap |
| himalaya | 1.2.0 | installed |
| agent-browser | 0.27.0 | npm |
| redis-server | 8.6.3 | snap |
| ydotool | 1.0.4 | apt |
| nvcc | 12.4 | nvidia-cuda-toolkit |
| node | 22.22.3 | nvm |

## Gmail Account

- Email: robertosantos.una@gmail.com
- IMAP: imap.gmail.com:993 (SSL)
- SMTP: smtp.gmail.com:587 (STARTTLS)
- Auth: App Password (16 chars)
- 11,584 emails in INBOX

## Telegram

- API_ID: precisa regenerar (atual inválido)
- Número: +55 31 982125758
- telethon instalado, aguardando credenciais válidas

## WhatsApp

- Desktop: instalado e rodando (11 processos)
- Web: bloqueado (Brave User-Agent rejeitado)
- Controle visual: pendente (Wayland screenshots quebrados)

## Local LLM (GPU)

- Modelo: Phi-3.1-mini-4k-instruct (Q4_K_M, 2.4GB)
- Engine: llama-cpp-python 0.3.23 com CUDA
- GPU: GTX 1650, 24/33 layers offloaded, ~2.4GB/4GB VRAM
- Speed: ~7-10 tok/s
- Uso: task-router classification

## Known Issues

1. **mss + Wayland**: todos monitores capturam tela preta (0% pixels não-pretos)
   → Usar grim (precisa instalar) ou portal D-Bus Screenshot
2. **WhatsApp Web + Brave**: User-Agent bloqueado
   → Usar WhatsApp Desktop app
3. **himalaya**: formato TOML quebrado entre versões
   → Substituído por imaplib Python direto
4. **/tmp tmpfs quota**: 3.3GB limit com usrquota
   → Usar TMPDIR=~/tmp para instalações grandes
