---
name: email-autonomy
description: "Leitura, classificação, resposta e triagem autônoma de emails via IMAP/SMTP direto. Substitui himalaya. Integrado ao Gmail da ENTIDADE."
version: 1.1.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [email, imap, smtp, gmail, autonomy, triage]
    related_skills: [life-os, executive-communication, freelancing-automation, dashboard]
---

# Email Autonomy — Módulo Python Direto

**📧 Stack email: `email-autonomy` (primária) → IMAP/SMTP direto. `executive-communication` (triagem/resposta). `himalaya` (CLI, raramente usado). Use email-autonomy para 95% dos casos.**

Usa imaplib + smtplib nativos. NÃO depende de himalaya.

### Por que não himalaya

himalaya v1.2.0+ teve formato TOML quebrado entre versões. Config `[accounts."nome"]` 
com `imap.host` etc. resultou em "feature not available" e "TOML parse error" 
na mesma versão. Tempo perdido: ~30min em 2 sessões tentando formatos diferentes.

**Solução**: Python direto com `imaplib` (stdlib) + `smtplib` (stdlib). Zero dependências, 
controle total, funcionou na primeira tentativa.

### Gmail — App Password OBRIGATÓRIO

Senha normal NÃO funciona para IMAP/SMTP. O Google exige "Senha de app" gerada em:
https://myaccount.google.com/apppasswords

Pré-requisito: verificação em 2 etapas ativada na conta.
Gerar para app "E-mail", dispositivo "Linux". Senha de 16 caracteres (com espaços).

## CONTA CONFIGURADA

```
Email: robertosantos.una@gmail.com
IMAP:  imap.gmail.com:993 (SSL)
SMTP:  smtp.gmail.com:587 (STARTTLS)
Senha: App Password (16 chars)
```

## COMANDOS RÁPIDOS

**⚠️ ATENÇÃO: Não existe módulo `email_reader.py`. Use imaplib direto (stdlib, zero dependências) ou o script `scripts/check_email.py`.**

### Buscar emails por remetente e palavra-chave

```python
import imaplib, email, re
from email.header import decode_header

mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('robertosantos.una@gmail.com', SENHA_APP)
mail.select('INBOX')

# Buscar por remetente em intervalo de datas
status, msgs = mail.search(None, '(FROM "99freelas" SINCE "24-May-2026")')
ids = msgs[0].split()

for mid in ids:
    status, data = mail.fetch(mid, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    subj = decode_header(msg['Subject'])[0][0]
    if isinstance(subj, bytes): subj = subj.decode()
    
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                break
    else:
        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
    
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '\n', body)
    
    print(f'[{msg["Date"]}] {subj[:100]}')
    print(body[:300])

mail.logout()
```

### Enviar email

```python
import smtplib
from email.mime.text import MIMEText

msg = MIMEText('Corpo do email')
msg['Subject'] = 'Assunto'
msg['From'] = 'robertosantos.una@gmail.com'
msg['To'] = 'destino@email.com'

with smtplib.SMTP('smtp.gmail.com', 587) as s:
    s.starttls()
    s.login('robertosantos.una@gmail.com', SENHA_APP)
    s.send_message(msg)
```

## TRIAGEM AUTÔNOMA

### Classificação
```python
def classify_email(email):
    sender = email['from'].lower()
    
    # Oportunidades (prioridade máxima)
    if any(k in sender for k in ['99freelas', 'fiverr', 'workana', 'freelancer']):
        return 'OPORTUNIDADE'
    
    # Clientes (urgente)
    if any(k in email['subject'].lower() for k in ['projeto', 'pagamento', 'prazo', 'entrega']):
        return 'CLIENTE'
    
    # Financeiro
    if any(k in sender for k in ['paypal', 'picpay', 'nubank', 'bradesco', 'fatura']):
        return 'FINANCEIRO'
    
    # Pessoal importante
    if any(k in sender for k in ['familia', 'amigo']):
        return 'PESSOAL'
    
    # Spam/Newsletter
    if any(k in sender for k in ['newsletter', 'noreply', 'marketing']):
        return 'SPAM'
    
    return 'GERAL'
```

## MONITORAMENTO DE OPORTUNIDADES

