#!/usr/bin/env python3
"""Generate profile avatars for Telegram: Hermes Agent + Brain."""
from PIL import Image, ImageDraw
import math, os, random

output_dir = os.path.expanduser("~/.hermes/telegram_avatars/")
os.makedirs(output_dir, exist_ok=True)
random.seed(42)

def create_agent_avatar(size=512):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size//2, size//2
    r = size//2 - 10
    
    # Background circle
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(15, 15, 45, 255))
    # Outer ring
    draw.ellipse([cx-r+5, cy-r+5, cx+r-5, cy+r-5], outline=(0, 200, 255, 200), width=4)
    # Inner circle
    r2 = r - 25
    draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], fill=(8, 8, 28, 255), outline=(0, 160, 230, 150), width=2)
    
    # Central diamond (eye)
    eye_r = r2 - 30
    points = [
        (cx, cy - eye_r),
        (cx + eye_r, cy),
        (cx, cy + eye_r),
        (cx - eye_r, cy),
    ]
    draw.polygon(points, fill=(0, 190, 255, 230))
    pupil_r = eye_r // 3
    draw.ellipse([cx-pupil_r, cy-pupil_r, cx+pupil_r, cy+pupil_r], fill=(10, 10, 30, 255))
    
    # Corner nodes + connections
    for angle in [30, 150, 210, 330]:
        rad = math.radians(angle)
        nx = cx + int((r-15) * math.cos(rad))
        ny = cy + int((r-15) * math.sin(rad))
        draw.ellipse([nx-6, ny-6, nx+6, ny+6], fill=(0, 220, 255, 210))
        ex = cx + int(eye_r * 0.7 * math.cos(rad))
        ey = cy + int(eye_r * 0.7 * math.sin(rad))
        draw.line([nx, ny, ex, ey], fill=(0, 150, 220, 120), width=2)
    
    path = os.path.join(output_dir, "hermes_agent.png")
    img.save(path)
    return path

def create_brain_avatar(size=512):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size//2, size//2
    r = size//2 - 10
    
    # Background
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(25, 4, 45, 255))
    draw.ellipse([cx-r+5, cy-r+5, cx+r-5, cy+r-5], outline=(180, 40, 220, 180), width=3)
    
    r2 = r - 20
    # Left hemisphere
    draw.ellipse([cx-r2, cy-r2, cx, cy+r2], fill=(55, 15, 85, 200), outline=(150, 35, 200, 150), width=2)
    # Right hemisphere
    draw.ellipse([cx, cy-r2, cx+r2, cy+r2], fill=(55, 15, 85, 200), outline=(150, 35, 200, 150), width=2)
    # Center line
    draw.line([cx, cy-r2, cx, cy+r2], fill=(150, 35, 200, 180), width=2)
    
    # Neural nodes
    synapses = []
    for _ in range(14):
        sx = random.randint(cx-r2+20, cx+r2-20)
        sy = random.randint(cy-r2+20, cy+r2-20)
        draw.ellipse([sx-5, sy-5, sx+5, sy+5], fill=(255, 90, 255, 210))
        synapses.append((sx, sy))
    
    # Connect nearby nodes
    for i, (sx1, sy1) in enumerate(synapses):
        for sx2, sy2 in synapses[i+1:]:
            dist = math.sqrt((sx2-sx1)**2 + (sy2-sy1)**2)
            if dist < r2 * 0.8:
                alpha = max(30, int(140 - dist * 1.4))
                draw.line([sx1, sy1, sx2, sy2], fill=(200, 70, 255, alpha), width=1)
    
    path = os.path.join(output_dir, "hermes_brain.png")
    img.save(path)
    return path

if __name__ == '__main__':
    a = create_agent_avatar()
    b = create_brain_avatar()
    print(f"Agente: {a}")
    print(f"Cerebro: {b}")
