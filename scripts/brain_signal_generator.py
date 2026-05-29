#!/usr/bin/env python3
"""
Brain Signal Generator — Analisa charts do TradingView via CDP e gera sinais CHoCH+FVG.
Executado pelo cérebro (cron no_agent). Sinais salvos para validação do agente.

Uso:
  python3 brain_signal_generator.py          # Analisa todos os pares abertos
  python3 brain_signal_generator.py --pair EURUSD  # Um par específico
  python3 brain_signal_generator.py --cron   # Modo silencioso para cron
"""

import json, sys, os, time, argparse
from datetime import datetime, timezone
from pathlib import Path

HERMES = Path.home() / ".hermes"
SIGNALS_FILE = HERMES / "forex" / "signals_pending.json"
STATE_FILE = HERMES / "forex" / "brain_signal_state.json"
BRAIN_CONTEXT = HERMES / "brain_context.json"
WEEKLY_BIAS_FILE = HERMES / "forex" / "weekly_bias.json"

# Pares para analisar (símbolos do TradingView)
PAIRS = {
    "GBPJPY": {"symbol": "FX:GBPJPY", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AGBPJPY&interval=15"},
    "USDJPY": {"symbol": "FX:USDJPY", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AUSDJPY&interval=15"},
    "EURUSD": {"symbol": "FX:EURUSD", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AEURUSD&interval=15"},
    "GBPUSD": {"symbol": "FX:GBPUSD", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AGBPUSD&interval=15"},
    "EURJPY": {"symbol": "FX:EURJPY", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AEURJPY&interval=15"},
    "USDCAD": {"symbol": "FX:USDCAD", "tv_url": "https://www.tradingview.com/chart/?symbol=FX%3AUSDCAD&interval=15"},
}

# Config da estratégia CHoCH+FVG M15 + CRT + S/R + Weekly Bias (v4)
# Backtest V5 (25/05): CRT 3t/100%WR/+24.2p vs baseline 9t/66.7%WR/+33.8p
# Backtest 7d: CRT+S/R 3t/100%WR/+26.3p vs CRT apenas 6t/83.3%WR
# Backtest V3 (10d): Sweep+CRT 4t/100%WR/+3.84% (apenas London Close ativou)
STRATEGY = {
    "version": "v4-crt-sr",
    "timeframe": "M15",
    "min_gap_pips": 5,
    "active_hours_utc": [6, 7, 11, 15, 16],  # London Open + London Close + NY Open (UTC)
    "rr_ratio": 3.0,
    "max_trades_per_day": 4,
    "crt_required": True,   # CRT = Critical filter: wick>body*1.3 + min 2p wick
    "sr_required": True,    # S/R = Support/Resistance filter (100% WR quando combinado)
    "use_weekly_bias": True,
    "killzones_brt": {
        "london_open": "05:00-07:00",
        "ny_open": "10:00-12:00",
        "london_close": "12:00-14:00"
    }
}

def load_weekly_bias():
    """Carrega o viés semanal dos pares."""
    if WEEKLY_BIAS_FILE.exists():
        try:
            bias = json.loads(WEEKLY_BIAS_FILE.read_text())
            return bias.get("pairs", {})
        except:
            pass
    return {}


def get_tv_data(pair_key):
    """Extrai dados do chart TradingView via CDP browser."""
    import subprocess
    pair = PAIRS[pair_key]
    
    # Navega para o chart
    subprocess.run([
        "python3", str(HERMES / "scripts" / "brain_browser.py"),
        "--navigate", pair["tv_url"],
        "--content"
    ], capture_output=True, timeout=20)
    
    time.sleep(2)
    
    # Tenta extrair preço atual via eval JavaScript
    result = subprocess.run([
        "python3", str(HERMES / "scripts" / "brain_browser.py"),
        "--eval",
        """
        (function() {
            try {
                // Preço atual do widget TradingView
                var price = document.querySelector('[data-symbol-short]')?.getAttribute('data-last') ||
                           document.querySelector('.last-price-value')?.textContent ||
                           null;
                return JSON.stringify({price: price, ok: true});
            } catch(e) {
                return JSON.stringify({error: e.message, ok: false});
            }
        })()
        """,
        "--json"
    ], capture_output=True, text=True, timeout=15)
    
    try:
        return json.loads(result.stdout) if result.stdout else {"error": "no output"}
    except:
        return {"error": f"parse error: {result.stdout[:100]}", "raw": result.stdout}


def analyze_pair(pair_key, data):
    """Analisa se há setup CHoCH+FVG no par."""
    hour_utc = datetime.now(timezone.utc).hour
    
    # Verifica se está em horário de trading ativo
    if hour_utc not in STRATEGY["active_hours_utc"]:
        return {"signal": None, "reason": f"fora do horário (UTC {hour_utc})"}
    
    # Carrega viés semanal
    weekly_bias = load_weekly_bias() if STRATEGY.get("use_weekly_bias") else {}
    bias = weekly_bias.get(pair_key.replace("/", ""), "NEUTRAL")
    
    # Placeholder - a análise real será feita por mim (agente) via browser tools
    # O cérebro coleta os dados, eu valido visualmente
    return {
        "signal": "PENDING_VALIDATION",
        "pair": pair_key,
        "price": data.get("price", "unknown"),
        "hour_utc": hour_utc,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "needs_human_validation": False,
        "weekly_bias": bias,
        "crt_required": STRATEGY.get("crt_required", True),
        "sr_required": STRATEGY.get("sr_required", True),
        "min_gap_pips": STRATEGY["min_gap_pips"],
        "rr_ratio": STRATEGY["rr_ratio"],
        "strategy_version": STRATEGY.get("version", "v4")
    }


def load_existing_signals():
    """Carrega sinais pendentes existentes."""
    if SIGNALS_FILE.exists():
        try:
            return json.loads(SIGNALS_FILE.read_text())
        except:
            pass
    return {"pending": [], "validated": [], "rejected": [], "executed": []}


def save_signals(signals):
    """Salva sinais no arquivo de pendentes."""
    SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SIGNALS_FILE.write_text(json.dumps(signals, indent=2, ensure_ascii=False, default=str))


def update_brain_context(signals_count):
    """Atualiza o brain_context.json com status forex."""
    if BRAIN_CONTEXT.exists():
        try:
            ctx = json.loads(BRAIN_CONTEXT.read_text())
        except:
            ctx = {}
        
        bias = load_weekly_bias()
        ctx["forex_status"] = {
            "signals_pending": signals_count,
            "last_scan": datetime.now(timezone.utc).isoformat(),
            "strategy": "CHoCH+FVG M15 + CRT + S/R + Weekly Bias (v4)",
            "weekly_bias": bias,
            "crt_enabled": True,
            "sr_enabled": True
        }
        BRAIN_CONTEXT.write_text(json.dumps(ctx, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Brain Signal Generator")
    parser.add_argument("--pair", help="Par específico (EURUSD, USDJPY, GBPUSD)")
    parser.add_argument("--cron", action="store_true", help="Modo silencioso para cron")
    args = parser.parse_args()
    
    pairs_to_scan = [args.pair] if args.pair else list(PAIRS.keys())
    
    if not args.cron:
        print(f"🧠 Brain Signal Generator — {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Estratégia: CHoCH+FVG M15, RR 1:3, CRT: ON")
        print(f"   Horário UTC ativo: {STRATEGY['active_hours_utc']}")
        
        # Mostra viés semanal
        bias = load_weekly_bias()
        if bias:
            print(f"   Viés Semanal: {', '.join(f'{k}={v}' for k,v in bias.items())}")
        print()
    
    signals = load_existing_signals()
    new_signals = 0
    
    for pair_key in pairs_to_scan:
        if not args.cron:
            print(f"📊 Analisando {pair_key}...")
        
        data = get_tv_data(pair_key)
        
        if "error" in str(data):
            if not args.cron:
                print(f"   ⚠️ Erro ao obter dados: {data}")
            continue
        
        analysis = analyze_pair(pair_key, data)
        
        if analysis.get("signal"):
            # Evita duplicar
            existing = [s for s in signals["pending"] if s.get("pair") == pair_key]
            if not existing:
                signals["pending"].append(analysis)
                new_signals += 1
                if not args.cron:
                    print(f"   🔔 SINAL: {pair_key} @ {analysis.get('price')} → VALIDAÇÃO PENDENTE")
            else:
                if not args.cron:
                    print(f"   ⏳ Sinal já existe para {pair_key}, aguardando validação")
        else:
            if not args.cron:
                print(f"   ⚪ Sem setup — {analysis.get('reason', 'condições não atendidas')}")
    
    if new_signals > 0:
        save_signals(signals)
        update_brain_context(len(signals["pending"]))
        if not args.cron:
            print(f"\n✅ {new_signals} novo(s) sinal(is) salvo(s) em {SIGNALS_FILE}")
    else:
        if not args.cron:
            print(f"\n📭 Nenhum sinal novo. Sinais pendentes: {len(signals['pending'])}")
    
    # Salva estado
    state = {
        "last_scan": datetime.now(timezone.utc).isoformat(),
        "pairs_scanned": pairs_to_scan,
        "signals_found": new_signals,
        "total_pending": len(signals["pending"]),
        "total_validated": len(signals["validated"]),
        "total_executed": len(signals["executed"])
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
