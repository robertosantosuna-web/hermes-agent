# Brain Pipeline Map — Aprendizado Contínuo do Cérebro

> **Regra #0:** Todo módulo do cérebro DEVE consultar este mapa antes de executar sua rotina.
> **Regra #1:** Se um padrão falhou 2x consecutivas, NÃO repetir — marcar como STALE e pesquisar alternativa.
> **Regra #2:** Toda descoberta de falha ou solução DEVE ser escrita no knowledge_bridge.

---

## MAPA DE ABORDAGENS DO CÉREBRO

### 📡 Forex Research Collector (diário 03:00)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| YouTube transcripts sem API key | yt-dlp ou transcript API com header User-Agent real |
| RSS sem feedparser no venv | `PYTHONPATH=$HOME/.local/lib/python3.14/site-packages` |
| Web scraping de sites com Cloudflare (BabyPips, Investopedia) | Fontes sem Cloudflare: innercircletrader.net, atas.net, wyckoffanalytics.com |
| Pesquisar sempre as mesmas fontes | Rodar `research_sources.json` atualizado com fontes avançadas |
| Ignorar falhas silenciosamente | Reportar `error` no study_log.jsonl |

**Pitfall conhecido:** O collector rodou 24/05 com 0 YouTube transcripts e falhou no feedparser.  
**Correção:** `PYTHONPATH` fix + fontes atualizadas em `research_sources.json` (adicionado 24/05).

### 📊 Brain Signal Generator (*/2 fds, */15 semana)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Gerar sinais com mercado fechado | Detectar `market_open = False` e pular scan |
| Yahoo Finance como fonte primária | TradingView (dados mais precisos) |
| Ignorar `signals_pending.json` vazio | Escrever `total_pending: 0` com timestamp |
| Não reportar ausência de sinais | Silêncio = OK (watchdog pattern) |

**Estado:** 24/05 12:22 — 0 sinais (mercado fechado, esperado). Correto.

