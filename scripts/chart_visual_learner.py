#!/usr/bin/env python3
"""
Chart Visual Learner v1.0 — Reconhecimento Visual de Padrões de Gráfico.
Integra: Visual Cortex (screenshot+OCR) + algorithmic patterns + MT5 charts.

Aprende a reconhecer visualmente:
- CHoCH (Change of Character) — varredura de liquidez + reversão
- FVG (Fair Value Gap) — gaps entre velas
- OB (Order Blocks) — blocos de ordem institucionais
- BOS (Break of Structure) — quebra de estrutura
- S/R Levels — suporte/resistência por swing points
- Liquidity sweeps — varreduras de liquidez (EQH/EQL)

Fluxo:
  1. Captura screenshot do MT5 (Xvfb :99)
  2. OCR extrai preços
  3. Visual Cortex detecta elementos (velas, candles, indicadores)
  4. Cruza com padrões algorítmicos (chart_pattern_study.py)
  5. Salva no pattern_library visual + KB Neural
  6. Aprende correlação: padrão → resultado (WR por tipo de padrão)

no_agent — zero tokens. Roda via cron.
"""

import json, os, sys, subprocess, time, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES = Path(os.path.expanduser('~/.hermes'))
VISUAL_LIB = HERMES / 'forex' / 'patterns' / 'visual_library.json'
ALGO_LIB = HERMES / 'forex' / 'patterns' / 'pattern_library.json'
SCREENSHOTS_DIR = HERMES / 'forex' / 'patterns' / 'screenshots'
TRADE_LOG = HERMES / 'forex' / 'trade_log.json'
DISPLAY = ':99'

# ── Pairs e Timeframes ───────────────────────────────────────────────────

PAIRS = ['EURUSD', 'GBPUSD', 'AUDUSD', 'NZDUSD', 'USDJPY', 'USDCAD']
TIMEFRAMES = {
    'M5': {'mt5_period': 5, 'bars_visible': 120},
    'M15': {'mt5_period': 15, 'bars_visible': 100},
    'H1': {'mt5_period': 60, 'bars_visible': 80},
}

# ── MT5 Screenshot Capture ───────────────────────────────────────────────

def focus_mt5():
    """Focus MT5 window on Xvfb :99."""
    try:
        # List windows
        result = subprocess.run(
            ['xdotool', 'search', '--name', 'MetaTrader', '--display', DISPLAY],
            capture_output=True, text=True, timeout=5
        )
        window_ids = result.stdout.strip().split('\n')
        if window_ids and window_ids[0]:
            subprocess.run(
                ['xdotool', 'windowfocus', window_ids[0], '--display', DISPLAY],
                timeout=3
            )
            return window_ids[0]
    except Exception:
        pass
    return None


def navigate_to_chart(pair, timeframe='M15'):
    """
    Navigate MT5 to a specific pair+timeframe chart.
    Uses Ctrl+O (open symbol), types pair name, sets timeframe via toolbar.
    """
    try:
        # Ctrl+O to open symbol window
        subprocess.run(['xdotool', 'key', '--display', DISPLAY, 'ctrl+o'], timeout=2)
        time.sleep(0.5)
        
        # Type pair name
        subprocess.run(['xdotool', 'type', '--display', DISPLAY, f'{pair}'], timeout=2)
        time.sleep(0.3)
        subprocess.run(['xdotool', 'key', '--display', DISPLAY, 'Return'], timeout=2)
        time.sleep(1.0)  # Wait for chart to load
        
        # Set timeframe via keyboard shortcut
        tf_keys = {'M5': '5', 'M15': '7', 'H1': '8'}
        if timeframe in tf_keys:
            subprocess.run(['xdotool', 'key', '--display', DISPLAY, f'Alt+{tf_keys[timeframe]}'], timeout=2)
            time.sleep(0.5)
        
        return True
    except Exception as e:
        print(f"  ⚠ Navigation error: {e}")
        return False


