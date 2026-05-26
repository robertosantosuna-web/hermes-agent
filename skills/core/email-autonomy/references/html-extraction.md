# Extração de Texto de Emails HTML

Técnica usada para extrair conteúdo legível de emails de plataformas (99Freelas, Fiverr) que usam templates HTML com CSS inline extenso.

## Problema

Emails de plataformas usam HTML complexo:
```html
<html>
  <head><style>@media only screen... (300+ linhas CSS)</style></head>
  <body style="background-color: #e7e5e7;">
    <table><tr><td>
      <!-- header com logo, data -->
      ...
      <!-- conteúdo real escondido em divs aninhadas -->
      <div>Olá, Roberto. Nova mensagem de Martin L.</div>
      ...
    </td></tr></table>
  </body>
</html>
```

`msg.get_payload(decode=True)` retorna o HTML bruto. `text/plain` geralmente está vazio ou com placeholder.

## Técnica (3 passos)

```python
import re

def extract_text_from_html_email(html: str) -> list[str]:
    """Extrai linhas de texto significativas de email HTML."""
    
    # Passo 1: Remover CSS e metadados
    body = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    body = re.sub(r'<head>.*?</head>', '', body, flags=re.DOTALL)
    
    # Passo 2: Converter tags HTML em newlines (preserva estrutura)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<[^>]+>', '\n', body)
    
    # Passo 3: Limpar whitespace
    body = re.sub(r'\n\s*\n+', '\n', body)
    body = re.sub(r'[ \t]+', ' ', body)
    
    # Extrair linhas significativas
    boilerplate_keywords = [
        '99freelas', 'cancelar', 'visualizar', 'navegador', 
        'inscrição', '©', 'direitos', 'reservados', 'newsletter',
        'enviado', 'politica de privacidade', 'termos de uso',
        'notificações', 'alertas'
    ]
    
    lines = [
        line.strip() 
        for line in body.split('\n') 
        if line.strip() 
        and len(line.strip()) > 15
        and not any(skip in line.lower() for skip in boilerplate_keywords)
    ]
    
    return lines
```

## Uso prático

```python
import imaplib, email

mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login(USER, APP_PASSWORD)
mail.select('INBOX')

status, ids = mail.search(None, '(FROM "99freelas" SUBJECT "Nova mensagem")')
for num in ids[0].split()[-5:]:  # últimos 5
    status, data = mail.fetch(num, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            lines = extract_text_from_html_email(html)
            for line in lines:
                print(line)
```

## Limitações

- Emails puramente baseados em imagens não extraem texto
- Tokens de confirmação (`token=***`) são mascarados pela plataforma — links "visualizar no navegador" são inúteis
- Emojis e caracteres especiais podem ser perdidos se o charset não for UTF-8
- Tabelas complexas viram texto linear (perde estrutura colunar)
