#!/usr/bin/python3
"""
Motor Local de Processamento de Imagens - Multi-backend
Backends: xvfb (MT5/Wine), browser (CDP), wayland (grim se disponível)
Uso: python3 vision_engine.py [modo] [opções]
"""

import subprocess
import sys
import json
import os
import shutil
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path.home() / ".hermes" / "cache" / "vision"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════
# BACKEND 1: Xvfb (para MT5, Wine, apps X11)
# ═══════════════════════════════════════════
def xvfb_screenshot(display=":99", window="root", output_path=None):
    """Captura tela do Xvfb via ImageMagick import."""
    if not shutil.which("import"):
        return {"error": "ImageMagick 'import' não instalado"}
    
    if output_path is None:
        output_path = CACHE_DIR / f"xvfb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    cmd = ["import", "-display", display, "-window", window, str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                           env={**os.environ, "DISPLAY": display})
    
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "path": None}
    
    return {
        "path": str(output_path),
        "size": os.path.getsize(output_path),
        "display": display,
        "window": window
    }


def xvfb_screenshot_region(display=":99", x=0, y=0, w=1920, h=1080, output_path=None):
    """Captura região específica do Xvfb."""
    if output_path is None:
        output_path = CACHE_DIR / f"xvfb_region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    cmd = [
        "import", "-display", display, "-window", "root",
        "-crop", f"{w}x{h}+{x}+{y}", str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10,
                           env={**os.environ, "DISPLAY": display})
    
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "path": None}
    
    return {
        "path": str(output_path),
        "size": os.path.getsize(output_path),
        "display": display,
        "region": [x, y, w, h]
    }


# ═══════════════════════════════════════════
# BACKEND 2: Wayland (grim, se suportado)
# ═══════════════════════════════════════════
def wayland_screenshot(output_path=None):
    """Tenta capturar via grim (Wayland wlr). GNOME não suporta."""
    if not shutil.which("grim"):
        return {"error": "grim não instalado"}
    
    if output_path is None:
        output_path = CACHE_DIR / f"wayland_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    
    result = subprocess.run(["grim", str(output_path)], capture_output=True, text=True, timeout=10)
    
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "path": None}
    
    return {"path": str(output_path), "size": os.path.getsize(output_path)}


# ═══════════════════════════════════════════
# OCR Engine (Tesseract)
# ═══════════════════════════════════════════
try:
    from PIL import Image, ImageEnhance
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def preprocess_image(image_path):
    """Otimiza imagem para OCR."""
    img = Image.open(image_path)
    img = img.convert("L")  # grayscale
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = img.point(lambda x: 0 if x < 140 else 255)  # threshold adaptativo
    processed = str(Path(image_path).with_suffix(".ocr.png"))
    img.save(processed)
    return processed


def ocr_image(image_path, lang="por+eng", preprocess=True):
    """OCR via Tesseract com métricas."""
    if not HAS_OCR:
        return {"error": "PIL/pytesseract não disponíveis"}
    if not os.path.exists(image_path):
        return {"error": f"Imagem não encontrada: {image_path}"}
    
    proc_path = preprocess_image(image_path) if preprocess else image_path
    
    try:
        text = pytesseract.image_to_string(
            Image.open(proc_path), lang=lang, config="--psm 6"
        )
        data = pytesseract.image_to_data(
            Image.open(proc_path), lang=lang, output_type=pytesseract.Output.DICT
        )
        confidences = [c for c in data["conf"] if c > 0]
        
        return {
            "text": text.strip(),
            "confidence": round(sum(confidences) / len(confidences), 1) if confidences else 0,
            "word_count": len(text.split()),
            "source": image_path
        }
    except Exception as e:
        return {"error": str(e)}


