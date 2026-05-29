# Platform Registration Results — 2026-05-29

Testes de cadastro em plataformas digitais USD usando número virtual +55 (61) 98173-7725 (quackr.io).

## Testados

| Plataforma | Status | Detalhe |
|-----------|--------|---------|
| **Fiverr** | ❌ Bloqueio | PerimeterX ERRCODE PXCR10002539 detecta CDP. Sem workaround. |
| **Workana** | ⚠️ Viável | Signup multi-etapa funciona. Fluxo: "Busco trabalho" → "Freelance" → "Avançar" → formulário. Não pede telefone no cadastro inicial. |
| **Mercado Livre** | ⚠️ Viável | Tem campo `tel`. Pede email primeiro, telefone depois. Form React. |
| **OLX** | ❌ Inútil | Não pede telefone no cadastro (CPF, nome, nascimento, email, senha). |
| **GetNinjas** | ❌ Offline | URL `/cadastro/profissional` retorna 404. |
| **Respondent.io** | ⚠️ Viável | Cadastro carrega, mas não pede telefone (só nome, email, senha). |
| **UserTesting** | ⚠️ Viável | Página de signup carrega. |
| **UpWork** | 🔜 Pendente | Aba criada, página carregou. Não testado além disso. |
| **DataAnnotation.tech** | ❌ Offline | `/signup` retorna 404. Tentar `/auth/signup`. |

## Plataformas já logadas (Brave :9222)

- **Freelancer.com** — Dashboard com 5 notificações. Login via Google ativo.
- **99Freelas** — Dashboard logado.
- **TradingView** — EURJPY chart aberto.

## Navegadores CDP — Status 29/05

| Porta | Browser | HTTP | WebSocket | Evaluate | Cookies |
|-------|---------|------|-----------|----------|---------|
| :9222 | Brave | ✅ | ✅ | ❌ (bloqueia sessão) | ❌ (retorna 0) |
| :9224 | Edge WA | ✅ | ❌ (não testado) | ❌ | ❌ |
| :9225 | Edge main | ❌ (caiu) | ❌ | ❌ | ❌ |
| :9226 | Chrome headless | ✅ | ❌ (403 Forbidden) | ❌ | ❌ |

## Recomendação para contas novas USD

1. **Freelancer.com** — já logado, operar direto
2. **UpWork** — criar conta (precisa de telefone, usar número virtual)
3. **Respondent.io** — criar conta (não precisa de telefone, mas paga $50-200/research)
4. **UserTesting** — criar conta ($10-60 por teste)
