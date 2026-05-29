#!/usr/bin/env python3
"""
ANÁLISE COMPARATIVA: FOREX vs CRYPTO
Características de cada mercado e otimizações específicas por agente
"""
import json
from pathlib import Path

print("═══ DIFERENÇAS ESTRUTURAIS ENTRE MERCADOS ═══")
print()

diffs = [
    ("Horário",        "Seg-Sex, sessões fixas",  "24/7 contínuo"),
    ("Volatilidade",   "Sazonal (picos em abertura)", "Constante, eventos-driven"),
    ("Correlação",     "Moeda base (USD/EUR/GBP)", "Tudo vs BTC (85% sinc)"),
    ("Liquidez",       "Altíssima (trilhões/dia)", "Média (concentrada em top 10)"),
    ("Spread",         "0.1-1 pip",                "0.01-0.5% do preço"),
    ("Alavancagem",    "Até 500:1",                "Até 125:1 (spot: 1:1)"),
    ("Notícias",       "CPI, FOMC, NFP",           "Regulação, hacks, ETFs"),
    ("Ciclos",         "Sessões Asia/London/NY",   "Ciclos de 4 anos (halving)"),
    ("Tamanho vela",   "Pips (0.0001)",            "% do preço (0.02-2%)"),
    ("Stop Loss",      "10-20 pips",               "0.1-1% do preço"),
    ("Timeframe ideal","M15/M5/M1",                "H1/M15/M5"),
    ("Padrão técnico", "FVG + CRT + S/R",          "OB + Fibonacci + MS"),
]

print(f"{'Característica':<18s} {'Forex':<30s} {'Crypto':<30s}")
print("-" * 78)
for name, forex, crypto in diffs:
    print(f"{name:<18s} {forex:<30s} {crypto:<30s}")

print()
print("═══ PERFORMANCE POR AGENTE (Backtest) ═══")
print()

perf = [
    ("FOREX", "Padrão (FVG)", "67%", "GBPUSD 100%, AUDUSD 88%", "EURUSD 10% — FVG não funciona"),
    ("FOREX", "Estrutura (CRT)", "18%", "4 trades em 10 dias", "Muito restritivo, perder oportunidades"),
    ("FOREX", "Sessão (Volat)", "N/A", "Contexto apenas", "Virou modificador de peso ✅"),
    ("FOREX", "Perfil (Horário)", "N/A", "Contexto apenas", "Virou modificador de peso ✅"),
    ("CRYPTO", "Padrão (OB)", "70%", "BTC 70%, DOGE 43%", "Motor do sistema"),
    ("CRYPTO", "Tendência (EMA)", "27%", "Gate, não isolado", "Essencial como filtro"),
    ("CRYPTO", "Sessão (Horário)", "21%", "Bônus NY +10", "Impacto baixo, manter"),
    ("CRYPTO", "Fluxo (BTC)", "25%", "Contexto macro", "Útil para alts"),
]

print(f"{'Mercado':<10s} {'Agente':<18s} {'WR':<8s} {'Força':<30s} {'Fraqueza':<30s}")
print("-" * 96)
for m, a, w, strength, weakness in perf:
    print(f"{m:<10s} {a:<18s} {w:<8s} {strength:<30s} {weakness:<30s}")

print()
print("═══ OTIMIZAÇÕES POR MERCADO ═══")
print()

optimizations = {
    "FOREX": [
        ("FVG gap mínimo", "1 pip → 2 pips", "Reduz trades ruins em EURUSD"),
        ("Sessão gate", "Só operar London/NY (7-20h UTC)", "Elimina 60% de ruído"),
        ("Daily bias", "Usar bias real dos dados (não fixo)", "Estrutura passa a funcionar"),
        ("Confluencia", "Padrão sozinho > Conselho atual", "Remover Conselho ou recalibrar"),
        ("Pares", "Remover EURUSD, focar GBP/USD/JPY/AUD", "WR sobe de 10% → 70%"),
    ],
    "CRYPTO": [
        ("Volume real", "Já implementado como bônus", "Manter, não gate"),
        ("Market Structure", "H4/H1 bias mais forte", "Reduz trades contra tendência"),
        ("Multi-TF peso", "H1 +20, M30 +15, M5 obrigatório", "Já implementado ✅"),
        ("BNB/USDT", "Melhor par (89% WR)", "Aumentar peso/alocação"),
        ("DOGE/USDT", "Alta volatilidade", "SL mais largo (0.3% vs 0.15%)"),
    ]
}

for market, opts in optimizations.items():
    print(f"\n  {market}:")
    for title, action, impact in opts:
        print(f"    {title:<25s} → {action:<35s} | {impact}")

print()
print("═══ ARQUITETURA IDEAL POR MERCADO ═══")
print()

arch = """
  FOREX (Sessão-dependente):
  ┌──────────┐    ┌───────────┐    ┌──────────┐
  │ Sessão   │───▶│ Estrutura  │───▶│ Padrão   │───▶ TRADE
  │ (gate)   │    │ (CRT/FVG)  │    │ (FVG)    │
  └──────────┘    └───────────┘    └──────────┘
       │                                │
       └── Perfil (mod. peso) ──────────┘

  CRYPTO (24/7 contínuo):
  ┌──────────┐    ┌───────────┐    ┌──────────┐
  │ Tendência│───▶│ Market Str│───▶│ Padrão   │───▶ TRADE
  │ (H1/H4)  │    │ (gate)    │    │ (OB+Fib) │
  └──────────┘    └───────────┘    └──────────┘
       │                                │
       ├── Sessão (bônus NY) ───────────┤
       └── Fluxo (BTC corr) ────────────┘
"""
print(arch)

print("═══ CONCLUSÃO ═══")
print("  Cada mercado tem características ÚNICAS:")
print("  • Forex = sessão + moeda base + pips")
print("  • Crypto = tendência + structure + % preço")
print("  • Agentes NÃO são intercambiáveis entre mercados")
print("  • Especialização por mercado é o caminho correto ✅")
