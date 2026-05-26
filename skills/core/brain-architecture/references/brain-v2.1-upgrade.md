# Cérebro v2.1 — Absorção de Claude Code + Ruff/LSP

**Data:** 23/05/2026
**Versão do Hermes:** v0.14.0

## O que foi absorvido

### 1. Do Claude Code → Segurança de Comandos

| Componente | Upgrade | Descrição |
|-----------|---------|-----------|
| Cerebelo | v2.1 | 13 padrões de comando perigoso detectados |
| Thalamus | v2.1 | Filtro `filter_error_sanitization` — 7 padrões de injection |
| Self-Correction | AP-11 | Anti-padrão: executar comandos perigosos sem detecção |

### 2. Do Ruff/LSP → Validação Semântica de Código

| Componente | Upgrade | Descrição |
|-----------|---------|-----------|
| Brain Code Validator | NOVO | Validação AST-level de todos os scripts do cérebro |
| Self-Correction | AP-12 | Anti-padrão: gerar código sem validação |

### 3. Navegador Interno + TradingView (23/05)

| Componente | Upgrade | Descrição |
|-----------|---------|-----------|
| Brain Browser | NOVO | Brave CDP headless porta 9223, systemd, controller Python |
| TV Chart Analyzer | NOVO | Bar Replay, screenshots, pattern detection no TradingView |
| TV Session Restore | NOVO | Persistência de cookies Google OAuth entre reboots |

### 4. Cross-Agent Simulation (23/05)

Hermes e Cérebro rodaram simulações independentes de padrões forex (1694 padrões) e fizeram cross-analysis. 5 correções aplicadas ao Neural KB. Ver `forex-choch-m15/references/cross-agent-simulation-2026-05-23.md`.

## Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `scripts/cerebellum.py` | +112 linhas: DANGEROUS_PATTERNS, ERROR_INJECTION_PATTERNS, scan_dangerous_commands(), scan_error_injections() |
| `thalamus/filters.py` | +35 linhas: _SANITIZE_PATTERNS, filter_error_sanitization(), integrado ao pipeline (posição 2) |
| `scripts/brain_code_validator.py` | NOVO (220 linhas): validate_syntax, validate_imports, validate_dangerous_patterns |
| `scripts/brain_browser.py` | NOVO (260 linhas): CDP controller para brain scripts |
| `scripts/tv_chart_analyzer.py` | NOVO (420 linhas): TradingView Bar Replay + análise |
| `scripts/tv_session_restore.py` | NOVO (80 linhas): restaura cookies Google OAuth |
| `scripts/chart_visual_learner.py` | NOVO (470 linhas): screenshots MT5 + OCR |
| `scripts/chart_pattern_degraded.py` | NOVO (500 linhas): templates numéricos + similarity |
| `skills/core/self-correction/SKILL.md` | +14 linhas: AP-11, AP-12, novas métricas |
| `skills/core/bi-neural-brain/SKILL.md` | +3 linhas: Cerebelo v2.1, Brain Code Validator, filtro error sanitization |
| `skills/core/brain-architecture/SKILL.md` | +4 linhas: tabela de agentes atualizada, filtro novo |

## Impacto

- **Segurança**: 13 padrões de ataque bloqueados + 7 padrões de injection sanitizados
- **Qualidade**: 64 scripts cerebrais validados via AST (LSP-style)
- **TradingView**: login Google persistente, Bar Replay funcional, 5 pares configurados
- **Tokens**: Zero — todas as melhorias são no_agent (scripts Python puros, sem LLM)
- **Anti-padrões**: 2 novas regras no self-correction (AP-11, AP-12)
