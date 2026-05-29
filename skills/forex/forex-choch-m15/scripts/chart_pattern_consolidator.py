#!/usr/bin/env python3
"""
Chart Pattern Consolidator — transforma 1.5MB de dados em insights acionáveis.
Lê o arquivo mais recente de chart_patterns, consolida por par/tipo/timeframe,
e salva um resumo compacto + sinais para o bot.

Uso:
  python3 chart_pattern_consolidator.py           # Consolida o último dump
  python3 chart_pattern_consolidator.py --json     # Output JSON apenas

Output: ~/.hermes/forex/chart_patterns_summary.json + chart_signals.json
"""
import json, sys, os
from pathlib import Path
from datetime import datetime
from collections import Counter

HERMES = Path.home() / ".hermes"
PATTERNS_DIR = HERMES / "forex" / "chart_patterns"
SUMMARY_FILE = HERMES / "forex" / "chart_patterns_summary.json"
SIGNALS_FILE = HERMES / "forex" / "chart_signals.json"

BIAS_MAP = {
    "HEAD_AND_SHOULDERS": "BEARISH", "INVERSE_HEAD_AND_SHOULDERS": "BULLISH",
    "DOUBLE_TOP": "BEARISH", "DOUBLE_BOTTOM": "BULLISH",
    "CUP_HANDLE": "BULLISH", "ASCENDING_TRIANGLE": "BULLISH",
    "DESCENDING_TRIANGLE": "BEARISH", "SYMMETRICAL_TRIANGLE": "NEUTRAL",
    "WEDGE_RISING": "BEARISH", "WEDGE_FALLING": "BULLISH",
    "FLAG_BULL": "BULLISH", "FLAG_BEAR": "BEARISH",
    "PENNANT_BULL": "BULLISH", "PENNANT_BEAR": "BEARISH",
}


def load_latest():
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
    summary = {
        "timestamp": ts.isoformat(), "pairs": {},
        "global": {"total_patterns": 0, "high_confidence": 0, "bullish": 0, "bearish": 0, "neutral": 0}
    }
    
    for pair_data in data:
        pair = pair_data["pair"]
        pair_summary = {"patterns_by_tf": {}, "signals": []}
        
        for tf, tf_data in pair_data.get("timeframes", {}).items():
            patterns = tf_data.get("patterns", [])
            if not patterns:
                continue
            
            type_counts = Counter()
            biases = Counter()
            confidences = []
            
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
                "count": len(patterns), "avg_confidence": round(avg_conf, 1),
                "dominant_bias": dominant_bias, "top_patterns": type_counts.most_common(3),
                "bias_distribution": dict(biases),
            }
            
            for bias, count in biases.items():
                if count >= len(patterns) * 0.7 and len(patterns) >= 3:
                    top = type_counts.most_common(1)[0]
                    pair_summary["signals"].append({
                        "pair": pair, "timeframe": tf, "bias": bias,
                        "confidence": round(avg_conf, 1), "top_pattern": top[0],
                        "pattern_count": count, "total": len(patterns),
                    })
        
        summary["global"]["bullish"] += biases.get("BULLISH", 0)
        summary["global"]["bearish"] += biases.get("BEARISH", 0)
        summary["global"]["neutral"] += biases.get("NEUTRAL", 0)
        summary["pairs"][pair] = pair_summary
    
    return summary


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    
    data, ts = load_latest()
    if not data:
        sys.exit(1)
    
    summary = consolidate(data, ts)
    
    # Salvar sinais
    signals = []
    for pair, pair_data in summary.get("pairs", {}).items():
        for s in pair_data.get("signals", []):
            signals.append(s)
    signals.sort(key=lambda s: s["confidence"], reverse=True)
    SIGNALS_FILE.write_text(json.dumps({"generated": datetime.now().isoformat(), "signals": signals}, indent=2))
    
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2, default=str))
    
    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        g = summary["global"]
        print(f"📊 Chart Pattern Consolidator — {ts:%d/%m %H:%M}")
        print(f"   Total: {g['total_patterns']} | Alta confiança: {g['high_confidence']}")
        print(f"   🐂 {g['bullish']} bullish | 🐻 {g['bearish']} bearish")
        if signals:
            print(f"\n🔔 {len(signals)} sinais:")
            for s in signals[:5]:
                e = "🟢" if s["bias"] == "BULLISH" else "🔴"
                print(f"   {e} {s['pair']} {s['timeframe']} — {s['bias']} ({s['confidence']}%)")


if __name__ == "__main__":
    main()
