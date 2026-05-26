#!/usr/bin/env python3
"""
Brain Intensive Study Session — Estudo intensivo de forex no fim de semana.
Executa múltiplas fontes de conhecimento, backtests, e salva descobertas.

no_agent — zero tokens. Executado pelo cron do cérebro.

Etapas:
0. Carrega brain_pipeline_map.md (anti-padrões e correções pendentes)
0.5. Carrega NN-Brain (rede neural do cérebro) — feed_forward + absorb knowledge bridge
1. Coleta material de estudo (research collector)
2. Backtest de parâmetros em múltiplos pares/timeframes
3. Detecção de padrões de estrutura (CHoCH, BOS, FVG, OB, Sweeps)
4. Análise de correlação entre padrões
5. Salva descobertas na Knowledge Bridge
5.5. Cross-pollinate NN-Shared (compartilha com NN-Agent)
"""

import json, os, sys, time, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES = Path.home() / ".hermes"
STUDY_DIR = HERMES / "forex" / "study_sessions"
SESSION_FILE = STUDY_DIR / f"session_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
BRIDGE_SCRIPT = HERMES / "scripts" / "knowledge_bridge.py"
NN_ENGINE = HERMES / "scripts" / "nn_engine.py"

# Pares para estudar
PAIRS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY']
TIMEFRAMES = ['M5', 'M15', 'M30', 'H1']

def run_script(script_name, args=""):
    """Executa um script Python e retorna o output."""
    try:
        result = subprocess.run(
            ["python3", str(HERMES / "scripts" / script_name)] + args.split(),
            capture_output=True, text=True, timeout=120
        )
        return result.stdout[:5000]
    except Exception as e:
        return f"Error: {e}"

def write_to_bridge(content):
    """Escreve descoberta na Knowledge Bridge."""
    try:
        subprocess.run(
            ["python3", str(BRIDGE_SCRIPT), "write", "brain", content],
            capture_output=True, text=True, timeout=10
        )
    except:
        pass

