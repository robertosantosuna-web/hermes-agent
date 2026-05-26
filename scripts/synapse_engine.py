#!/usr/bin/env python3
"""
SYNAPSE ENGINE — Motor de Sinapses da Rede Neural.
Rede neural artificial que cruza descobertas entre TODOS os módulos do cérebro.

Funcionamento:
1. Lê outputs de cada módulo (arquivos de cron, logs, libraries)
2. Detecta correlações entre módulos (ex: qualidade CHoCH → WR do par)
3. Cria sinapses (conexões de conhecimento) na Neural KB
4. Atualiza o estado global (market regime, risk level)
5. Retroalimenta os módulos com insights cruzados

Cada sinapse = um neurônio aprendendo com outro.
Roda diariamente às 07:00 BRT (antes do daily study).
"""
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

HERMES = Path(os.path.expanduser('~/.hermes'))
KB_PATH = HERMES / 'neural_knowledge_base.json'
CRON_OUT = HERMES / 'cron' / 'output'
SYNAPSE_LOG = HERMES / 'synapse_engine_log.jsonl'

def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except:
        return None

def load_kb():
    if not KB_PATH.exists():
        return None
    try:
        return json.loads(KB_PATH.read_text())
    except:
        return None

def save_kb(kb):
    KB_PATH.write_text(json.dumps(kb, indent=2))

def log_synapse(entry):
    """Append to synapse engine log."""
    with open(SYNAPSE_LOG, 'a') as f:
        f.write(json.dumps(entry, default=str) + '\n')

# ═══════════════════════════════════════════════════════════════
# COLETA DE DADOS DE TODOS OS MÓDULOS
# ═══════════════════════════════════════════════════════════════

def collect_amygdala_data():
    """Collect threat data from Amygdala outputs."""
    amy_dir = CRON_OUT / 'amygdala'
    if not amy_dir.exists():
        return None
    
    files = sorted(amy_dir.glob('threats_*.json'), reverse=True)
    if not files:
        return None
    
    try:
        data = json.loads(files[0].read_text())
        return {
            'threat_count': data.get('threats_detected', 0),
            'action': data.get('action', 'LOG_ONLY'),
            'threats': data.get('threats', []),
            'last_scan': data.get('timestamp'),
        }
    except:
        return None

def collect_accumbens_data():
    """Collect learning data from N. Accumbens."""
    weights_file = HERMES / 'forex' / 'pair_weights_live.json'
    state_file = HERMES / 'forex' / 'accumbens_state.json'
    
    weights = load_json(weights_file)
    state = load_json(state_file)
    
    return {
        'pair_weights': weights.get('pairs', {}) if weights else {},
        'total_trades': weights.get('total_trades', 0) if weights else 0,
        'last_learning': weights.get('updated') if weights else None,
        'changes': state.get('changes', []) if state else [],
    }

def collect_chart_pattern_data():
    """Collect pattern data from Chart Pattern Study."""
    pattern_lib = load_json(HERMES / 'forex' / 'patterns' / 'pattern_library.json')
    patterns_dir = HERMES / 'forex' / 'patterns'
    
    # Find latest daily report
    reports = sorted(patterns_dir.glob('*/*/pattern_report.json'), reverse=True)
    
    patterns_summary = {}
    if pattern_lib:
        for ptype, data in pattern_lib.items():
            patterns_summary[ptype] = {
                'total': data.get('total_collected', 0),
                'examples': len(data.get('examples', [])),
            }
    
    latest_report = None
    if reports:
        try:
            latest_report = json.loads(reports[0].read_text())
        except:
            pass
    
    return {
        'library': patterns_summary,
        'latest_report': latest_report,
        'total_patterns': sum(p['total'] for p in patterns_summary.values()),
    }

def collect_hippocampus_data():
    """Collect consolidation data from Hippocampus."""
    patterns_file = HERMES / 'hippocampus_patterns.json'
    hippo_dir = CRON_OUT / 'hippocampus'
    
    patterns = load_json(patterns_file)
    
    return {
        'trade_patterns': patterns.get('trade_patterns') if patterns else None,
        'failure_patterns': patterns.get('failure_patterns') if patterns else None,
        'evolution_status': patterns.get('evolution_status') if patterns else None,
        'last_consolidation': patterns.get('timestamp') if patterns else None,
    }