### 📈 Chart Pattern Study (diário 08:00 seg-sex)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| **Estudar estratégia ATR genérica** (WR 17-36%, preso desde 19/05) | **Estudar estratégia V4** (FVG + gap≥5 + horas[6,7,15,16]) |
| Backtest sem filtros (baseline 48% WR) | Backtest COM filtros V4 (gap + horas + CRT) |
| Ignorar pares inviáveis (AUDUSD, NZDUSD) | Focar USDJPY (#1), GBPUSD (#2), EURUSD (#3) |
| Não comparar com backtest anterior | Comparar evolução WR/PF entre ciclos |

**🚨 CRÍTICO:** O study_log.jsonl mostra a MESMA estratégia ATR desde 19/05/2026. O cérebro está preso em loop.  
**Correção:** Redirecionar para V4 imediatamente. O `best_params.json` é lixo (AUDUSD com ATR).

### 🧠 Parameter Backtest

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Testar ATR com AUDUSD (melhor "35.9% WR") | Testar FVG V4 com USDJPY (73.3% WR) |
| Usar `best_params.json` de 19/05 | Rodar `fvg_simulation.py` e aplicar filtros V4 |
| Não ler o knowledge_bridge antes de testar | `absorb brain` antes de cada ciclo |
| RR 2.0-3.5 genérico | RR 3:1 fixo (validado por 5059 padrões) |

### 🔗 Knowledge Bridge

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Escrever descobertas sem `absorb` | Escrever → rodar `absorb` para o outro lado |
| Dados repetitivos (FVG counts a cada 2h) | Só escrever se delta > 5% ou descoberta NOVA |
| Ignorar o bridge nos módulos | Todo módulo deve `read` antes e `write` depois |
| Não usar `absorb` | `absorb agent` após cada ciclo de estudo |

**Pitfall:** 24/05 — 46 descobertas do brain, 99% eram FVG counts repetidos.  
**Correção:** Só escrever insights com novidade (delta significativo ou nova correlação).

### 🧬 Neural KB + Synapse Engine

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Sinapses com `source: null, target: null` | Validar source/target antes de criar sinapse |
| Módulos com `last_modified: ?` | Todo módulo deve escrever timestamp ISO ao rodar |
| Não detectar market regime | `kb_bridge.query('market_regime')` a cada ciclo |
| Sinapses sem `confidence` | Exigir confidence ≥ 0.6 para criar sinapse |

### 🛡️ Amygdala (threat detector)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Manter threats velhos (23/05 "disk full") | Expirar threats > 48h sem re-ocorrência |
| WAKE_CORTEX com zero ameaças reais | Só WAKE se `threat_level != normal` E `threats frescos` |
| Não verificar saúde dos módulos | Checar `cerebellum.last_validation` antes de alertar |

### 🔍 Cerebellum (action validator)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Só validar quando há erro | Escrever `modules_checked` mesmo sem falhas |
| `last_validation` stale (23/05) | Validar a cada ciclo (*/5 min) |
| Não detectar loops (study_log repetido) | Detectar padrão repetido ≥ 3x = ALERTA |

### 🧪 Brain Research (auto-dev cycle)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Rodar sem ler o knowledge_bridge | `absorb brain` antes de iniciar pesquisa |
| Pesquisar fontes antigas/estáticas | Usar `research_sources.json` atualizado (v2 24/05) |
| Não reportar descobertas | Escrever no bridge com `category: brain_research` |

---

## HEURÍSTICA DO CÉREBRO

### Hierarquia de ferramentas (igual ao córtex)

```
kernel-level (ydotool) > CDP leitura > Terminal/curl > Web scraping > NADA (reportar)
```

### Anti-padrões do cérebro

1. ❌ Estudar estratégia que já falhou (ATR desde 19/05)
2. ❌ Escrever dados repetitivos no bridge (FVG counts sem delta)
3. ❌ Criar sinapses sem source/target válidos
4. ❌ Manter estado stale (threats velhos, validações antigas)
5. ❌ Rodar módulo sem `absorb` antes
6. ❌ Usar `best_params.json` como verdade (é lixo de ATR)
7. ❌ Ignorar `research_sources.json` atualizado
8. ❌ Gerar sinais com mercado fechado sem verificar
9. ❌ Não reportar falhas (erro silencioso)
10. ❌ Rodar YouTube transcripts sem API key/config correta

---

## CICLO DE AUTO-CORREÇÃO

```
1. Módulo inicia → ver task-pipeline-map (córtex) + brain-pipeline-map (cérebro)
2. Detecta abordagem que já falhou? → PULAR, usar alternativa mapeada
3. Abordagem nova falhou 2x? → Mapear falha, pesquisar solução, ATUALIZAR este arquivo
4. Escrever descoberta no knowledge_bridge → absorb
5. Cerebellum detecta loop (≥3x mesma falha) → ALERTA → Brain Research investiga
```

---

## REGISTRO DE ATUALIZAÇÕES

| Data | Módulo | Falha | Solução |
|------|--------|-------|---------|
| 24/05 | Research Collector | feedparser não instalado no venv | PYTHONPATH override |
| 24/05 | Research Collector | 0 YouTube transcripts | Fontes atualizadas em research_sources.json v2 |
| 24/05 | Chart Pattern Study | Loop ATR desde 19/05 | Redirecionar para FVG V4 |
| 24/05 | Parameter Backtest | best_params.json é ATR lixo | Rodar fvg_simulation.py com filtros V4 |
| 24/05 | Knowledge Bridge | 46 descobertas 99% repetidas | Só escrever se delta > 5% |
| 24/05 | Neural KB | Sinapses sem source/target | Validar antes de criar |
| 24/05 | Amygdala | Threats velhos (23/05) | Expirar > 48h |
| 24/05 | Brain Research | Fontes genéricas/estáticas | Adicionar 135+ fontes avançadas (24/05) |
