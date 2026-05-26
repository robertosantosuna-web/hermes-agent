# Root Cause Analysis — Exemplos Reais (22/05/2026)

## Metodologia: "Vá aprofundando o porquê até chegar na raiz, depois faça o processo inverso resolvendo"

Esta é a técnica dos "5 Porquês" adaptada para debugging de sistemas. A diferença é que não basta perguntar — cada "porquê" exige EVIDÊNCIA (ler código, verificar estado real, inspecionar dados).

---

## Exemplo 1: Forex Bot abrindo ordens com WR 33% (abaixo do threshold de 40%)

**Sintoma:** Bot continua abrindo ordens mesmo com regra "WR<40% → NÃO ABRIR".

**Cadeia de investigação:**

1. **Por que o bot abre ordens com WR<40%?**
   → Verificar código: `forex_bot_real.py` linha 484: `if wr < 40: continue`
   → `wr` vem de `cfg['wr']`

2. **Por que `cfg['wr']` é >40% se o WR real é 33%?**
   → Olhar definição: `PAIRS = {'GBP/USD': {'wr': 67.9, ...}}`
   → É um valor HARDCODED

3. **Por que está hardcoded?**
   → Era o WR do BACKTEST (30 dias, dados históricos), não o WR da CONTA REAL

4. **Por que ninguém atualiza esse valor com o WR real?**
   → Procurar por "self_learning" no código: NADA encontrado
   → Self-learning era só intenção, nunca foi implementado

5. **Raiz:** O código compara contra o WR do backtest (~67%), não contra o WR real (33%). O sistema de self-learning nunca existiu.

**Solução (processo inverso):**
1. Renomear `cfg['wr']` → `cfg['backtest_wr']` (deixar claro que é referência)
2. Criar `get_real_wr(pair)` que lê `trade_log.json`
3. Criar `should_trade_pair(pair)` com regras: WR real<40%→bloqueia, elite≥80%→libera
4. Remover qualquer uso de `cfg['wr']` para decisão de trading

**Resultado:** NZD/USD (100% WR) = único par liberado. GBP/USD (25%), AUD/USD (25%), EUR/USD (0%) = bloqueados.

---

## Exemplo 2: OANDA "real bugada" — não consegue logar

**Sintoma:** Memória diz "OANDA real bloqueada (bug plataforma)". Múltiplas tentativas de login falharam.

**Cadeia de investigação:**

1. **Por que o login falha?**
   → Verificar credenciais: `user_profile.yaml` → senha `wc0ZO6#p`, servidor `OANDA_Global-Demo-1`

2. **Por que o servidor é "Demo"?**
   → Só existe conta DEMO. Procurar emails da OANDA: apenas 1 email, sobre conta demo

3. **Por que não existe conta real?**
   → O fluxo de criação de conta real nunca foi concluído. Apenas demo foi criada.

4. **Raiz:** Não existe conta real OANDA. A memória estava errada — o bug não era na plataforma, era tentar logar em uma conta que não existe.

**Solução:**
1. Corrigir memória: remover "OANDA real bloqueada"
2. Documentar estado real: demo #1715539800 ativa, saldo $85.30
3. Alternativa: Exness (cadastro preenchido, $10 depósito pendente)

---

## Exemplo 3: Desktop Daemon offline

**Sintoma:** Porta 9876 vazia. Sem controle do desktop.

**Cadeia de investigação:**

1. **Por que o daemon não está rodando?**
   → Nenhum processo na porta 9876

2. **Por que não iniciou?**
   → Não existia serviço systemd. O script era iniciado manualmente.

3. **Por que o script não sobrevive a reboots?**
   → Não estava registrado como serviço

4. **Raiz:** Sem systemd service, sem auto-start. Script também tinha bugs: XAUTHORITY hardcoded, screenshot usava grim (não suporta GNOME), screen_size era 1920x1080 fixo (real: 3840x1080).

**Solução (processo inverso):**
1. Corrigir XAUTHORITY: autodetect via `ls /run/user/1000/.mutter-Xwaylandauth.*`
2. Corrigir screenshot: grim → mss (compatível com GNOME/XWayland)
3. Corrigir screen_size: autodetect via mss
4. Criar `hermes-desktop-daemon.service` (systemd user)
5. `systemctl --user enable --now`

**Resultado:** Daemon rodando 24/7, porta 9876, screenshot funcional.

---

## Checklist: Root Cause Investigation

Antes de propor QUALQUER correção:

- [ ] Qual é o sintoma EXATO? (não "não funciona", mas "erro X na linha Y ao fazer Z")
- [ ] Já verifiquei o ESTADO REAL? (arquivos, processos, logs, não confiar na memória)
- [ ] Já li o CÓDIGO relevante? (não assumir — ler com read_file)
- [ ] Já perguntei "por quê?" pelo menos 3 vezes?
- [ ] Já encontrei EVIDÊNCIA para cada resposta?
- [ ] A raiz que encontrei explica TODOS os sintomas?

Se alguma resposta for NÃO, continue investigando. Não proponha correção ainda.