def ocr_numbers_only(image_path, lang="por+eng"):
    """OCR otimizado para extrair apenas números (valores, preços, %)."""
    if not HAS_OCR:
        return {"error": "PIL/pytesseract não disponíveis"}
    
    proc_path = preprocess_image(image_path)
    text = pytesseract.image_to_string(
        Image.open(proc_path), lang=lang,
        config="--psm 6 -c tessedit_char_whitelist=0123456789.,%-+ "
    )
    return {"text": text.strip(), "source": image_path}


# ═══════════════════════════════════════════
# Pipeline unificado
# ═══════════════════════════════════════════
def full_pipeline(mode="xvfb", **kwargs):
    """Pipeline completo: captura + OCR."""
    display = kwargs.get("display", ":99")
    lang = kwargs.get("lang", "por+eng")
    no_ocr = kwargs.get("no_ocr", False)
    
    # Captura
    if mode == "xvfb":
        result = xvfb_screenshot(display=display)
    elif mode == "xvfb_region":
        region = kwargs.get("region", [0, 0, 1920, 1080])
        result = xvfb_screenshot_region(display=display, x=region[0], y=region[1],
                                        w=region[2], h=region[3])
    elif mode == "wayland":
        result = wayland_screenshot()
    elif mode == "ocr_only":
        if not kwargs.get("image"):
            return {"error": "Modo ocr_only requer --image"}
        result = {"path": kwargs["image"]}
        no_ocr = False  # force OCR
    else:
        return {"error": f"Modo desconhecido: {mode}"}
    
    if result.get("error"):
        return result
    
    # OCR
    if not no_ocr and result.get("path"):
        if kwargs.get("numbers_only"):
            ocr_result = ocr_numbers_only(result["path"], lang)
        else:
            ocr_result = ocr_image(result["path"], lang)
        result["ocr"] = ocr_result
        
    # Metadados
    result["timestamp"] = datetime.now().isoformat()
    result["mode"] = mode
    return result


# ═══════════════════════════════════════════
# Funções especializadas
# ═══════════════════════════════════════════
def capture_mt5():
    """Captura MT5 no Xvfb com regiões de interesse (preços, P&L)."""
    result = full_pipeline("xvfb", numbers_only=True)
    result["mt5_status"] = "captured"
    return result


def capture_mt5_account_info():
    """Captura info da conta MT5 (saldo, equity, margem) - região específica."""
    # Região típica do terminal MT5: canto inferior
    result = full_pipeline("xvfb_region", region=[0, 880, 1920, 200], numbers_only=True)
    result["mt5_section"] = "account_info"
    return result


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Motor de Processamento de Imagens")
    parser.add_argument("mode", nargs="?", default="xvfb",
                       choices=["xvfb", "xvfb_region", "wayland", "ocr_only", "mt5", "mt5_account"])
    parser.add_argument("--display", default=":99")
    parser.add_argument("--image", help="Caminho da imagem para OCR")
    parser.add_argument("--region", help="Região x,y,w,h (modo xvfb_region)")
    parser.add_argument("--lang", default="por+eng")
    parser.add_argument("--no-ocr", action="store_true")
    parser.add_argument("--numbers-only", action="store_true")
    
    args = parser.parse_args()
    
    if args.mode == "mt5":
        result = capture_mt5()
    elif args.mode == "mt5_account":
        result = capture_mt5_account_info()
    elif args.mode == "ocr_only":
        if not args.image:
            print(json.dumps({"error": "--image obrigatório para ocr_only"}, ensure_ascii=False))
            sys.exit(1)
        lang = args.lang
        if args.numbers_only:
            result = ocr_numbers_only(args.image, lang)
        else:
            result = ocr_image(args.image, lang)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    else:
        kwargs = {"display": args.display, "lang": args.lang,
                  "no_ocr": args.no_ocr, "numbers_only": args.numbers_only}
        if args.mode == "xvfb_region" and args.region:
            kwargs["region"] = [int(x) for x in args.region.split(",")]
        result = full_pipeline(args.mode, **kwargs)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