def collect_cerebellum_data():
    """Collect validation data from Cerebellum."""
    state_file = HERMES / 'cerebellum_state.json'
    cereb_dir = CRON_OUT / 'cerebellum'
    
    state = load_json(state_file)
    failures = []
    
    if cereb_dir.exists():
        for f in sorted(cereb_dir.glob('validate_*.json'), reverse=True)[:3]:
            try:
                data = json.loads(f.read_text())
                failures.extend(data.get('failures', []))
            except:
                pass
    
    return {
        'last_validation': state.get('last_run') if state else None,
        'recent_failures': failures[-5:],
        'module_health': {},
    }

def collect_research_data():
    """Collect research data from Research Collector."""
    research_dir = HERMES / 'forex' / 'research'
    
    days = sorted(research_dir.glob('20*'), reverse=True)
    articles_count = 0
    topics = set()
    
    for day_dir in days[:7]:  # Last 7 days
        summary = load_json(day_dir / '_summary.json')
        if summary:
            articles_count += summary.get('total_collected', 0)
            for item in summary.get('items', []):
                topics.add(item.get('source', ''))
    
    return {
        'articles_7d': articles_count,
        'sources_active': list(topics),
        'last_collection': days[0].name if days else None,
    }

def collect_weekly_insights():
    """Collect insights from Weekly Analyzer."""
    analyzer_dir = CRON_OUT / '89158ec43168'
    
    if not analyzer_dir.exists():
        return None
    
    files = sorted(analyzer_dir.glob('*.md'), reverse=True)
    if not files:
        return None
    
    content = files[0].read_text()
    
    # Extract key sections
    insights = {
        'patterns_section': '',
        'performance_section': '',
        'alerts': [],
    }
    
    # Simple extraction
    for line in content.split('\n'):
        if '🔍' in line or 'PADRÕES' in line:
            insights['patterns_section'] += line + '\n'
        elif '📈' in line or 'PERFORMANCE' in line:
            insights['performance_section'] += line + '\n'
        elif '⚠️' in line or 'ALERTA' in line:
            insights['alerts'].append(line.strip())
    
    return insights

# ═══════════════════════════════════════════════════════════════
# CRUZAMENTO DE DADOS — CRIAÇÃO DE SINAPSES
# ═══════════════════════════════════════════════════════════════

def cross_pattern_performance(patterns, accumbens):
    """Cross chart patterns with trade performance."""
    synapses = []
    
    pattern_lib = patterns.get('library', {})
    pair_weights = accumbens.get('pair_weights', {})
    
    # Check if CHoCH quality correlates with WR
    choch_data = pattern_lib.get('choch', {})
    structure_data = pattern_lib.get('structure_breaks', {})
    
    for pair, weights in pair_weights.items():
        wr = weights.get('wr', 0)
        rec = weights.get('recommendation', '')
        
        # Synapse: pattern quality → performance
        if rec in ('PRIORITY', 'ACTIVE') and wr >= 55:
            synapses.append({
                'from': 'chart_patterns',
                'to': 'n_accumbens',
                'insight': f'Pair {pair} with WR={wr}% ({rec}) — validate if pattern quality is high',
                'confidence': min(0.9, wr / 100),
                'evidence': {'pair': pair, 'wr': wr, 'recommendation': rec},
            })
        
        # Synapse: low WR → check patterns
        if rec == 'PAUSE' and wr < 45:
            synapses.append({
                'from': 'n_accumbens',
                'to': 'chart_patterns',
                'insight': f'Pair {pair} with low WR ({wr}%) — focus pattern study on this pair',
                'confidence': 0.7,
                'evidence': {'pair': pair, 'wr': wr, 'issue': 'low_performance'},
            })
    
    return synapses

def cross_threats_risk(amygdala, cerebellum):
    """Cross threat detection with system health."""
    synapses = []
    
    threats = amygdala.get('threat_count', 0) if amygdala else 0
    failures = len(cerebellum.get('recent_failures', [])) if cerebellum else 0
    
    if threats > 0 and failures > 0:
        synapses.append({
            'from': 'amygdala',
            'to': 'cerebellum',
            'insight': f'{threats} threats + {failures} validation failures — system under stress',
            'confidence': 0.8,
            'evidence': {'threats': threats, 'failures': failures},
        })
    
    # Synapse: threats → risk level
    if threats >= 3:
        synapses.append({
            'from': 'amygdala',
            'to': 'global_state',
            'insight': f'Risk elevated: {threats} active threats',
            'confidence': 0.85,
            'evidence': {'threat_count': threats},
        })
    
    return synapses

