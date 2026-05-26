# OCR Setup — Tesseract no Wayland/GNOME

## Problema

Tesseract snap não acessa arquivos fora do sandbox. `TESSDATA_PREFIX` é ignorado.
Solução: baixar traineddata manualmente e usar `tesserocr` (binding Python nativo com libtesseract bundled).

## Instalação

```bash
# 1. Instalar tesserocr (vem com libtesseract bundled, não precisa do snap)
pip install --break-system-packages tesserocr

# 2. Baixar traineddata
mkdir -p ~/.local/share/tessdata
curl -sL "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" -o ~/.local/share/tessdata/eng.traineddata
curl -sL "https://github.com/tesseract-ocr/tessdata/raw/main/por.traineddata" -o ~/.local/share/tessdata/por.traineddata
```

## Uso

```python
import os
from tesserocr import PyTessBaseAPI, PSM
from PIL import Image

os.environ['TESSDATA_PREFIX'] = os.path.expanduser('~/.local/share/tessdata')

with PyTessBaseAPI(path=os.path.expanduser('~/.local/share/tessdata'), lang='eng', psm=PSM.AUTO) as api:
    api.SetImageFile('/tmp/screenshot.png')
    text = api.GetUTF8Text()
```

## Verificação

```python
from tesserocr import get_languages
print(get_languages())  # Deve listar ['eng', 'por']
```

## Pitfalls

- `tesserocr` vs `pytesseract`: tesserocr é binding nativo (mais rápido, lib bundled). pytesseract é wrapper CLI (precisa do binário tesseract no PATH)
- Snap tesseract NÃO funciona para OCR programático porque não acessa tessdata externo
- Traineddata do GitHub são binários válidos (~15MB cada), formato `.traineddata`
