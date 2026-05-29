# Freelancer.com Email Parsing — Digest de Projetos

> Validado: 27/05/2026 — 2 emails, 19-20 projetos extraídos com sucesso.

Freelancer.com's "projects matching your skills" digest emails are ~70KB of heavily nested inline-CSS HTML (no stylesheet blocks, all inline `style=` attributes). Standard HTML-strip-then-split-line extraction loses all structure.

## Estrutura Real do HTML (descoberta 27/05/2026)

Cada projeto é um bloco com esta estrutura exata:

```html
<tr><td>
  <a href=https://www.freelancer.com/projects/...>
    <span style=...font-size:16px;font-weight:700>PROJECT_TITLE</span>
  </a>
<tr><td height=4>
<tr><td>
  <span style=...font-size:12px;font-weight:400>DESCRIPTION_TEXT</span>
  ... <a href=...><span>See more</span></a>
<tr><td height=4>
<tr><td>
  <span style=...font-weight:700>Skills: </span>
  <span style=...font-weight:400>SKILL1 | SKILL2 | ...</span>
</table>
<td width=16>
<td ... width=130>  <!-- coluna direita: budget -->
  <span style=...font-size:16px;font-weight:700>$X - $Y USD</span>
  ...
  <a ...>Bid now</a>
</td>
```

**NÃO existem labels "PROJECT", "DESCRIPTION", "BUDGET" no HTML** — a estrutura é puramente posicional via `<table>` rows.

## Regex Funcional (validado 27/05/2026)

```python
import re

body = raw_html  # direto do email, sem strip

# 1. Títulos + URLs dos projetos
urls_titles = re.findall(
    r'<a href=(https?://www\.freelancer\.com/projects/[^\s>]*?)[^>]*?>'
    r'.*?<span[^>]*?>([^<]{10,200})</span>\s*</a>',
    body, re.DOTALL
)

# 2. Budgets (coluna direita, formato $X - $Y USD ou $X USD)
budgets = re.findall(
    r'\$\s*([\d,]+)\s*(?:[-–]\s*\$?\s*([\d,]+))?\s*USD',
    body
)

# 3. Descriptions (span antes de "... See more")
descs = re.findall(
    r'font-weight:400;line-height:1\.5>([^<]{40,400})</span>\s*\.\.\.\s*<a href=',
    body
)

# 4. Skills (após "Skills:" label)
skills = re.findall(
    r'Skills:[^<]*</span>\s*<span[^>]*>([^<]+)</span>',
    body
)
```

### Alinhamento

URLs/titles, budgets, descs, e skills aparecem na MESMA ORDEM no HTML. Alinhar por índice:

```python
for i, (url, title) in enumerate(urls_titles):
    title = re.sub(r'<[^>]+>', '', title).strip()
    
    if i < len(budgets):
        b = budgets[i]
        budget = f"${b[0]} - ${b[1]} USD" if b[1] else f"${b[0]} USD"
    else:
        budget = "?"
    
    desc = descs[i][:200] if i < len(descs) else ''
    skill = skills[i][:150] if i < len(skills) else ''
    
    print(f"[{i+1}] {title} | {budget} | {skill}")
```

## Filtro de Relevância

Filtrar projetos por keywords nas 3 fontes (título + descrição + skills):

```python
kw = ['python', 'automation', 'excel', 'script', 'api', 'data', 'scrap',
      'bot', 'automa', 'planilha', 'google sheets', 'vba', 'llm', 'ai',
      'selenium', 'playwright', 'whatsapp', 'dialog', 'chrome', 'puppeteer',
      'integrate', 'integration', 'webhook', 'csv', 'json', 'rest', 'twilio',
      'chatbot', 'n8n', 'make.com', 'zapier']

combined = f"{title} {desc} {skill}".lower()
is_relevant = any(k in combined for k in kw)
```

## Pitfalls

- **Budgets são ranges, não valores fixos**: `$18 - $146 USD` significa que o cliente espera propostas nessa faixa. O valor real depende da negociação.
- **Orçamento mínimo enganoso**: Projetos com `$2 - $8 USD` geralmente são placeholders — o budget real está na descrição.
- **"See more" trunca descrições**: A descrição no email é truncada. Para o texto completo, clicar no link do projeto.
- **Projetos repetidos entre digests**: O mesmo projeto pode aparecer em múltiplos emails (ex: Python digest + API Development digest).
- **Perfil incompleto bloqueia**: Projetos >$2.500 USD exigem "Verified by Freelancer". Sem telefone verificado, o perfil não completa e esses projetos são inacessíveis.

## Email Characteristics

- **From:** `Freelancer.com <noreply@notifications.freelancer.com>`
- **Subject pattern:** `Roberto, these {skills} projects might interest you`
- **Body size:** 60-80KB HTML (inline CSS, sem `<style>` blocks — usar regex direto)
- **Structure:** Cada projeto = bloco de `<tr>` rows com `<td>` para título/descrição/skills + `<td width=130>` para budget
- **Project URLs:** Disponíveis nos atributos `href` dos links de título — extraíveis via regex