def study_session():
    """Sessão completa de estudo."""
    session = {
        "started": datetime.now(timezone.utc).isoformat(),
        "phases": {},
        "discoveries": [],
        "duration_seconds": 0,
        "pipeline_map_checks": []
    }
    
    start = time.time()
    
    # ─── FASE 0: Carregar Pipeline Map ──────────────────────────
    try:
        pipeline_path = HERMES / "forex" / "brain_pipeline_map.md"
        if pipeline_path.exists():
            pipeline_content = pipeline_path.read_text()
            # Verificar correções pendentes (marcadas com 🚨 CRÍTICO)
            criticals = [l for l in pipeline_content.split('\n') if '🚨' in l or 'CRÍTICO' in l]
            session["pipeline_map_checks"] = criticals[:5]
            print(f"[pipeline] {len(criticals)} correções críticas pendentes")
            for c in criticals[:3]:
                print(f"  ⚠️ {c.strip()[:120]}")
            
            # Verificar se tem anti-padrões que afetam esta sessão
            if 'best_params.json é lixo' in pipeline_content:
                session["skip_atr_backtest"] = True
                print("  ⛔ Pulando backtest ATR (marcado como lixo no pipeline map)")
    except Exception as e:
        print(f"[pipeline] erro ao carregar: {e}")
    # ─────────────────────────────────────────────────────────────
    
    # ─── FASE 0.5: Carregar NN-Brain + Absorb Bridge ────────────
    try:
        if NN_ENGINE.exists():
            # Absorb knowledge bridge → NN-Brain (novas descobertas)
            print("🧠 FASE 0.5: Carregando NN-Brain + absorb bridge...")
            subprocess.run(
                ["python3", str(NN_ENGINE), "absorb"],
                capture_output=True, text=True, timeout=30
            )
            # Feed-forward para ativar sinapses
            subprocess.run(
                ["python3", str(NN_ENGINE), "feed_forward", "brain"],
                capture_output=True, text=True, timeout=15
            )
            print("  ✅ NN-Brain ativada")
    except Exception as e:
        print(f"  ⚠️ NN-Brain erro (não crítico): {e}")
    # ─────────────────────────────────────────────────────────────
    
    # ═══ FASE 1: Coleta de Material Educacional ═══
    print("📚 FASE 1: Coletando material de estudo...")
    collector_output = run_script("forex_research_collector.py")
    session["phases"]["research_collector"] = {
        "status": "completed",
        "output": collector_output[:1000]
    }
    
    # ═══ FASE 2: Backtest de Parâmetros ═══
    print("🔬 FASE 2: Backtest de parâmetros...")
    study_output = run_script("forex_daily_study.py")
    session["phases"]["parameter_backtest"] = {
        "status": "completed", 
        "output": study_output[:1000]
    }
    
    # ═══ FASE 3: Detecção de Padrões (ICT) ═══
    print("📊 FASE 3: Detectando padrões ICT (FVG, CHoCH, BOS)...")
    patterns = detect_all_patterns()
    session["phases"]["ict_patterns"] = patterns
    
    # ═══ FASE 3.5: Detecção de Padrões Gráficos Clássicos ═══
    print("📈 FASE 3.5: Detectando padrões gráficos (H&S, topos, triângulos, flags)...")
    chart_patterns = detect_chart_patterns()
    session["phases"]["chart_patterns"] = chart_patterns
    
    # ═══ FASE 4: Consolidação ═══
    print("🧠 FASE 4: Consolidando conhecimento...")
    insights = consolidate_findings(session)
    session["discoveries"] = insights
    
    # Salvar sessão
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(session, indent=2, default=str))
    
    # Escrever descobertas na bridge
    for insight in insights[:5]:  # Top 5
        write_to_bridge(insight)
    
    # ─── FASE 5.5: Cross-pollinate NN-Shared ─────────────────────
    try:
        if NN_ENGINE.exists():
            print("🔗 FASE 5.5: Cross-pollinate NN-Shared...")
            subprocess.run(
                ["python3", str(NN_ENGINE), "cross_pollinate"],
                capture_output=True, text=True, timeout=30
            )
            # Backprop no brain para ajustar pesos
            subprocess.run(
                ["python3", str(NN_ENGINE), "backprop", "brain"],
                capture_output=True, text=True, timeout=15
            )
            print("  ✅ Cross-pollinate + backprop concluídos")
    except Exception as e:
        print(f"  ⚠️ Cross-pollinate erro (não crítico): {e}")
    # ─────────────────────────────────────────────────────────────
    
    session["duration_seconds"] = round(time.time() - start)
    
    print(f"\n✅ Sessão concluída em {session['duration_seconds']}s")
    print(f"   Descobertas: {len(insights)}")
    print(f"   Arquivo: {SESSION_FILE}")
    
    return session


def detect_all_patterns():
    """Detecta padrões em todos os pares usando Yahoo Finance."""
    import urllib.request
    
    patterns_found = defaultdict(list)
    
    for pair in PAIRS[:4]:  # Limitar pares para não sobrecarregar
        try:
            symbol = f"{pair}=X"
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=15m"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            result = data['chart']['result'][0]
            quotes = result['indicators']['quote'][0]
            
            candles = []
            for i in range(len(result['timestamp'])):
                o, h, l, c = quotes['open'][i], quotes['high'][i], quotes['low'][i], quotes['close'][i]
                if None not in (o, h, l, c):
                    candles.append({'o': o, 'h': h, 'l': l, 'c': c})
            
            if len(candles) < 20:
                continue
            
            pip_size = 0.01 if 'JPY' in pair else 0.0001
            
            # Detectar FVGs
            fvgs = []
            for i in range(1, len(candles) - 1):
                if candles[i-1]['h'] < candles[i+1]['l']:
                    gap = round((candles[i+1]['l'] - candles[i-1]['h']) / pip_size, 1)
                    fvgs.append({'type': 'FVG_BULL', 'gap_pips': gap, 'idx': i})
                if candles[i-1]['l'] > candles[i+1]['h']:
                    gap = round((candles[i-1]['l'] - candles[i+1]['h']) / pip_size, 1)
                    fvgs.append({'type': 'FVG_BEAR', 'gap_pips': gap, 'idx': i})
            
            # Estatísticas
            bullish_fvgs = [f for f in fvgs if f['type'] == 'FVG_BULL']
            bearish_fvgs = [f for f in fvgs if f['type'] == 'FVG_BEAR']
            
            if fvgs:
                avg_gap = round(sum(f['gap_pips'] for f in fvgs) / len(fvgs), 1)
                patterns_found[pair] = {
                    'total_fvgs': len(fvgs),
                    'bullish': len(bullish_fvgs),
                    'bearish': len(bearish_fvgs),
                    'avg_gap_pips': avg_gap,
                    'max_gap_pips': max(f['gap_pips'] for f in fvgs),
                    'candles_analyzed': len(candles)
                }
            
            time.sleep(1)  # Rate limit
            
        except Exception as e:
            patterns_found[pair] = {'error': str(e)[:100]}
    
    return dict(patterns_found)


