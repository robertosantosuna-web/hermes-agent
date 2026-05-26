# Plataformas — Cadastro Autônomo (19/05/2026)

Registro de URLs corretas, bloqueios e padrões descobertos durante sessão de cadastro em massa.

## URLs CORRETAS DE CADASTRO

| Plataforma | URL de registro | Tipo de auth | Resultado |
|-----------|----------------|-------------|-----------|
| TimeBucks | timebucks.com → "Continue with Google" | Google OAuth | ✅ Completo automático |
| Toloka | we.toloka.ai/auth → "Continue with Google" | Google OAuth + SMS | ✅ Completo (SMS manual) |
| Neevo | neevo.definedcrowd.com/en-us/account/register/ | Email + senha | ✅ Completo (email externo) |
| SproutGigs | sproutgigs.com/signup.php | Email + senha | 🟡 Bootstrap-select |
| Clickworker | workplace.clickworker.com/en/users/new/ | Email + senha (Rails) | 🟡 Bootstrap-select |
| OneForma | my.oneforma.com/center/signup | Email + senha | 🟡 Bootstrap-select |
| GoTranscript | gotranscript.com | — | 🔜 Pendente |

## URLS DE DASHBOARD (após login)

| Plataforma | Dashboard | Notas |
|-----------|----------|-------|
| TimeBucks | timebucks.com/publishers/index.php?pg=dashboard | Earn: pg=earn&tab=all_surveys |
| Toloka | we.toloka.ai/explore | Perfil em "Complete your profile" |
| Neevo | neevo.definedcrowd.com/en-us/dashboard/work | Skills: /dashboard/skills-badges |

## PADRÃO GOOGLE OAUTH (funciona sempre)

1. Navegar para página de login da plataforma
2. Clicar "Continue with Google" (Input.dispatchMouseEvent)
3. Google Account Chooser → clicar perfil "Roberto Rodrigues"
4. Consent screen → clicar "Continuar"
5. **Importante**: OAuth pode completar em OUTRA aba. Verificar todas as abas após 5-8s.
6. TimeBucks completou em background sem refresh da aba de origem.

## BLOQUEIOS POR COMPONENTE

### Bootstrap-select (Clickworker, SproutGigs, OneForma)
- Select nativo aceita `value = "br"` mas componente visual não atualiza
- `$(sel).selectpicker('refresh')` não disponível sem jQuery injetado
- Validação do form detecta que dropdown não foi preenchido visualmente
- **Solução**: usuário interage manualmente (30s-5min por plataforma)

### React Custom Dropdown (Neevo firststeps)
- Lista de 261 idiomas, só ~30 no DOM (virtualizada)
- `Input.dispatchKeyEvent` não aciona filtro React
- Opção "Portuguese" no índice 172, fora da viewport
- **Solução**: scroll do container até a opção + click. Falhou via CDP. Resolvido pelo usuário.

### Email confirmation (Neevo)
- Confirmation email NUNCA chegou no Gmail (inbox, spam, all mail)
- Reenvio via página não surtiu efeito
- Usuário confirmou externamente (provavelmente mobile)
- **Suspeita**: Neevo email system com delay ou Gmail server-level block

## NEEVO — FLUXO COMPLETO

1. Register (email + senha) → confirmation email (pode não chegar)
2. Após confirmar → firststeps (seleção de idioma)
3. Dashboard: `/dashboard/work` → sem jobs até qualificar
4. Skills & Badges: `/dashboard/skills-badges` → testes de idioma
5. **Requer PayPal validado** para fazer os testes
6. Testes disponíveis: Writing + Listening (Portuguese-Brazil)

## TIMEBUCKS — SURVEYS DISPONÍVEIS

- Dashboard mostra survey list com preços ($0.02 a $1.77)
- Menor cash out: $2.70
- Bônus diário/semanal por volume
- Tasks: games, surveys, offerwalls, bonus clicks, refer

## TOLOKA — TASKS DISPONÍVEIS

- UHRS tasks: $0.05 a $10.00 por task
- Precisa completar perfil para acessar todas
- Abas: Projects, Qualifications, Tasks
