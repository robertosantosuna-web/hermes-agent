---
name: task-pipeline-map
description: "Mapeamento universal de abordagens: o que funciona, o que falha, e o pipeline correto para cada tipo de tarefa. Sistema de aprendizado contínuo — atualizado a cada erro descoberto."
version: 1.0.0
---

# Task Pipeline Map — Aprendizado Contínuo

> **Regra #0:** Antes de qualquer tarefa, CONSULTAR este mapa. Se o cenário não está mapeado, aplicar a heurística. Se falhar, ATUALIZAR o mapa IMEDIATAMENTE.
> **Regra #1:** NUNCA repetir abordagem que já falhou para o mesmo tipo de cenário.

---

## MAPA DE ABORDAGENS POR CENÁRIO

### 🌐 Sites com Cloudflare/PerimeterX/Turnstile

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| CDP headless (detectado como bot) | Desktop Daemon + ydotool no Brave real |
| Playwright headless | Navegador Wayland real (porta 9222) |
| Qualquer automação via navegador headless | Mouse/teclado kernel-level (ydotool) |

**Sites afetados:** 99Freelas, BabyPips, Investopedia
**Skill:** `99freelas-automation`
**Refinamento (24/05):** CDP no Brave REAL (porta 9222) funciona para LEITURA de DOM e extração de texto em sites Cloudflare — desde que o navegador já esteja logado e com sessão ativa. Headless (9223) é bloqueado.

### ⚛️ Sites React/SPA com controlled components

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| `Input.insertText` (CDP) | ydotool `type` (kernel-level) |
| `Input.dispatchKeyEvent` (CDP) | ydotool `key` |
| `textarea.value = "..."` + dispatchEvent | ydotool `click` no botão real |
| `navigator.clipboard.writeText` | — |
| React fiber state manipulation | — |

**Sites afetados:** 99Freelas, TradingView, maioria das SPAs modernas
**Skill:** `99freelas-automation`

### 📊 TradingView / Charts

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Yahoo Finance (dados atrasados/imprecisos) | TradingView CDP (porta 9222, sessão logada) |
| Web scraping de charts renderizados | Pine Script + Bar Replay |
| — | Brain browser CDP (porta 9223) para telas sem Cloudflare |

**Skill:** `forex-choch-m15` → references/tradingview-integration.md

### 📧 Email / IMAP

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| himalaya CLI (TOML quebrado entre versões) | imaplib + smtplib nativos (Python stdlib) |
| Senha normal Gmail | App Password (16 chars) |
| Labels Gmail sem aspas (`[Gmail]/All Mail`) | Com aspas duplas (`"[Gmail]/All Mail"`) |

**Skill:** `email-autonomy`

### 🖥️ Desktop / Wayland

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| xdotool no Wayland | ydotool + ydotoold |
| `windowactivate` no Xvfb sem WM | `windowfocus` + enviar teclas |
| Screenshot via D-Bus (instável) | mss (com DISPLAY=:0 + XAUTHORITY) |
| OCR do MT5 para números | xdotool Ctrl+C no Trade Terminal |

**Skill:** `desktop-control`

### 📈 Forex Trading

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| BOS como entrada (0-12% WR M15) | FVG com gap≥5 + horas [6,7,15,16] |
| CHoCH standalone M15 (7 sinais/60d) | CRT como filtro confirmacional |
| AUDUSD/NZDUSD para FVG (45%/44% WR) | USDJPY (73%), GBPUSD (65%), EURUSD (56%) |
| FVG sem filtro de gap (48%) | gap≥5 pips (+11pp WR boost) |
| H1 Trend como filtro excludente (reduz WR) | H1 apenas como viés direcional (score) |
| MT5 OANDA (0/0Kb tráfego) | IC Markets Demo (display:0) |
| `forex_bot_real.py` com WR hardcoded do backtest | `get_real_wr()` do `trade_log.json` |

**Skill:** `forex-choch-m15`

### 🤖 Freelancing

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| CDP para input no 99Freelas (React) | Desktop Daemon + ydotool |
| Mencionar valor/prazo em propostas | Proposta qualitativa, sem números |
| Tentar logar no 99Freelas sem sessão | Brave Wayland já logado (porta 9222) |

**Skill:** `99freelas-automation`, `proposta-99freelas`

---

## HEURÍSTICA GERAL

Quando enfrentar um cenário NOVO não mapeado:

1. **Classificar o tipo de barreira:**
   - Anti-bot (Cloudflare, Turnstile, PerimeterX)?
   - React/SPA (controlled components)?
   - Auth/OAuth?
   - API rate limit?
   - Keyboard layout (ABNT2)?

2. **Aplicar a hierarquia de ferramentas:**
   ```
   Kernel-level (ydotool) > CDP leitura > Terminal/curl > Web scraping > NADA (ação humana)
   ```