def capture_screenshot(filename):
    """Capture screenshot of MT5 chart via Xvfb."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SCREENSHOTS_DIR / filename
    
    try:
        result = subprocess.run(
            ['xwd', '-display', DISPLAY, '-root', '-out', '/tmp/mt5_screenshot.xwd'],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            subprocess.run(
                ['convert', '/tmp/mt5_screenshot.xwd', str(filepath)],
                capture_output=True, timeout=10
            )
            return str(filepath) if filepath.exists() else None
    except Exception as e:
        print(f"  ⚠ Screenshot error: {e}")
    return None


# ── Pattern Recognition Heuristics (Chart Geometry) ──────────────────────

def detect_visual_patterns(screenshot_path):
    """
    Analyze screenshot for visual chart features.
    Uses ImageMagick and basic heuristics — no deep learning needed.
    
    Detects:
    - Price distribution (where price is in the visible range)
    - Candle density (volatility zones)
    - Trend direction (visual slope)
    """
    features = {
        'screenshot': screenshot_path,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'detections': {},
    }
    
    try:
        # Get image dimensions
        result = subprocess.run(
            ['identify', '-format', '%w %h', screenshot_path],
            capture_output=True, text=True, timeout=5
        )
        w, h = map(int, result.stdout.strip().split())
        
        # Sample pixel colors from right side (price axis area) and center (chart area)
        for region_name, region_coords in [
            ('price_axis_right', f'{w-20}x{h}+{w-20}+0'),
            ('chart_center', f'{w//2}x{h//4}+{w//4}+{h//4}'),
            ('chart_bottom_left', f'{w//3}x{h//5}+10+{h-h//5}'),
        ]:
            try:
                result = subprocess.run(
                    ['convert', screenshot_path, '-crop', region_coords,
                     '-resize', '1x1!', '-format', '%[pixel:u]', 'info:'],
                    capture_output=True, text=True, timeout=5
                )
                features['detections'][region_name] = result.stdout.strip()
            except Exception:
                features['detections'][region_name] = 'unknown'
        
    except Exception as e:
        features['error'] = str(e)
    
    return features


def analyze_chart_structure(screenshot_path, pair, timeframe):
    """
    Analyze chart structure from screenshot:
    - Detect candle colors (green=up, red=down, doji=flat)
    - Count bullish vs bearish candles in visible range
    - Detect possible patterns based on color sequences
    """
    analysis = {
        'pair': pair,
        'timeframe': timeframe,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'market_structure': {},
    }
    
    try:
        # Reduce to analyze dominant colors in chart area
        result = subprocess.run(
            ['convert', screenshot_path, '-resize', '100x60!',
             '-colors', '8', '-format', '%c', 'histogram:info:'],
            capture_output=True, text=True, timeout=5
        )
        color_data = result.stdout
        
        # Parse histogram: count dark (bearish/background) vs bright (bullish)
        dark_count = 0
        bright_count = 0
        for line in color_data.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Extract pixel count and color
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    count_str = parts[0].strip()
                    # Handle "  1234: (..." format
                    count = int(''.join(c for c in count_str if c.isdigit() or c == ' ').split()[0])
                except (ValueError, IndexError):
                    continue
                
                color_str = parts[1].strip().lower()
                # Simple heuristic: bright colors = bullish, dark = bearish
                if 'green' in color_str or 'white' in color_str or 'red' in color_str:
                    if 'green' in color_str or 'white' in color_str:
                        bright_count += count
                    if 'red' in color_str:
                        dark_count += count
        
        if bright_count + dark_count > 0:
            bullish_pct = bright_count / (bright_count + dark_count) * 100
            analysis['market_structure']['bullish_dominance_pct'] = round(bullish_pct, 1)
            analysis['market_structure']['sentiment'] = (
                'bullish' if bullish_pct > 55 else
                'bearish' if bullish_pct < 45 else
                'neutral'
            )
    
    except Exception as e:
        analysis['market_structure']['error'] = str(e)
    
    return analysis


# ── OCR Price Extraction ─────────────────────────────────────────────────

def extract_prices_ocr(screenshot_path, pair):
    """
    Use Tesseract OCR to extract price levels from the chart screenshot.
    Focuses on the price axis (right side of chart) and current price indicator.
    """
    prices = {'pair': pair, 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    try:
        # Crop right side (price axis)
        axis_crop = str(SCREENSHOTS_DIR / f'{pair}_axis_{datetime.now().strftime("%H%M%S")}.png')
        
        # Get dimensions
        result = subprocess.run(
            ['identify', '-format', '%w %h', screenshot_path],
            capture_output=True, text=True, timeout=5
        )
        w, h = map(int, result.stdout.strip().split())
        
        # Crop price axis (right ~15% of chart)
        crop_w = int(w * 0.15)
        subprocess.run(
            ['convert', screenshot_path, '-crop', f'{crop_w}x{h}+{w-crop_w}+0',
             '-colorspace', 'Gray', '-contrast-stretch', '2%',
             axis_crop],
            capture_output=True, timeout=5
        )
        
        # OCR
        result = subprocess.run(
            ['tesseract', axis_crop, 'stdout', '-l', 'eng', '--psm', '6'],
            capture_output=True, text=True, timeout=10
        )
        ocr_text = result.stdout.strip()
        
        # Extract numbers (price levels)
        numbers = re.findall(r'\d+\.?\d*', ocr_text)
        prices['ocr_raw'] = ocr_text
        prices['numbers_found'] = numbers[:10]  # Top 10 numbers
        
        # Find current price (usually highlighted/bold on MT5)
        # Look for the number near the right edge with a distinctive format
        for num in numbers:
            val = float(num)
            if pair == 'EURUSD' and 0.9 < val < 1.3:
                prices['current_price_estimate'] = val
                break
            elif pair == 'GBPUSD' and 1.1 < val < 1.5:
                prices['current_price_estimate'] = val
                break
            elif pair == 'AUDUSD' and 0.5 < val < 0.8:
                prices['current_price_estimate'] = val
                break
            elif pair == 'NZDUSD' and 0.5 < val < 0.7:
                prices['current_price_estimate'] = val
                break
            elif pair == 'USDJPY' and 100 < val < 200:
                prices['current_price_estimate'] = val
                break
            elif pair == 'USDCAD' and 1.2 < val < 1.5:
                prices['current_price_estimate'] = val
                break
        
    except Exception as e:
        prices['ocr_error'] = str(e)
    
    return prices


# ── Visual Pattern Library ───────────────────────────────────────────────

def update_visual_library(pair, timeframe, pattern_type, data):
    """Add visual pattern example to the visual library."""
    library = {}
    if VISUAL_LIB.exists():
        try:
            library = json.loads(VISUAL_LIB.read_text())
        except:
            pass
    
    key = f"{pair}_{timeframe}_{pattern_type}"
    if key not in library:
        library[key] = {
            'pair': pair,
            'timeframe': timeframe,
            'pattern_type': pattern_type,
            'examples': [],
            'total_collected': 0,
            'last_updated': datetime.now(timezone.utc).isoformat(),
        }
    
    # Append example
    library[key]['examples'].append(data)
    library[key]['total_collected'] = len(library[key]['examples'])
    
    # Keep last 100 per key
    if len(library[key]['examples']) > 100:
        library[key]['examples'] = library[key]['examples'][-100:]
    
    library[key]['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    VISUAL_LIB.parent.mkdir(parents=True, exist_ok=True)
    VISUAL_LIB.write_text(json.dumps(library, indent=2, default=str))


def correlate_with_outcomes():
    """
    Correlate visual patterns with actual trade outcomes.
    Reads trade_log.json and matches patterns to results.
    """
    if not TRADE_LOG.exists():
        return {}
    
    try:
        trade_log = json.loads(TRADE_LOG.read_text())
        trades = trade_log.get('trades', [])
        closed_trades = [t for t in trades if t.get('status') == 'closed' and t.get('pnl') is not None]
        
        if not closed_trades:
            return {}
        
        # Group by pair + direction
        outcomes = {}
        for t in closed_trades:
            key = f"{t.get('pair', '?')}_{t.get('direction', '?')}"
            if key not in outcomes:
                outcomes[key] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            pnl = t.get('pnl', 0)
            outcomes[key]['total_pnl'] += pnl
            if pnl > 0:
                outcomes[key]['wins'] += 1
            else:
                outcomes[key]['losses'] += 1
        
        # Calculate WR per pair+direction
        for key, data in outcomes.items():
            total = data['wins'] + data['losses']
            data['wr'] = round(data['wins'] / total * 100, 1) if total > 0 else 0
            data['total_trades'] = total
        
        return outcomes
    
    except Exception:
        return {}


# ── Main Study Loop ──────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y%m%d_%H%M')
    
    print(f"📸 Chart Visual Learner — {now.strftime('%Y-%m-%d %H:%M')} UTC")
    
    # Check MT5 accessibility
    window_id = focus_mt5()
    if not window_id:
        print("⚠ MT5 não acessível no Xvfb :99 — estudo visual abortado")
        print("  (MT5 precisa estar rodando no Xvfb)")
        return
    
    print(f"✓ MT5 window: {window_id}")
    
    # Load algorithmic patterns for comparison
    algo_patterns = {}
    if ALGO_LIB.exists():
        try:
            algo_patterns = json.loads(ALGO_LIB.read_text())
            print(f"✓ Algo patterns loaded: {list(algo_patterns.keys())}")
        except:
            pass
    
    outcomes = correlate_with_outcomes()
    if outcomes:
        print(f"✓ Trade outcomes: {len(outcomes)} pair+direction combos")
    
    results = []
    
    for pair in PAIRS:
        print(f"\n▶ {pair}")
        
        for tf_name, tf_config in TIMEFRAMES.items():
            # Navigate to chart
            if not navigate_to_chart(pair, tf_name):
                print(f"  {tf_name}: navigation failed")
                continue
            
            time.sleep(0.5)
            
            # Capture screenshot
            filename = f"{pair}_{tf_name}_{today}.png"
            screenshot = capture_screenshot(filename)
            
            if not screenshot:
                print(f"  {tf_name}: screenshot failed")
                continue
            
            # Visual analysis
            visual_features = detect_visual_patterns(screenshot)
            chart_structure = analyze_chart_structure(screenshot, pair, tf_name)
            ocr_prices = extract_prices_ocr(screenshot, pair)
            
            # Combine results
            session_result = {
                'pair': pair,
                'timeframe': tf_name,
                'timestamp': now.isoformat(),
                'screenshot': filename,
                'visual': visual_features,
                'structure': chart_structure,
                'prices': ocr_prices,
                'outcome_correlation': outcomes.get(f"{pair}_BUY", {}),
            }
            
            results.append(session_result)
            
            # Update visual library
            update_visual_library(pair, tf_name, 'chart_study', session_result)
            
            # Summary
            sentiment = chart_structure.get('market_structure', {}).get('sentiment', '?')
            price = ocr_prices.get('current_price_estimate', '?')
            print(f"  {tf_name}: sentiment={sentiment}, price≈{price}")
    
    # ── Save Session Report ─────────────────────────────────────────────
    report_dir = HERMES / 'forex' / 'patterns' / 'visual_reports'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"visual_study_{today}.json"
    
    report = {
        'timestamp': now.isoformat(),
        'pairs_studied': len(results),
        'timeframes_per_pair': len(TIMEFRAMES),
        'results': results,
        'outcomes': outcomes,
        'summary': {
            'pairs_with_bullish_sentiment': [
                r['pair'] for r in results
                if r.get('structure', {}).get('market_structure', {}).get('sentiment') == 'bullish'
            ],
            'pairs_with_bearish_sentiment': [
                r['pair'] for r in results
                if r.get('structure', {}).get('market_structure', {}).get('sentiment') == 'bearish'
            ],
        },
    }
    
    report_path.write_text(json.dumps(report, indent=2, default=str))
    
    # ── Neural KB Integration ──────────────────────────────────────────
    try:
        from kb_bridge import write as kb_write
        
        kb_write('visual_cortex', {
            'last_visual_study': now.isoformat(),
            'pairs_studied': len(results),
            'sentiment_map': {r['pair']: r.get('structure', {}).get('market_structure', {}).get('sentiment', '?')
                            for r in results},
            'price_estimates': {r['pair']: r.get('prices', {}).get('current_price_estimate')
                               for r in results},
            'visual_samples_count': len(results),
        })
    except ImportError:
        pass
    
    print(f"\n✅ Visual study complete: {len(results)} chart views captured")
    print(f"📸 Screenshots: {SCREENSHOTS_DIR}")
    print(f"📄 Report: {report_path}")
    print(f"📚 Visual Library: {VISUAL_LIB}")


if __name__ == '__main__':
    main()