def cross_research_strategy(research, hippocampus):
    """Cross research findings with trading patterns."""
    synapses = []
    
    articles = research.get('articles_7d', 0) if research else 0
    trade_patterns = hippocampus.get('trade_patterns') if hippocampus else None
    
    if articles >= 10 and trade_patterns:
        synapses.append({
            'from': 'research_collector',
            'to': 'hippocampus',
            'insight': f'{articles} research articles available — correlate with trade pattern analysis',
            'confidence': 0.6,
            'evidence': {'articles': articles},
        })
    
    return synapses

def cross_evolution_health(brain_research_data, cerebellum):
    """Cross brain evolution gaps with system health."""
    synapses = []
    
    # Check if any gaps correlate with validation failures
    failures = cerebellum.get('recent_failures', []) if cerebellum else []
    
    if failures:
        failed_modules = set(f.get('module', '') for f in failures)
        synapses.append({
            'from': 'cerebellum',
            'to': 'brain_research',
            'insight': f'Modules with validation failures: {failed_modules} — prioritize fixes',
            'confidence': 0.9,
            'evidence': {'failed_modules': list(failed_modules)},
        })
    
    return synapses

def detect_market_regime(accumbens, patterns):
    """Detect current market regime from multiple signals."""
    weights = accumbens.get('pair_weights', {})
    pattern_data = patterns.get('library', {})
    
    # Simple regime detection
    active_pairs = sum(1 for w in weights.values() if w.get('recommendation') in ('PRIORITY', 'ACTIVE'))
    total_pairs = len(weights)
    
    if total_pairs == 0:
        return 'unknown', 0.0
    
    active_ratio = active_pairs / total_pairs
    
    if active_ratio >= 0.6:
        regime = 'trending'
        confidence = min(0.9, active_ratio)
    elif active_ratio >= 0.3:
        regime = 'ranging'
        confidence = 0.6
    else:
        regime = 'choppy'
        confidence = 0.7
    
    # Check for high CHoCH count (regime change signal)
    choch_data = pattern_data.get('choch', {})
    if choch_data.get('total', 0) > 50:
        if regime == 'trending':
            regime = 'transitioning'
            confidence = 0.5
    
    return regime, confidence

# ═══════════════════════════════════════════════════════════════
# MAIN CONSOLIDATION CYCLE
# ═══════════════════════════════════════════════════════════════

