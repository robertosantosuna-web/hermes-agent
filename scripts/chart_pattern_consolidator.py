#!/usr/bin/env python3
"""
Chart Pattern Consolidator — transforma 1.5MB de dados em insights acionáveis.
Lê o arquivo mais recente de chart_patterns, consolida por par/tipo/timeframe,
e salva um resumo compacto + sinais para o bot.

Uso:
  python3 chart_pattern_consolidator.py           # Consolida o último dump
  python3 chart_pattern_consolidator.py --all      # Consolida todos os dumps
  python3 chart_pattern_consolidator.py --json     # Output JSON apenas
"""

import json, sys, os
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict

HERMES = Path.home() / ".hermes"
PATTERNS_DIR = HERMES / "forex" / "chart_patterns"
SUMMARY_FILE = HERMES / "forex" / "chart_patterns_summary.json"
SIGNALS_FILE = HERMES / "forex" / "chart_signals.json"

# Padrões bullish/bearish
BIAS_MAP = {
    "HEAD_AND_SHOULDERS": "BEARISH",
    "INVERSE_HEAD_AND_SHOULDERS": "BULLISH",
    "DOUBLE_TOP": "BEARISH",
    "DOUBLE_BOTTOM": "BULLISH",
    "CUP_HANDLE": "BULLISH",
    "ASCENDING_TRIANGLE": "BULLISH",
    "DESCENDING_TRIANGLE": "BEARISH",
    "SYMMETRICAL_TRIANGLE": "NEUTRAL",
    "WEDGE_RISING": "BEARISH",
    "WEDGE_FALLING": "BULLISH",
    "FLAG_BULL": "BULLISH",
    "FLAG_BEAR": "BEARISH",
    "PENNANT_BULL": "BULLISH",
    "PENNANT_BEAR": "BEARISH",
}


def load_latest():
    """Carrega o arquivo de padrões mais recente."""
    files = sorted(PATTERNS_DIR.glob("chart_patterns_*.json"), reverse=True)
    if not files:
        print("Nenhum arquivo de padrões encontrado.", file=sys.stderr)
        return None, None
    
    latest = files[0]
    ts_str = latest.stem.replace("chart_patterns_", "")
    try:
        ts = datetime.strptime(ts_str, "%Y%m%d_%H%M")
    except:
        ts = datetime.now()
    
    with open(latest) as f:
        data = json.load(f)
    
    return data, ts


def consolidate(data, ts):
    """Consolida padrões em resumo por par/timeframe/tipo."""
    summary = {
        "timestamp": ts.isoformat(),
        "pairs": {},
        "global": {
            "total_patterns": 0,
            "high_confidence": 0,  # ≥80%
            "bullish": 0,
            "bearish": 0,
            "neutral": 0,
        }
    }
    
    for pair_data in data:
        pair = pair_data["pair"]
        pair_summary = {"patterns_by_tf": {}, "signals": []}
        
        for tf, tf_data in pair_data.get("timeframes", {}).items():
            patterns = tf_data.get("patterns", [])
            if not patterns:
                continue
            
            type_counts = Counter()
            confidences = []
            biases = Counter()
            
            for p in patterns:
                ptype = p.get("type", "UNKNOWN")
                conf = p.get("confidence", 0)
                bias = BIAS_MAP.get(ptype, p.get("bias", "NEUTRAL"))
                
                type_counts[ptype] += 1
                confidences.append(conf)
                biases[bias] += 1
                
                summary["global"]["total_patterns"] += 1
                if conf >= 80:
                    summary["global"]["high_confidence"] += 1
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            dominant_bias = biases.most_common(1)[0][0] if biases else "NEUTRAL"
            
            pair_summary["patterns_by_tf"][tf] = {
                "count": len(patterns),
                "avg_confidence": round(avg_conf, 1),
                "dominant_bias": dominant_bias,
                "top_patterns": type_counts.most_common(3),
                "bias_distribution": dict(biases),
            }
            
            # Gerar sinal se dominância ≥ 70%
            for bias, count in biases.items():
                if count >= len(patterns) * 0.7 and len(patterns) >= 3:
                    top = type_counts.most_common(1)[0]
                    pair_summary["signals"].append({
                        "pair": pair,
                        "timeframe": tf,
                        "bias": bias,
                        "confidence": round(avg_conf, 1),
                        "top_pattern": top[0],
                        "pattern_count": count,
                        "total": len(patterns),
                    })
        
        summary["global"]["bullish"] += biases.get("BULLISH", 0)
        summary["global"]["bearish"] += biases.get("BEARISH", 0)
        summary["global"]["neutral"] += biases.get("NEUTRAL", 0)
        summary["pairs"][pair] = pair_summary
    
    return summary


def save_signals(summary):
    """Extrai sinais para o bot consumir."""
    signals = []
    for pair, data in summary.get("pairs", {}).items():
        for s in data.get("signals", []):
            signals.append(s)
    
    # Ordenar por confiança
    signals.sort(key=lambda s: s["confidence"], reverse=True)
    
    SIGNALS_FILE.write_text(json.dumps({
        "generated": datetime.now().isoformat(),
        "signals": signals,
        "note": "Sinais baseados em dominância de padrões ≥70%. Usar como filtro adicional, não entrada isolada."
    }, indent=2))
    
    return signals


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Consolida todos os dumps (não só último)")
    parser.add_argument("--json", action="store_true", help="Output JSON apenas")
    args = parser.parse_args()
    
    data, ts = load_latest()
    if not data:
        sys.exit(1)
    
    summary = consolidate(data, ts)
    signals = save_signals(summary)
    
    # Salvar resumo
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, default=str))
    
    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        g = summary["global"]
        print(f"📊 Chart Pattern Consolidator — {ts.strftime('%d/%m %H:%M')}")
        print(f"   Total: {g['total_patterns']} padrões | Alta confiança (≥80%): {g['high_confidence']}")
        print(f"   Viés: 🐂 {g['bullish']} bullish | 🐻 {g['bearish']} bearish | ⚪ {g['neutral']} neutral")
        print()
        
        if signals:
            print(f"🔔 {len(signals)} sinais gerados:")
            for s in signals[:5]:
                emoji = "🟢" if s["bias"] == "BULLISH" else "🔴" if s["bias"] == "BEARISH" else "⚪"
                print(f"   {emoji} {s['pair']} {s['timeframe']} — {s['bias']} ({s['confidence']}%) — {s['top_pattern']} ({s['pattern_count']}/{s['total']})")
        else:
            print("📭 Nenhum sinal forte (dominância < 70%).")
        
        print(f"\n📁 Resumo: {SUMMARY_FILE}")
        print(f"📁 Sinais: {SIGNALS_FILE}")


if __name__ == "__main__":
    main()
