# Agente Freelancer — Pitfalls de Email (29/05/2026)

## Remetentes Verificados (IMAP `FROM` search)

⚠️ **NÃO presumir os endereços. Sempre verificar com `mail.fetch()` antes de usar.**

| Plataforma | Remetente REAL (From header) | Remetente ERRADO (anterior) |
|-----------|------------------------------|---------------------------|
| **99Freelas** | `no-reply@99freelas.com.br` | ✅ Correto |
| **Freelancer.com** | `noreply@notifications.freelancer.com` | ~~`notifications@freelancer.com`~~ |
| **Workana** | `noreply-pt@workana.com` / `noreply-es@workana.com` | ~~`noreply@workana.com`~~ |
| **Fiverr** | `noreply@fiverr.com` (verificar) | ⚠️ Não confirmado |

### Como verificar remetentes

```python
import imaplib, email

mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
mail.login(USER, APP_PASS)
mail.select("INBOX")

# Buscar por domínio (mais abrangente)
status, msgs = mail.search(None, '(FROM "freelancer.com" SINCE "01-Jan-2026")')
for mid in msgs[0].split()[-3:]:
    status, data = mail.fetch(mid, "(RFC822)")
    msg = email.message_from_bytes(data[0][1])
    print(f"From: {msg['From']}")
```

---

## Bug 1: Remetentes Incorretos

**Sintoma:** `check_emails()` retorna 0 emails de Freelancer.com e Workana.

**Causa:** `PLATFORM_EMAILS` usava endereços incorretos:
- `notifications@freelancer.com` → real: `noreply@notifications.freelancer.com`
- `noreply@workana.com` → real: `noreply-pt@workana.com` e `noreply-es@workana.com`

**Correção:** Atualizar `PLATFORM_EMAILS` com endereços reais.

---

## Bug 2: `'novo projeto'` vs `'Novos projetos'` (Singular vs Plural)

**Sintoma:** Digests do 99Freelas com subject "Novos projetos" não são classificados como `new_project`.

**Causa:** O check `'novo projeto' in full_text` não captura "Novos projetos" porque "projeto" ≠ "projetos".

**Correção:** Adicionar `'novos projetos'` ao check:
```python
elif 'novo projeto' in full_text or 'novos projetos' in full_text or ...
```

---

## Bug 3: Keywords Apenas em Português

**Sintoma:** Emails do Freelancer.com (em inglês) nunca dão match em `QUICK_JOB_KEYWORDS`.

**Causa:** `QUICK_JOB_KEYWORDS` só tinha palavras em português. Emails do Freelancer.com vêm em inglês.

**Correção:** Adicionar keywords em inglês:
```python
QUICK_JOB_KEYWORDS = [
    # ... portuguese ...
    # English keywords (Freelancer.com)
    'data entry', 'typing', 'copy paste', 'spreadsheet',
    'proofread', 'edit', 'virtual assistant', 'admin support',
    'scrap', 'automation', 'python script', 'macro', 'vba'
]
```

---

## Bug 4: Digest Bloqueado por Skip Keywords

**Sintoma:** Digests (que contêm projetos de TODAS as categorias) são marcados `is_skip=True` porque contêm keywords como "site", "vídeo", "marketing" de projetos irrelevantes.

**Causa:** O classificador opera no email INTEIRO, não por projeto individual. Um digest com 30 projetos (2 de Excel + 28 de web dev) é bloqueado porque os 28 irrelevantes contêm skip keywords.

**Correção:** Se é digest E tem quick keywords, ignorar o skip:
```python
is_digest = ('novos projetos' in full_text or 'projects matching your skills' in full_text)
if is_digest and is_quick:
    is_skip = False  # Digests: quick wins over skip
```

**Limitação:** O agente atual classifica no nível de email (não de projeto individual). Para extrair projetos individuais de digests, seria necessário um parser de HTML específico por plataforma. Isso é um TODO para v2.

---

## Bug 5: `login` Genérico Antes de Check Específico

**Sintoma:** Emails do Freelancer.com classificados como `login_alert` (ignorados).

**Causa:** O check `'login' in full_text` vinha ANTES do check `platform == 'freelancer' and 'projects matching your skills'`. Emails do Freelancer contêm "login" no corpo (ex: "login to view project").

**Correção:** Mover checks platform-specific ANTES do check genérico `'login'`:
```python
# CORRETO: platform-specific ANTES do genérico
elif platform == 'freelancer' and 'projects matching your skills' in full_text:
    notif_type = 'new_project'
elif platform == 'workana' and 'seu perfil' in full_text:
    notif_type = 'login_alert'
elif 'login' in full_text or 'acesso' in full_text:
    notif_type = 'login_alert'
```

---

## Bug 6: `extract_project_title` Capturando HTML