3. **Se falhar, NÃO repetir a mesma abordagem.** Mapear a falha e subir um nível na hierarquia.

4. **Atualizar ESTE mapa** com o novo cenário.

---

## ANTI-PADRÕES UNIVERSAIS

1. ❌ Tentar CDP para input em React/SPA → perda de tokens garantida
2. ❌ Headless browser em site com Cloudflare → bloqueio instantâneo
3. ❌ Repetir abordagem que já falhou → definição de insanidade
4. ❌ Setar `value` no DOM em vez de usar input kernel-level
5. ❌ Usar `windowactivate` em Xvfb sem window manager
6. ❌ OCR para números financeiros no MT5 (illegível)
7. ❌ Yahoo Finance como fonte primária (dados imprecisos)
8. ❌ `feedparser` sem instalar no venv (cron jobs falham)
9. ❌ Clipboard API sem user gesture real
10. ❌ Instalar ferramenta sem verificar compatibilidade Python/VRAM/deps antes (custo: +10 tentativas falhas)
11. ❌ Forçar instalação de RVC em Python 3.11 (requer 3.10) — sempre usar venv Python compatível
12. ❌ CDP headless (9223) em site Cloudflare para qualquer operação — só CDP real (9222) para leitura

---

## REGRA ANTI-DESPERDÍCIO 🔥

**Antes de instalar QUALQUER ferramenta:**
1. Verificar versão Python compatível (`python_requires` no PyPI/GitHub)
2. Verificar VRAM/RAM disponível vs requisitos
3. Verificar conflitos de dependência conhecidos
4. Se inviável, PULAR e sugerir alternativa compatível

**NUNCA:**
- Tentar forçar instalação com `--break-system-packages` sem check prévio
- Gastar +3 tentativas corrigindo dependências em cascata
- Instalar em Python do sistema se o venv tem versão diferente

---

### 🔄 Forex AutoPilot — Ciclo de Morte (27/05)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| AutoPilot com balance hardcoded ($400) | Ler balance real do MT5 via bridge |
| Drawdown threshold 3% ($12) | 15% mínimo + cooldown 30min |
| Sem limite diário de trades | MAX_DAILY_TRADES=20 |
| Fechar tudo e reabrir sem cooldown | Cooldown file após close_all |

**Skill:** `forex-choch-m15` → references/v8.2-autopilot-cycle-of-death.md

### 🧠 Ollama — Context Window (27/05)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| qwen2.5:3b (32K ctx) em cron jobs Hermes | llama3.2:3b (128K ctx) ou phi3:mini (128K) |
| Modelos < 64K em providers config | Verificar `ollama show <model>` antes de configurar |

### 🌐 CDP Browser Port (27/05)

| ❌ NÃO funciona | ✅ FUNCIONA |
|-----------------|-------------|
| Porta :9223 (headless) offline sem systemd | Porta :9222 (Brave real, sempre ativo) |
| CDP /json/navigate para SPAs | Page.navigate via WebSocket |

## REGISTRO DE ATUALIZAÇÕES

| Data | Cenário | Falha | Solução |
|------|---------|-------|---------|
| 27/05 | AutoPilot fecha tudo em loop | DD 3% + balance $400 fixo | DD 15% + balance real + cooldown 30min |
| 27/05 | 154 trades/dia | Sem limite diário | MAX_DAILY_TRADES=20 |
| 27/05 | monitor_consumer crash | `list.get()` em vez de dict | isinstance check |
| 27/05 | brain_browser offline | Porta :9223 headless down | Migrar para :9222 (Brave real) |
| 27/05 | Ollama 32K rejeitado | qwen2.5:3b < 64K mínimo | llama3.2:3b (128K) |
| 24/05 | Instalação RVC | Python 3.11 incompatível (requer 3.10) | Usar Coqui TTS XTSS v2 (compatível 3.11) |
| 24/05 | Instalação Coqui TTS | transformers 5.9.0 quebrou | Pin transformers==4.36.2 |
| 24/05 | Instalação Coqui TTS | torch.load weights_only PyTorch 2.6 | Patch io.py weights_only=False |
| 24/05 | 99Freelas React input | 14 tentativas CDP falharam | ydotool type kernel-level |
| 24/05 | Coordenadas erradas | mss reporta 3840, real 1920 | window.screenX/Y + getBoundingClientRect |
| 24/05 | ABNT2 corrompe acentos | ydotool type com ç/ã | Mensagens ASCII puro |
| 22/05 | MT5 OANDA offline | 0/0Kb tráfego | IC Markets Demo display:0 |
| 21/05 | Bot com WR hardcoded | Usava backtest_wr em vez de real_wr | get_real_wr() do trade_log |
| 20/05 | FVG index bug | df.iloc[j] em slice errado | df30.iloc[j] nas últimas 30 velas |