def consolidate():
    """Run full neural consolidation cycle."""
    now = datetime.now(timezone.utc)
    
    print(f"🧠 SYNAPSE ENGINE — Neural Consolidation")
    print(f"   {now.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print()
    
    # 1. Collect data from all modules
    print("▶ Coletando dados de todos os módulos...")
    
    amygdala = collect_amygdala_data()
    print(f"  Amygdala: {'✓' if amygdala else '✗'}")
    
    accumbens = collect_accumbens_data()
    print(f"  N.Accumbens: {'✓' if accumbens.get('pair_weights') else '✗'} ({accumbens.get('total_trades', 0)} trades)")
    
    patterns = collect_chart_pattern_data()
    print(f"  Chart Patterns: {'✓' if patterns.get('library') else '✗'} ({patterns.get('total_patterns', 0)} total)")
    
    hippocampus = collect_hippocampus_data()
    print(f"  Hippocampus: {'✓' if hippocampus.get('trade_patterns') else '✗'}")
    
    cerebellum = collect_cerebellum_data()
    print(f"  Cerebellum: {'✓' if cerebellum else '✗'}")
    
    research = collect_research_data()
    print(f"  Research: {'✓' if research else '✗'} ({research.get('articles_7d', 0)} articles/7d)")
    
    weekly = collect_weekly_insights()
    print(f"  Weekly Analyzer: {'✓' if weekly else '✗'}")
    
    # 2. Cross-reference — create synapses
    print("\n▶ Criando sinapses...")
    
    all_synapses = []
    
    # Pattern ↔ Performance
    s1 = cross_pattern_performance(patterns, accumbens)
    all_synapses.extend(s1)
    print(f"  Pattern→Performance: {len(s1)} sinapses")
    
    # Threats ↔ Risk
    s2 = cross_threats_risk(amygdala, cerebellum)
    all_synapses.extend(s2)
    print(f"  Threats→Risk: {len(s2)} sinapses")
    
    # Research ↔ Strategy
    s3 = cross_research_strategy(research, hippocampus)
    all_synapses.extend(s3)
    print(f"  Research→Strategy: {len(s3)} sinapses")
    
    # Evolution ↔ Health
    s4 = cross_evolution_health(None, cerebellum)
    all_synapses.extend(s4)
    print(f"  Evolution→Health: {len(s4)} sinapses")
    
    # 3. Detect market regime
    regime, confidence = detect_market_regime(accumbens, patterns)
    print(f"\n▶ Market Regime: {regime} (confidence: {confidence:.0%})")
    
    # 4. Load KB and apply
    kb = load_kb()
    if kb is None:
        from neural_kb import init_kb
        kb = init_kb()
    
    # Update module data in KB
    if amygdala:
        kb['modules']['amygdala'].update({
            'active_threats': amygdala.get('threats', []),
            'threat_level': 'elevated' if amygdala.get('threat_count', 0) >= 3 else 'normal',
            'last_scan': amygdala.get('last_scan'),
        })
    
    if accumbens.get('pair_weights'):
        kb['modules']['n_accumbens'].update({
            'pair_weights': accumbens['pair_weights'],
            'learning_observations': accumbens.get('changes', []),
            'last_learning': accumbens.get('last_learning'),
        })
    
    if patterns.get('latest_report'):
        report = patterns['latest_report']
        kb['modules']['chart_patterns'].update({
            'dominant_patterns': [
                {'type': k, 'count': v}
                for k, v in report.get('by_type', {}).items()
            ],
            'last_scan': report.get('date'),
        })
    
    if hippocampus.get('trade_patterns'):
        tp = hippocampus['trade_patterns']
        kb['modules']['hippocampus'].update({
            'trade_behavior_patterns': {
                'total_trades': tp.get('total'),
                'wr': tp.get('wins', 0) / max(tp.get('total', 1), 1) * 100,
                'avg_pnl_win': tp.get('avg_pnl_win'),
                'avg_pnl_loss': tp.get('avg_pnl_loss'),
            },
            'failure_heatmap': hippocampus.get('failure_patterns', {}).get('by_category', {}),
            'last_consolidation': hippocampus.get('last_consolidation'),
        })
    
    if cerebellum:
        kb['modules']['cerebellum'].update({
            'validation_failures': cerebellum.get('recent_failures', []),
            'last_validation': cerebellum.get('last_validation'),
        })
    
    if research:
        kb['modules']['research_collector'].update({
            'sources_collected': research.get('articles_7d', 0),
            'last_collection': research.get('last_collection'),
        })
    
    # Add synapses to KB
    for syn in all_synapses:
        syn['id'] = f"syn-{kb['_meta']['total_synapses'] + 1:04d}"
        syn['timestamp'] = now.isoformat()
        syn['applied'] = False
        kb['synapses'].append(syn)
        kb['_meta']['total_synapses'] += 1
    
    # Update global state
    kb['global_state'].update({
        'market_regime': regime,
        'market_regime_confidence': round(confidence, 2),
        'risk_level': 'elevated' if len(all_synapses) >= 5 else 'normal',
        'active_modules': sum(1 for v in [amygdala, accumbens.get('pair_weights'), patterns.get('library'), hippocampus, cerebellum, research] if v),
        'last_updated': now.isoformat(),
    })
    
    kb['_meta']['last_consolidation'] = now.isoformat()
    
    # Keep synapses manageable
    if len(kb['synapses']) > 200:
        kb['synapses'] = kb['synapses'][-200:]
    
    save_kb(kb)
    
    # Log
    log_entry = {
        'timestamp': now.isoformat(),
        'synapses_created': len(all_synapses),
        'total_synapses': kb['_meta']['total_synapses'],
        'market_regime': regime,
        'regime_confidence': confidence,
        'modules_active': kb['global_state']['active_modules'],
    }
    log_synapse(log_entry)
    
    # Summary
    print(f"\n✅ Consolidação completa:")
    print(f"   Sinapses criadas: {len(all_synapses)}")
    print(f"   Total na rede: {kb['_meta']['total_synapses']}")
    print(f"   Market regime: {regime} ({confidence:.0%})")
    print(f"   Módulos ativos: {kb['global_state']['active_modules']}/7")
    
    return log_entry

if __name__ == '__main__':
    consolidate()