**Sintoma:** Título extraído mostra `s <html xmlns="http://www` em vez do nome do projeto.

**Causa:** O regex `(?:projeto)\s*[:>-]?\s*(.+?)` captura o conteúdo após "projeto" no HTML bruto (antes do strip de tags).

**Correção:** Fazer strip de HTML antes do regex:
```python
clean_body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
clean_body = re.sub(r'<[^>]+>', ' ', clean_body)
clean_body = re.sub(r'\s+', ' ', clean_body)
search_text = subject + " " + clean_body[:500]
```

Para digests (onde não há um título único), usar o próprio subject como fallback:
```python
if 'novos projetos' in subject.lower():
    return 'Novos projetos (digest)'
if 'projects matching' in subject.lower():
    return 'Projects matching your skills (digest)'
```

---

## Bug 7: Digest Detectado MAS Regex Captura Igual (Extract Title Ordem)

**Sintoma:** Digests do 99Freelas geram títulos como `"s --> Olá, Roberto Rodrigues, há novos projetos que possam ser do seu interesse"` — o regex de extração de título captura texto de saudação do digest como se fosse título de projeto.

**Causa:** Em `extract_project_title()`, o regex `(?:Novo Projeto|no projeto|projeto)\s*...(.+?)` rodava ANTES do check de digest. O regex capturava "s" (fragmento HTML) + saudação após "projeto" no texto do digest.

**Correção (29/05):** Mover o check de digest para ANTES do regex:
```python
def extract_project_title(subject, body):
    # DIGESTS: detectar PRIMEIRO
    subj_lower = subject.lower()
    if 'novos projetos' in subj_lower or 'novos projetos' in body[:500].lower():
        return '99Freelas Digest — múltiplos projetos'
    if 'projects matching' in subj_lower:
        return 'Freelancer Digest — múltiplos projetos'
    # SÓ ENTÃO rodar o regex de título individual
    ...
```
E adicionar filtros anti-saudação no resultado do regex:
```python
if (title and not title.startswith('<') and len(title) > 5
    and 'há novos projetos' not in title.lower()
    and 'possam ser do seu interesse' not in title.lower()
    and 'olá' not in title.lower()[:10]):
    return title[:120]
```

---

## Bug 8: Contador de Propostas Cumulativo

**Sintoma:** `"Propostas geradas: 23"` — número cresce a cada execução, sem distinguir sessão atual do histórico.

**Causa:** `state['stats']['proposals_sent']` era incrementado a cada execução e nunca resetado. O resumo usava esse valor como "desta sessão".

**Correção:** Separar contador de sessão do histórico:
```python
session_proposals = len(quick_jobs)  # apenas desta execução
log(f"  Propostas geradas (sessão): {session_proposals}")
log(f"  Total histórico: {state['stats']['proposals_sent']}")
```

---

## Bug 9: `body[:3000]` Truncado por CSS (Digest Parser)

**Sintoma:** `parse_99freelas_digest()` recebia `body[:3000]` mas retornava 0 projetos — o CSS inline do email consumia 2000+ caracteres, deixando zero conteúdo real de projeto nos primeiros 3000 bytes.

**Causa:** Emails 99Freelas têm `<style>` extenso (~2KB de CSS) antes do conteúdo. `body[:3000]` pegava só CSS.

**Correção:** Strip do `<style>` antes de truncar + aumentar limite:
```python
'body': re.sub(r'<style[^>]*>.*?</style>', '', body[:15000], flags=re.DOTALL)
```

---

## Bug 10: Caracteres Acentuados no META_RE (Edição ≠ Edição)

**Sintoma:** Metadados do 99Freelas como "Edição & Revisão |" não eram reconhecidos como meta-linhas, causando vazamento de cabeçalhos de categoria como títulos de projeto.

**Causa:** O regex `^(?:Edição|...)` usa 'c' simples, mas o texto real do email contém 'ç' (c-cedilha): "Edição". O match falhava silenciosamente.

**Correção:** Usar classes de caractere para variantes com/sem acento:
```python
META_RE = re.compile(
    r'^(?:Edi[cç]ão|Entrada|Assistente|Iniciante|Intermedi[áa]rio|Avan[çc]ado|...)'
)
```

---

## Bug 11: Cabeçalhos de Categoria Vazando como Projetos

**Sintoma:** "Planilhas e Relatórios |", "Especialista |" e "Suporte Administrativo" apareciam como títulos de projeto extraídos do digest.

**Causa:** O check `if line in CATEGORY_HEADERS` exigia match EXATO, mas as linhas do email têm pipe (`|`) no final: "Planilhas e Relatórios |" ≠ "Planilhas e Relatórios". Além disso, categorias como "Especialista" não estavam no conjunto.

