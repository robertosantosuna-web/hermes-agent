#!/usr/bin/env python3
"""
Forex Backtest V3 — Parâmetros adaptados por par
Dados reais: EURJPY 6.3p avg, USDJPY 6.2p, GBPUSD 4.1p, EURUSD 2.2p (5m)
"""
import yfinance as yf, pandas as pd
from datetime import datetime, timedelta
import sys

# ─── PER-PAIR PARAMETERS (5m candles, real data calibrated) ──
PAIR_CONFIG = {
    "EURJPY=X": {"name": "EUR/JPY", "pip": 0.01,  "stop_min": 5, "stop_max": 10,
                 "range_min": 8, "momentum_min": 4, "wick_ratio": 1.3},
    "JPY=X":    {"name": "USD/JPY", "pip": 0.01,  "stop_min": 5, "stop_max": 8,
                 "range_min": 7, "momentum_min": 3, "wick_ratio": 1.3},
    "GBPUSD=X": {"name": "GBP/USD", "pip": 0.0001,"stop_min": 4, "stop_max": 8,
                 "range_min": 6, "momentum_min": 3, "wick_ratio": 1.2},
    "EURUSD=X": {"name": "EUR/USD", "pip": 0.0001,"stop_min": 3, "stop_max": 5,
                 "range_min": 4, "momentum_min": 2, "wick_ratio": 1.2},
    "EURGBP=X": {"name": "EUR/GBP", "pip": 0.0001,"stop_min": 3, "stop_max": 5,
                 "range_min": 4, "momentum_min": 2, "wick_ratio": 1.2},
}

KILLZONES = {
    "🇬🇧 London":       (7.0, 7.5,  ["EURJPY=X", "JPY=X", "GBPUSD=X"]),
    "🇺🇸 NY":           (12.5, 13.0, ["EURJPY=X", "JPY=X", "GBPUSD=X"]),
    "🇬🇧🇺🇸 LondonClose": (15.0, 15.5, ["EURJPY=X", "JPY=X", "GBPUSD=X"]),
}

RR = 2.0
LEV = 30

# ─── DATA ─────────────────────────────────────────────────
def fetch_all(days=10):
    pairs = list(PAIR_CONFIG.keys())
    print(f"📡 Baixando 5m para {len(pairs)} pares ({days}d)...")
    data = {}
    for sym in pairs:
        try:
            df = yf.download(sym, period=f"{days}d", interval="5m", progress=False, auto_adjust=False)
            if len(df) > 0:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                candles = []
                for idx, row in df.iterrows():
                    candles.append({
                        "dt": idx.to_pydatetime(), "o": float(row["Open"]),
                        "h": float(row["High"]), "l": float(row["Low"]),
                        "c": float(row["Close"])
                    })
                data[sym] = candles
                print(f"  ✅ {PAIR_CONFIG[sym]['name']:8s} → {len(candles)} candles")
        except Exception as e:
            print(f"  ⚠️ {sym} → {e}")
    return data

# ─── CRT ───────────────────────────────────────────────────
def body(c): return abs(c["c"] - c["o"])
def uw(c): return c["h"] - max(c["o"], c["c"])
def lw(c): return min(c["o"], c["c"]) - c["l"]
def rng(c): return c["h"] - c["l"]

def detect_sweep(ctx, cfg, pip_v):
    if len(ctx) < 3: return None
    cur, prev = ctx[-1], ctx[-2]
    b, uw_, lw_ = body(cur), uw(cur), lw(cur)
    wr = cfg["wick_ratio"]
    
    # Sweep alta → SELL (bearish close after fake breakout)
    if (cur["h"] > prev["h"] and uw_ > b * wr and 
        cur["c"] < cur["o"] and  # bearish candle
        uw_ / pip_v >= 2):  # min 2 pips wick
        sp = min(max(rng(cur) / pip_v * 0.6, cfg["stop_min"]), cfg["stop_max"])
        return {"type": "SELL", "entry": cur["c"],
                "reason": f"SH l={cur['l']:.5f}<{prev['l']:.5f} w={uw_/pip_v:.1f}p",
                "stop_pips": sp, "wick_pips": uw_/pip_v}
    
    # Sweep baixa → BUY (bullish close after fake breakdown)
    if (cur["l"] < prev["l"] and lw_ > b * wr and 
        cur["c"] > cur["o"] and  # bullish candle
        lw_ / pip_v >= 2):
        sp = min(max(rng(cur) / pip_v * 0.6, cfg["stop_min"]), cfg["stop_max"])
        return {"type": "BUY", "entry": cur["c"],
                "reason": f"SL l={cur['l']:.5f}<{prev['l']:.5f} w={lw_/pip_v:.1f}p",
                "stop_pips": sp, "wick_pips": lw_/pip_v}
    return None