### Scan automático a cada 2h
```python
def scan_opportunities():
    c = EmailClient()
    recent = c.list_since(days=1)
    opportunities = []
    
    platforms = {
        '99freelas': r'Novo Projeto: (.+)',
        'fiverr': r'New brief: (.+)',
        'workana': r'Novo projeto: (.+)',
    }
    
    for email in recent:
        for platform, pattern in platforms.items():
            if platform in email['from'].lower():
                match = re.search(pattern, email['subject'])
                if match:
                    opportunities.append({
                        'platform': platform,
                        'project': match.group(1),
                        'date': email['date'],
                        'link': extract_link(email['body']),
                    })
    
    return opportunities
```

## ALERTAS PROATIVOS

```python
def check_and_alert():
    c = EmailClient()
    unread = c.list_unread()
    
    alerts = []
    for email in unread:
        cat = classify_email(email)
        if cat in ['OPORTUNIDADE', 'CLIENTE', 'FINANCEIRO']:
            alerts.append(f'[{cat}] {email[\"from\"]}: {email[\"subject\"]}')
    
    if alerts:
        print(f'⚡ {len(alerts)} alertas:')
        for a in alerts:
            print(f'  {a}')
    else:
        print('✅ Nada urgente')
```

## MOTOR LOCAL DE MONITORAMENTO (no_agent)

Script `~/.hermes/scripts/monitor.py` — Python puro (zero tokens). Cron job `e566bcf226b8` roda a cada 5 min, entrega `local`.

**Fluxo:**
1. Conecta no Gmail via IMAP
2. Verifica emails de plataformas desde último check
3. Classifica: nova_mensagem, proposta_aceita, pagamento, novo_projeto
4. Só escreve `~/.hermes/monitor/wake.txt` se for alta prioridade
5. Agente lê o wake e age — sem gastar token em espera

**Quando acordar o agente:**
- ✅ Nova mensagem de cliente → SIM (urgente)
- ✅ Proposta aceita → SIM
- ✅ Pagamento recebido → SIM
- ✅ Novo projeto relevante (revisão/ABNT/TCC) → SIM
- ❌ Novo projeto genérico/survey → NÃO
- ❌ Login alert → NÃO

Consome ZERO tokens. Substitui o antigo \"Email Opportunity Scanner\" (LLM a cada 2h = ~$5/dia).

## CRON JOB (DEPRECATED — substituído pelo motor local)

```bash
# ❌ NÃO USAR MAIS — consome tokens desnecessariamente
# O motor local (monitor.py) faz o mesmo sem custo
```

## ENVIO DE EMAIL

```python
def send_email(to, subject, body):
    import smtplib
    from email.mime.text import MIMEText
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'robertosantos.una@gmail.com'
    msg['To'] = to
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('robertosantos.una@gmail.com', 'exnlrvfswckioces')
        server.send_message(msg)
```

## GMAIL LABELS — PITFALL DE ASPAS

Para acessar labels do Gmail com `imaplib.select()`, labels que contêm espaços ou caracteres especiais precisam de aspas duplas:

```python
# ❌ ERRO — "Could not parse command"
mail.select('[Gmail]/All Mail')
mail.select('All Mail')

# ✅ CORRETO
mail.select('"[Gmail]/All Mail"')
mail.select('"[Gmail]/Spam"')
mail.select('"[Gmail]/Trash"')
mail.select('"[Gmail]/Sent Mail"')
mail.select('"[Gmail]/Drafts"')

# INBOX funciona sem aspas
mail.select('INBOX')
```

**Regra**: sempre que o label tiver `/` ou espaço, envolver em aspas duplas. Labels simples como `INBOX` não precisam.

## SEGURANÇA

- App Password NUNCA deve ser commitada ou compartilhada
- Armazenar em ~/.hermes/.env com permissão 600
- Usar `password.cmd` ou variável de ambiente, nunca hardcoded

## PITFALLS DE EMAIL

