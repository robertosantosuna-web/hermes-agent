# Cron Error Triage — v2.6 (2026-05-27)

Procedimento de triagem quando múltiplos cron jobs começam a falhar simultaneamente.
A ordem é crítica — cada nível afeta um conjunto diferente de jobs.

## Nível 1: API Credits (maior raio de impacto)

**Sintoma:** Vários jobs com `RuntimeError: Error code: 402 - Insufficient Balance`
**Jobs afetados:** TODOS os cron jobs que usam LLM (não-no_agent): System Health Check,
MindCoach Checkpoint, Gateway Health Watchdog, Mental Morning/Evening, Motor Escalação,
Codex Forex Monitor, Freelance Scanner, Killzone Analysis, London/NY Open.

**Verificação rápida:**
```bash
grep -rl "402\|Insufficient Balance" ~/.hermes/cron/output/*/$(date +%Y-%m-%d)*.md 2>/dev/null | wc -l
```

**Causa:** DeepSeek/OpenRouter sem créditos. Afeta QUALQUER job que chama o modelo LLM.

**Ação:** Recarregar créditos ou migrar jobs afetados para Ollama local (zero custo).
Jobs `no_agent` NÃO são afetados — continuam funcionando normalmente.

## Nível 2: CDP Ports (raio médio de impacto)

**Sintoma:** `{'error': 'no output'}` em todos os pares no brain_signal_generator.py,
ou erros de conexão no brain_browser.py.

**Jobs afetados:** brain_signal_generator, tv_chart_scanner, brain_study_tradingview,
brain_calendar_monitor (modo CDP), e qualquer script que use brain_browser.py.

**Verificação rápida:**
```bash
# Porta headless (padrão dos scripts do cérebro)
curl -s --max-time 3 http://localhost:9223/json/version && echo "OK" || echo "OFFLINE"

# Porta real (Brave desktop, mais estável)
curl -s --max-time 3 http://localhost:9222/json/version && echo "OK" || echo "OFFLINE"
```

**Padrão conhecido:** A porta :9223 (Brave headless) cai com frequência — o processo pode ser
morto por OOM ou crash do browser. A porta :9222 (Brave desktop real) é mais estável porque
o usuário mantém o browser aberto.

**Ações (em ordem):**
1. Trocar brain_browser.py para usar :9222 em vez de :9223 (ou aceitar ambos com fallback)
2. Reiniciar Brave headless: `systemctl --user restart hermes-brain-browser`
3. Fallback: usar yfinance ou dados offline em vez de CDP para preços

## Nível 3: Per-script Bugs (raio baixo de impacto)

**Sintoma:** `Traceback (most recent call last)` em jobs específicos.

**Verificação rápida:**
```bash
# Listar jobs com traceback nas últimas 12h
find ~/.hermes/cron/output/ -name "*.md" -mmin -720 \
  -exec grep -l "Traceback" {} \; | sed 's|.*/output/||;s|/.*||' | sort -u
```

**Bug conhecido — monitor_consumer.py (27/05/2026):**
`AttributeError: 'list' object has no attribute 'get'` na linha 39.
Causa: `alerts.json` é um array JSON `[{...}]`, mas o código esperava `{"alerts": [{...}]}`.
Correção: verificar `isinstance(alerts, list)` antes de chamar `.get('alerts')`.

**Bug conhecido — Codex Backtests + Yahoo Finance (27/05/2026):**
`Could not resolve host: guce.yahoo.com` — Yahoo Finance anti-bot DNS.
Causa: `yfinance` tentando resolver domínio de verificação do Yahoo (guce.yahoo.com).
Se temporário: aguardar. Se persistente: trocar fonte de dados (MT5 direto, OANDA API).

## Fluxograma de Triagem

```
Múltiplos cron jobs falhando?
  │
  ├─ grep "402" nos outputs → SIM → 🔴 Nível 1: API sem créditos
  │   └─ Recarregar ou migrar jobs LLM → Ollama
  │
  ├─ grep "no output" + todos pares → SIM → 🟡 Nível 2: CDP port offline
  │   └─ curl :9223 → trocar porta ou reiniciar headless
  │
  └─ grep "Traceback" → SIM → 🟢 Nível 3: Bug individual
      └─ Abrir script, corrigir, testar
```
