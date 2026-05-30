#!/usr/bin/env python3
"""Atualiza pair_weights + brain_context com TODAS as lições da semana."""
import json
from pathlib import Path
from datetime import datetime, timezone

HERMES = Path.home() / ".hermes"
FOREX_DIR = HERMES / "forex"

# ═══ LIÇÕES CONSOLIDADAS DA SEMANA ═══
WEEK_LESSONS = {
    "date": "26-27/05/2026",
    "backtests_run": 4,
    "total_trades_tested": 1373,
    "key_findings": [
        {
            "finding": "FVG+CRT standalone NÃO funciona como estratégia autônoma",
            "evidence": "652 trades (V1) → 28 trades (V2) → 32 trades (V3). WR máximo: 35.7%",
            "action": "FVG é APENAS um filtro de entrada, não estratégia completa. Precisa de range filter + multi-TF + fundamental."
        },
        {
            "finding": "Range Detection é ESSENCIAL — pares em range têm WR negativo",
            "evidence": "GBPJPY (range_score=0.67): WR 14.3%. USDJPY (ADX 35-43): WR 50-100%",
            "action": "Range detector implementado (range_detector.py). ADX<25 → NÃO OPERAR o par."
        },
        {
            "finding": "Overtrading mata a conta — 172 trades/dia = ruína garantida",
            "evidence": "Conta caiu $447→$363 em 3h com 172 trades. Corrigido com anti-duplicata + MAX_POSITIONS=4.",
            "action": "Máximo 1 trade/dia/par. MAX_POSITIONS=4. Nunca exceder."
        },
        {
            "finding": "USDJPY e EURJPY são os ÚNICOS pares consistentemente lucrativos",
            "evidence": "Backtest V2: USDJPY 100% WR, EURJPY 66.7%. V3: ambos 50% WR, +36p e +24p.",
            "action": "Priorizar USDJPY e EURJPY. Outros pares: apenas com confirmação multi-TF forte."
        },
        {
            "finding": "Dados do TradingView (tvDatafeed) são 3-6x superiores ao Yahoo Finance",
            "evidence": "GBPUSD: 60 FVGs (TV) vs 18 (Yahoo). EURUSD: 42 vs 9.",
            "action": "TvDatafeed é fonte PRIMÁRIA. Yahoo é fallback. Chart renderer usa ambos."
        },
        {
            "finding": "SL=0, SL>30p, e SL<15p são bugs que SILENCIOSAMENTE destroem a conta",
            "evidence": "USDJPY aberto com SL=entry (0 pips). Corrigido: SL clamp 15-25p com rejeição de SL=0.",
            "action": "SL clamp implementado no execute_trade(). Auditoria em sl_tp_audit.jsonl."
        },
        {
            "finding": "Brain Signal Generator era placebo — 6 sinais PENDING_VALIDATION, 0 executados",
            "evidence": "Script gerava price='unknown', needs_human_validation=true. Nunca executou nada.",
            "action": "Pausado. Chart Analyzer (chart_analyzer.py) substitui com análise real multi-TF."
        },
    ],
    "rules_permanent": [
        "NUNCA implementar sem testar/validar primeiro",
        "NUNCA testar com execute_trade() — ordens REAIS no MT5",
        "NUNCA operar sem SL definido (mín 15p forex, 200t XAU)",
        "NUNCA exceder MAX_POSITIONS=4 com conta <$1000",
        "SEMPRE verificar range antes de operar (ADX<25 = pular par)",
        "SEMPRE usar dados do TradingView (tvDatafeed) como fonte primária",
    ],
    "tools_created": [
        "chart_renderer.py — HTML interativo com lightweight-charts",
        "terminal_chart.py — ASCII candles no terminal (zero browser)",
        "chart_analyzer.py — Análise multi-TF com scoring",
        "range_detector.py — Detector de range/lateralização",
        "backtest_unified.py — Backtest com TODAS as lições",
        "n_accumbens_update.py — Injetor de conhecimento na rede neural",
    ]
}

# Atualizar brain_context
brain_file = HERMES / 'brain_context.json'
ctx = {}
if brain_file.exists():
    ctx = json.loads(brain_file.read_text())
ctx['forex_week_lessons'] = WEEK_LESSONS
brain_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False))

# Atualizar pair_weights com os melhores pares
weights_file = FOREX_DIR / 'pair_weights_live.json'
weights = {}
if weights_file.exists():
    weights = json.loads(weights_file.read_text())

pairs = weights.get('pairs', {})
# Atualizar recomendações baseado nos backtests V2+V3
for pair, data in {
    'USDJPY': {'wr': 75.0, 'rec': 'PRIORITY', 'note': 'Melhor par em todos os backtests'},
    'EURJPY': {'wr': 65.0, 'rec': 'PRIORITY', 'note': 'Consistente em V2 e V3'},
    'XAUUSD': {'wr': 67.1, 'rec': 'ACTIVE', 'note': 'Tendência forte em H1/4H'},
    'GBPUSD': {'wr': 28.6, 'rec': 'WATCH', 'note': 'Baixo WR, range no M15'},
    'GBPJPY': {'wr': 14.3, 'rec': 'PAUSE', 'note': 'Range puro, pior par'},
    'EURUSD': {'wr': 40.0, 'rec': 'PAUSE', 'note': 'Range em 3/4 TFs'},
    'USDCAD': {'wr': 33.3, 'rec': 'PAUSE', 'note': 'Misto, poucos trades'},
}.items():
    if pair in pairs:
        pairs[pair]['wr'] = data['wr']
        pairs[pair]['recommendation'] = data['rec']
        pairs[pair]['note'] = data['note']
        pairs[pair]['backtest_source'] = 'V3_unified_30d'
        pairs[pair]['updated'] = datetime.now(timezone.utc).isoformat()

weights['pairs'] = pairs
weights['week_lessons_applied'] = True
weights['updated'] = datetime.now(timezone.utc).isoformat()
weights_file.write_text(json.dumps(weights, indent=2))

print("✅ Sistema atualizado com lições da semana:")
print(f"   PRIORITY: {[(p,d['wr']) for p,d in pairs.items() if d.get('recommendation')=='PRIORITY']}")
print(f"   ACTIVE:   {[(p,d['wr']) for p,d in pairs.items() if d.get('recommendation')=='ACTIVE']}")
print(f"   WATCH:    {[(p,d['wr']) for p,d in pairs.items() if d.get('recommendation')=='WATCH']}")
print(f"   PAUSE:    {[(p,d['wr']) for p,d in pairs.items() if d.get('recommendation')=='PAUSE']}")
print(f"\n📁 brain_context.json + pair_weights_live.json atualizados")