**Correção:** Normalizar a linha antes de comparar (strip de pipes e whitespace) + expandir o conjunto:
```python
normalized = line.rstrip('|').strip()
if normalized in CATEGORY_HEADERS:
    ...
CATEGORY_HEADERS = {
    'Suporte Administrativo', 'Edição & Revisão', 'Entrada de Dados',
    'Assistente Virtual', 'Especialista', 'Planilhas e Relatórios',
    'Revisão de Texto', 'Edição de Imagens', 'Web & Desenvolvimento', ...
}
```

---

## Bug 12: Keyword Stemming (cadastro ≠ cadastrar)

**Sintoma:** Projeto "Cadastrar roupas infantis na plataforma Tray" não era classificado como QUICK porque a keyword `'cadastro'` não é substring de `'cadastrar'`.

**Causa:** O matching usa `in` (substring): `'cadastro' in 'cadastrar'` → False. As duas palavras compartilham o radical "cadastr" mas a keyword exata não casa.

**Correção:** Adicionar variantes de radical às keywords:
```python
QUICK_JOB_KEYWORDS = [
    ...,
    'cadastro', 'cadastrar',  # ambas as formas
    ...
]
```

---

## Bug 13: Digest como Projeto Individual → Propostas Falsas

**Sintoma:** 8 "propostas" falsas geradas para digests em uma execução. Cada digest era tratado como 1 projeto, gerando proposta genérica.

**Causa:** `scan_and_act()` não distinguia digests de projetos individuais. O loop `for j in quick_jobs` gerava `generate_quick_proposal()` para cada digest como se fosse um projeto único.

**Correção:** Separar digests de projetos individuais ANTES do loop de propostas. Digests são reportados mas NÃO geram propostas automáticas (falta detalhe suficiente):
```python
digests = [o for o in new_opps if o.get('is_digest')]
individual = [o for o in new_opps if not o.get('is_digest')]
quick_jobs = [o for o in individual if o['is_quick_job'] and not o['is_skip']]
quick_digests = [d for d in digests if d['is_quick_job'] and not d['is_skip']]
```

Para digests, o parser `parse_99freelas_digest()` extrai projetos individuais e os reporta, mas sem gerar propostas automáticas.
Ver `references/digest-parser-implementation.md` para detalhes do parser.

---

## Bug 14: Healthcheck Bloqueia Pipeline Quando Só CDP Cai

**Sintoma:** Agente executa, faz healthcheck, detecta CDP Brave offline, e ABORTA — nunca chega a escanear emails. Output: "❌ Healthcheck falhou: CDP Brave offline" seguido de `return {'error': 'healthcheck_failed'}`.

**Causa:** `scan_and_act()` tratava QUALQUER falha de healthcheck como hard gate:
```python
if HEALTHCHECK_ENABLED:
    ok, details = healthcheck()
    if not ok:
        log(f"❌ Healthcheck falhou: {details}")
        return {'error': 'healthcheck_failed', 'details': details}  # ← ABORTA TUDO
```

**Impacto:** CDP Brave cai com frequência (processo morre, usuário fecha browser), mas IMAP continua 100% funcional. Com a lógica antiga, o agente ficava cego mesmo com email funcionando perfeitamente — perdendo novos projetos, mensagens de clientes e digests.

**Correção (29/05/2026):** Só abortar se AMBAS as fontes estiverem offline. Se uma fonte caiu, avisar e continuar com a outra:
```python
if HEALTHCHECK_ENABLED:
    ok, details = healthcheck()
    if not ok:
        details_str = details or ''
        if 'IMAP' in details_str and 'CDP' in details_str:
            log(f"❌ Healthcheck crítico: {details}")
            return {'error': 'healthcheck_failed', 'details': details}
        else:
            log(f"⚠️ Healthcheck parcial: {details}. Continuando com fontes disponíveis...")
```

**Princípio:** Healthcheck deve ser um *degradador* (reduz funcionalidade), não um *bloqueador* (derruba tudo). Email + CDP são fontes independentes — a falha de uma não deve impedir a outra de operar.

**Verificação:** Após o fix, com CDP offline, o agente deve mostrar "⚠️ Healthcheck parcial: CDP Brave offline. Continuando..." e então processar emails normalmente.

---

## Checklist de Validação Pós-Deploy

Após qualquer alteração no agente, verificar:
1. Executar `python3 ~/.hermes/brain/freelancer_agent.py` e inspecionar output
2. NENHUM título deve conter "Olá", "s <html", "há novos projetos"
3. Digests devem aparecer como "📋 DIGESTS" (não como "🎯 JOBS RÁPIDOS")
4. Propostas geradas (sessão) deve ser ≤ número de projetos INDIVIDUAIS
5. Projetos extraídos de digests devem ser títulos reais (não "Edição & Revisão |", "Especialista |")
6. "cadastrar" deve ser reconhecido como QUICK (verificar no output)
