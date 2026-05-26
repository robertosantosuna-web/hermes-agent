## Novas Falhas (22/05/2026)

### fail-013: Google OAuth bloqueia browser tools
- **Plataforma**: 99Freelas
- **Erro**: "Navegador ou app pode não ser seguro" ao tentar login Google OAuth via Chromium do Hermes
- **Solução**: Desktop Daemon no Brave real do Roberto (sessão Google já autenticada)
- **Status**: known_workaround

### fail-014: WR hardcoded — bot ignorava performance real
- **Plataforma**: Forex
- **Erro**: `PAIRS[].wr` usava valor fixo do backtest (~67%), ignorando WR real de 33%
- **Raiz**: Self-learning nunca foi implementado
- **Correção**: `get_real_wr()` + `should_trade_pair()` — NZD/USD único par liberado
- **Status**: fixed

### fail-015: Conta real OANDA fantasma
- **Plataforma**: OANDA
- **Erro**: Tentativas de login em conta real que nunca existiu — só demo foi criada
- **Solução**: Criar conta real ou pivotar para Exness ($10 depósito pendente)
- **Status**: pending