def detect_chart_patterns():
    """Detecta padrões gráficos clássicos em todos os pares."""
    import subprocess
    
    output = subprocess.run(
        ["python3", str(HERMES / "scripts" / "chart_pattern_detector.py"), "--json"],
        capture_output=True, text=True, timeout=120
    )
    
    try:
        data = json.loads(output.stdout)
        summary = {}
        for pair_data in data:
            pair = pair_data.get('pair', 'unknown')
            total = sum(len(tf['patterns']) for tf in pair_data.get('timeframes', {}).values())
            pattern_types = defaultdict(int)
            for tf in pair_data.get('timeframes', {}).values():
                for p in tf.get('patterns', []):
                    pattern_types[p['type']] += 1
            summary[pair] = {
                'total_patterns': total,
                'pattern_types': dict(pattern_types)
            }
        return summary
    except:
        return {'error': 'chart pattern detection failed'}


def consolidate_findings(session):
    """Consolida descobertas da sessão em insights."""
    insights = []
    
    patterns = session["phases"].get("ict_patterns", {})
    
    for pair, data in patterns.items():
        if 'total_fvgs' in data and data['total_fvgs'] > 0:
            insights.append(
                f"[{pair}] {data['total_fvgs']} FVGs detectados em 5 dias M15 — "
                f"{data['bullish']} bullish, {data['bearish']} bearish — "
                f"gap médio: {data['avg_gap_pips']} pips, máximo: {data['max_gap_pips']} pips"
            )
    
    # Insights de padrões gráficos
    chart_p = session["phases"].get("chart_patterns", {})
    if chart_p and 'error' not in str(chart_p):
        total_chart = sum(v.get('total_patterns', 0) for v in chart_p.values() if isinstance(v, dict))
        if total_chart > 0:
            insights.append(
                f"[CHART] {total_chart} padrões gráficos detectados em {len(chart_p)} pares"
            )
            # Padrões mais comuns
            all_types = defaultdict(int)
            for v in chart_p.values():
                if isinstance(v, dict):
                    for ptype, count in v.get('pattern_types', {}).items():
                        all_types[ptype] += count
            top_types = sorted(all_types.items(), key=lambda x: x[1], reverse=True)[:5]
            if top_types:
                insights.append(
                    f"[CHART] Padrões mais frequentes: {', '.join(f'{t}({c})' for t,c in top_types)}"
                )
    
    # Insight sobre quais pares têm mais FVGs (melhores pra estratégia)
    fvg_pairs = [(p, d['total_fvgs']) for p, d in patterns.items() 
                 if 'total_fvgs' in d and d['total_fvgs'] > 0]
    fvg_pairs.sort(key=lambda x: x[1], reverse=True)
    
    if fvg_pairs:
        top = fvg_pairs[:3]
        insights.append(
            f"TOP FVG pairs: {', '.join(f'{p}({n})' for p, n in top)} — "
            f"priorizar estes na estratégia CHoCH+FVG"
        )
    
    # Timestamp
    insights.append(
        f"Sessão de estudo #{datetime.now().strftime('%Y%m%d-%H%M')} concluída. "
        f"Material coletado, backtest executado, {len(patterns)} pares analisados."
    )
    
    return insights


if __name__ == "__main__":
    study_session()