def ok_momentum(ctx, pip_v, min_p):
    if len(ctx) < 3: return False
    return abs(ctx[-1]["c"] - ctx[-3]["o"]) / pip_v >= min_p

def ok_range(ctx, pip_v, min_r):
    if len(ctx) < 5: return False
    return sum(rng(c) for c in ctx[-5:]) / 5 / pip_v >= min_r

# ─── SIM ───────────────────────────────────────────────────
def simulate(data):
    trades = []
    
    for kz_name, (start_h, end_h, pairs) in KILLZONES.items():
        for sym in pairs:
            if sym not in data: continue
            cfg = PAIR_CONFIG[sym]
            pip_v = cfg["pip"]
            all_c = data[sym]
            days = sorted(set(c["dt"].date() for c in all_c))
            
            for day in days:
                day_c = [c for c in all_c if c["dt"].date() == day]
                if len(day_c) < 10: continue
                
                # Killzone candles
                kz_c = [c for c in day_c if start_h <= c["dt"].hour + c["dt"].minute/60 < end_h]
                if len(kz_c) < 3: continue
                
                # Pre-killzone context (60 min = 12 candles 5m)
                kz_start = kz_c[0]["dt"]
                pre = [c for c in day_c if c["dt"] < kz_start][-12:]
                if len(pre) < 5: continue
                
                # Range filter
                if not ok_range(pre, pip_v, cfg["range_min"]): continue
                
                # Walk candles
                ctx = list(pre[-5:])
                in_trade = None
                ds = day.strftime("%d/%m")
                
                for i, c in enumerate(kz_c):
                    ctx.append(c)
                    
                    if in_trade:
                        elapsed = (c["dt"] - in_trade["et"]).total_seconds() / 60
                        ep, sp, tp = in_trade["ep"], in_trade["stop"], in_trade["target"]
                        typ = in_trade["type"]
                        
                        if typ == "BUY":
                            if c["l"] <= sp:
                                pnl = (sp - ep) / pip_v
                                trades.append(mk(sym, kz_name, typ, "LOSS", ep, sp, pnl, cfg, in_trade["reason"], ds, c["dt"], elapsed))
                                in_trade = None; continue
                            if c["h"] >= tp:
                                pnl = (tp - ep) / pip_v
                                trades.append(mk(sym, kz_name, typ, "WIN", ep, tp, pnl, cfg, in_trade["reason"], ds, c["dt"], elapsed))
                                in_trade = None; continue
                        else:
                            if c["h"] >= sp:
                                pnl = (ep - sp) / pip_v
                                trades.append(mk(sym, kz_name, typ, "LOSS", ep, sp, pnl, cfg, in_trade["reason"], ds, c["dt"], elapsed))
                                in_trade = None; continue
                            if c["l"] <= tp:
                                pnl = (ep - tp) / pip_v
                                trades.append(mk(sym, kz_name, typ, "WIN", ep, tp, pnl, cfg, in_trade["reason"], ds, c["dt"], elapsed))
                                in_trade = None; continue
                        
                        if i == len(kz_c) - 1:
                            ex = c["c"]
                            pnl = (ex - ep) / pip_v if typ == "BUY" else (ep - ex) / pip_v
                            res = "WIN" if pnl > 0 else "LOSS"
                            trades.append(mk(sym, kz_name, typ, f"{res}⏰", ep, ex, pnl, cfg, in_trade["reason"], ds, c["dt"], elapsed))
                            in_trade = None
                        continue
                    
                    # Entry
                    if len(ctx) < 4: continue
                    if not ok_momentum(ctx, pip_v, cfg["momentum_min"]): continue
                    
                    sig = detect_sweep(ctx, cfg, pip_v)
                    if not sig: continue
                    
                    sp = sig["stop_pips"]
                    ep = sig["entry"]
                    in_trade = {
                        "type": sig["type"], "ep": ep, "et": c["dt"],
                        "stop": ep - sp * pip_v if sig["type"] == "BUY" else ep + sp * pip_v,
                        "target": ep + sp * RR * pip_v if sig["type"] == "BUY" else ep - sp * RR * pip_v,
                        "reason": sig["reason"], "stop_pips": sp
                    }
    
    return trades