### Mensagens truncadas em emails do 99Freelas
- **Sintoma**: email de "Nova mensagem de [cliente]" mostra apenas preview truncado com "..."
- **Causa**: O 99Freelas envia apenas um preview no email. O conteúdo completo está na plataforma.
- **Solução**: Para ler a mensagem completa, acessar o site 99freelas.com.br e abrir a conversa do projeto. NÃO tentar extrair do email.
- **Workaround**: Se Cloudflare Turnstile bloquear CDP, usar Desktop Daemon + ydotool no Brave real (ver skill `freelancing-automation` e memória: "Turnstile→Daemon+ydotool(não CDP)")
- **Sintoma**: plataforma mostra "email enviado" mas nada aparece no Gmail (inbox, spam, all mail)
- **Causa possível**: bloqueio no servidor do Gmail para domínios específicos (`neevo.ai`, `definedcrowd.com`)
- **Solução**: reenviar do site (clicar "Resend email") + aguardar até 10 min
- **Se persistir**: verificar no Gmail web se há filtros bloqueando o domínio. Tentar email alternativo.

### Gmail Label Names (IMAP)
- Labels com acentos ou nomes em português podem falhar com `mail.select()`
- Usar aspas duplas: `mail.select('"[Gmail]/All Mail"')` — NÃO usar aspas simples
- Labels padrão: `"[Gmail]/All Mail"`, `"[Gmail]/Spam"`, `"[Gmail]/Trash"`, `"INBOX"`

- NÃO usar `no-reply@` ou `noreply@` como filtro de exclusão genérico (captura 99Freelas, Fiverr, GitHub, bancos)
- NÃO fazer limpeza em massa sem WHITELIST explícita antes
- NÃO usar `mail.expunge()` sem revisar o que foi marcado como `\\Deleted`
- NÃO selecionar labels Gmail sem aspas duplas: use `"[Gmail]/All Mail"`, NÃO `[Gmail]/All Mail` (IMAP retorna "Could not parse command" sem aspas)
- NÃO fazer search ALL em inboxes grandes (>5000 emails) sem `limit` — pode causar timeout. Use `newer_than` ou `SINCE` date filters.

### WHITELIST (nunca deletar emails destes)
```
99freelas.com.br, fiverr.com, workana.com, freelancer.com
github.com, gitlab.com
paypal.com, picpay.com, nubank.com.br, bradesco.com.br
accounts.google.com (alertas de segurança)
contato@, suporte@, atendimento@ (canais de cliente)
oanda.com (broker — credenciais, updates de conta)
```

### Processo seguro de limpeza
1. Listar remetentes primeiro (não deletar)
2. Separar WHITELIST (acima) dos TRASH
3. Revisar manualmente remetentes com >10 emails
4. Só então marcar `\\Deleted`
5. NUNCA `expunge()` sem confirmação

### Gmail bloqueio silencioso de domínios

Alguns domínios podem ter emails bloqueados pelo Gmail ANTES de chegar à caixa (nem INBOX, nem Spam, nem All Mail). Sintoma: zero emails do domínio em qualquer label, mesmo após reenvio pelo remetente.

**Exemplo documentado**: `neevo.ai` / `definedcrowd.com` (19/05/2026) — cadastro criado, tela mostra "confirmation email sent", reenvio solicitado, zero emails em todas as labels. Causa provável: bloqueio no servidor do Gmail (não é filtro do usuário).

**Workaround**: usar outro provedor de email (ProtonMail, Outlook) para plataformas cujo domínio é bloqueado pelo Gmail.

## EXTRAÇÃO DE CONTEÚDO DE HTML

Emails de plataformas (99Freelas, Fiverr) usam templates HTML pesados com `<style>` extenso. Ver `references/html-extraction.md` para a técnica completa.

Técnica resumida:
1. `re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)` — remove CSS
2. `re.sub(r'<head>.*?</head>', '', html, flags=re.DOTALL)` — remove metadata
3. `re.sub(r'<[^>]+>', '\n', html)` — troca tags por newlines
4. Filtrar linhas: `len > 15` e sem keywords boilerplate (`cancelar`, `inscrição`, `newsletter`, `direitos`, `visualizar`, `navegador`)

### Extração de credenciais de brokers/trading platforms

Emails de brokers (OANDA, FXCM, etc.) contêm credenciais em formato chave-valor no corpo HTML. Após limpar o HTML, buscar por padrões como:

```python
import re

def extract_credentials(text):
    """Extrai login/senha/servidor de email de broker"""
    creds = {}
    patterns = {
        'login': r'Login:\s*(\d+)',
        'password': r'Password:\s*(\S+)',
        'server': r'Server:\s*(\S+)',
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        if m:
            creds[key] = m.group(1)
    return creds
```

Salvar em `~/.hermes/forex/user_profile.yaml` na seção `plataformas.oanda:`.
