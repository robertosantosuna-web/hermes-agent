# Freelancer.com — Profile Completion (19/05/2026)

## Form location

The profile edit form is NOT at `/users/settings/profile` (404) or `/settings` (redirects to home). It appears **inline on project pages** when the profile is incomplete.

Access path: Open any project → scroll to top → "Complete seu perfil" section with fields.

## Fields

| Field ID | Type | Constraint |
|----------|------|-----------|
| `first-name` | input text | - |
| `last-name` | input text | - |
| `professional-headline` | input text | **MAX 50 CHARS** (shows "Por favor, não use mais que 50 caracteres.") |
| `summary` | textarea | - |
| `hourly-rate` | input number | USD/hour |
| address | input text | "Apenas sua cidade e país serão mostrados publicamente" |

## 3 Steps to complete profile

1. Atualize suas habilidades — skills update (separate page/flow, not on this form)
2. Verifique seu e-mail — email verification (done)
3. Atualize seu perfil — the inline form described above

## Blockers

- **Phone verification** (SMS): Blocks profile completion. Banner: "Hi Roberto. Please verify your phone number. This is an essential security check to help protect your identity. Verify via SMS"
- **Verified by Freelancer**: Required for projects >$2,500. Sabrina M. (@FLSabrina) is a sales agent for this program.

## Our values (as of 19/05/2026)

- first-name: Roberto
- last-name: Rodrigues dos Santos
- professional-headline: Automation & AI Engineer | Python & LLM (39 chars)
- summary: "Desenvolvo automações web, pipelines de dados e soluções de IA. Experiência com Python, Playwright, Excel avançado, APIs REST, e fine-tuning de modelos de linguagem (LoRA/QLoRA). Foco em entregar soluções limpas, documentadas e funcionais — no prazo."
- hourly-rate: 30
- address: Vespasiano, Minas Gerais, Brazil
- language: Português

## CDP notes

- The form fields use standard `<input>` and `<textarea>` — not Angular `fl-input` wrappers
- Native value setter + `dispatchEvent('input')` works for these fields
- Save button at ~(1132, 2291) on the WhatsApp project page
- After save, the page doesn't show confirmation — the form just stays. Verify by checking if fields retain values after page reload.