def mk(sym, kz, typ, res, ep, ex, pnl, cfg, reason, ds, dt, dur):
    pnl_pct = (pnl * cfg["pip"]) / ep * LEV * 100
    return {
        "pair": cfg["name"], "kz": kz, "type": typ, "result": res,
        "pnl_pips": round(pnl, 1), "pnl_pct": round(pnl_pct, 2),
        "reason": reason, "date": ds, "time": dt.strftime("%H:%M"),
        "duration": f"{dur:.0f}m"
    }

# ─── MAIN ──────────────────────────────────────────────────
def main():
    print("═" * 60)
    print("  FOREX BACKTEST V3 — ICT Killzones + CRT (calibrado)")
    print("═" * 60)
    for sym, cfg in PAIR_CONFIG.items():
        print(f"  {cfg['name']:8s}: stop {cfg['stop_min']}-{cfg['stop_max']}p, range >{cfg['range_min']}p, mom >{cfg['momentum_min']}p")
    print()
    
    data = fetch_all(10)
    if not data: print("❌ Sem dados"); return
    
    trades = simulate(data)
    
    if not trades:
        print("\n⚠️ 0 trades. Mercado lateral extremo nos últimos 10 dias.")
        return
    
    wins = [t for t in trades if "WIN" in t["result"]]
    losses = [t for t in trades if "LOSS" in t["result"]]
    total_pnl = sum(t["pnl_pct"] for t in trades)
    wr = len(wins) / len(trades) * 100 if trades else 0
    
    print(f"\n{'═' * 60}")
    print(f"  📊 {len(trades)} TRADES EM 10 DIAS")
    print(f"{'═' * 60}")
    print(f"  Wins:        {len(wins)} ({wr:.0f}%)")
    print(f"  Losses:      {len(losses)}")
    print(f"  Avg win:     {sum(t['pnl_pips'] for t in wins)/max(len(wins),1):+.1f}p")
    print(f"  Avg loss:    {sum(t['pnl_pips'] for t in losses)/max(len(losses),1):+.1f}p")
    print(f"  P&L total:   {total_pnl:+.2f}%")
    print(f"  P&L/trade:   {total_pnl/len(trades):+.2f}%")
    
    print(f"\n📋 TODOS OS TRADES")
    print(f"  {'Data':6s} {'KZ':20s} {'Par':8s} {'T':5s} {'Result':10s} {'Pips':>7s} {'PnL':>7s} {'Dur':5s}  Motivo")
    for t in sorted(trades, key=lambda x: (x["date"], x["kz"], x["time"])):
        print(f"  {t['date']:6s} {t['kz']:20s} {t['pair']:8s} {t['type']:5s} {t['result']:10s} {t['pnl_pips']:>+6.1f}p {t['pnl_pct']:>+6.2f}% {t['duration']:>4s}  {t['reason']}")
    
    print(f"\n📊 POR KILLZONE")
    for kz_name in KILLZONES:
        kt = [t for t in trades if t["kz"] == kz_name]
        if kt:
            kw = [t for t in kt if "WIN" in t["result"]]
            print(f"  {kz_name:20s}: {len(kt):2d} trades, {len(kw)} wins, {sum(t['pnl_pct'] for t in kt):+.2f}%")
    
    print(f"\n📊 POR PAR")
    for pair in sorted(set(t["pair"] for t in trades)):
        pt = [t for t in trades if t["pair"] == pair]
        pw = [t for t in pt if "WIN" in t["result"]]
        print(f"  {pair:8s}: {len(pt)} trades, {len(pw)} wins, {sum(t['pnl_pct'] for t in pt):+.2f}%")
    
    print(f"\n{'═' * 60}")
    if total_pnl > 5 and wr > 45:
        print(f"  ✅ VIÁVEL! +{total_pnl:.1f}% em 10 dias, {wr:.0f}% WR.")
        print(f"  → OANDA demo com 0.01 lote.")
    elif total_pnl > 0:
        print(f"  ⚠️ MARGINAL: +{total_pnl:.1f}%, {wr:.0f}% WR.")
        print(f"  → Refinar filtros ou esperar volatilidade.")
    else:
        print(f"  ❌ NEGATIVO: {total_pnl:.1f}%.")
    print(f"{'═' * 60}")

if __name__ == "__main__":
    main()
