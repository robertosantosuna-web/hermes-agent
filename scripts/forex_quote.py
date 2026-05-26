#!/usr/bin/env python3
"""forex_quote.py v3 — Cotação forex via TradingView CDP (reusa mesma aba).
NÃO cria abas novas — brain_browser.py reusa aba existente.

Uso: python3 forex_quote.py EURUSD
"""
import json, sys, subprocess, re
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / ".hermes"
BRAIN_BROWSER = HERMES / "scripts" / "brain_browser.py"

def get_quote(symbol):
    """Get forex quote — reuses existing TradingView tab."""
    chart_url = f'https://www.tradingview.com/chart/?symbol=FX:{symbol}'
    
    try:
        result = subprocess.run(
            [sys.executable, str(BRAIN_BROWSER), "--navigate", chart_url, "--title", "--json"],
            capture_output=True, text=True, timeout=20
        )
        nav_data = json.loads(result.stdout)
        title = nav_data.get('title', '')
        
        match = re.search(r'([\d]+\.\d+)', title)
        if match:
            price = float(match.group(1))
            return {
                "symbol": symbol,
                "bid": price,
                "ask": round(price * 1.00002, 5),
                "source": "tradingview",
                "ts": datetime.now(timezone.utc).isoformat()
            }
    except Exception:
        pass
    
    return {"error": "unavailable", "symbol": symbol}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: forex_quote.py SYMBOL"}))
        sys.exit(1)
    
    print(json.dumps(get_quote(sys.argv[1].upper())))
