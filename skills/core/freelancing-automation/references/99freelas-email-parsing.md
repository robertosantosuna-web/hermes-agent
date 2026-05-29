# 99Freelas Digest Email Parsing — "Novos Projetos"

> Validado: 27/05/2026 — 2 digests parseados, 9 projetos cada, extração limpa.

Os emails de "Novos projetos" do 99Freelas chegam 2x ao dia (~09:40 e ~10:00 BRT) com subject "Novos projetos". São HTML inline-style, ~15-30KB, com 8-10 projetos listados.

## Estrutura do Digest

```
Olá, Roberto Rodrigues, há novos projetos que possam ser do seu interesse.
Há novos projetos que possam ser do seu interesse:

[TÍTULO DO PROJETO 1]
[CATEGORIA] |
Propostas: [N] |
Interessados: [N]
Ver projeto
Enviar proposta

[TÍTULO DO PROJETO 2]
[CATEGORIA] |
Propostas: [N] |
Interessados: [N]
[DESCRIÇÃO (se houver)] ... Leia mais.
Habilidades desejadas: [SKILLS]
Ver projeto
Enviar proposta
...
```

## Extração Robusta (sem depender de estrutura HTML exata)

A técnica confiável é fazer strip de HTML e depois parsear o texto limpo pelos marcadores `Propostas:` e `Interessados:`:

```python
import re
from email.header import decode_header

body = raw_html  # direto do email MIME

# Strip HTML
clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
clean = re.sub(r'<head>.*?</head>', '', clean, flags=re.DOTALL)
clean = re.sub(r'<br\s*/?>', '\n', clean)
clean = re.sub(r'<[^>]+>', '', clean)
clean = re.sub(r'&nbsp;', ' ', clean)
clean = re.sub(r'&amp;', '&', clean)
clean = re.sub(r'&quot;', '"', clean)
clean = re.sub(r'\n\s*\n+', '\n', clean)

lines = [l.strip() for l in clean.split('\n') if l.strip() and len(l.strip()) > 2]

# Encontrar a seção de projetos (após "possam ser do seu interesse")
capturing = False
projects = []
current = None

for line in lines:
    if 'possam ser do seu interesse' in line.lower():
        capturing = True
        continue
    if not capturing:
        continue
    # Fim do digest
    if 'Caso deseje' in line or line.startswith('99Freelas, 20'):
        if current:
            projects.append(current)
        break

    # Detectar proposta count → novo projeto
    if re.search(r'Propostas?:\s*\d+', line):
        if current:
            projects.append(current)
        current = {'proposals': line}
    elif re.search(r'Interessados?:\s*\d+', line) and current is not None:
        current['interests'] = line
    elif current is not None:
        # Primeira linha após propostas = título
        if 'title' not in current and len(line) > 10:
            current['title'] = line[:200]
        # Linhas seguintes = descrição (até "Leia mais" ou próxima seção)
        elif 'title' in current and 'desc' not in current:
            if 'Ver projeto' not in line and 'Enviar proposta' not in line and 'Habilidades' not in line:
                if len(line) > 10:
                    current['desc'] = line[:300]

if current:
    projects.append(current)

# Resultado
for i, p in enumerate(projects):
    title = p.get('title', '(sem título)')
    props = p.get('proposals', '?')
    intr = p.get('interests', '?')
    desc = p.get('desc', '')
    print(f"[{i+1}] {title}")
    print(f"    {props} | {intr}")
    if desc:
        print(f"    {desc[:150]}")
```

## Critérios de Bidding (aplicar a cada projeto)

```python
# Extrair números
prop_count = int(re.search(r'\d+', proposals).group())
intr_count = int(re.search(r'\d+', interests).group())

# Decisão
SKIP_KEYWORDS = ['intérprete', 'presencial', 'tradução simultânea']
QUICK_JOB_KEYWORDS = ['revisão', 'correção', 'abnt', 'format', 'digita',
                       'planilha', 'excel', 'google sheets', 'planilhas',
                       'word', 'pdf', 'converter', 'sumário', 'slide',
                       'powerpoint', 'cadastro', 'lista', 'ia', '3d']

is_quick_job = any(k in title.lower() for k in QUICK_JOB_KEYWORDS)
is_skip = any(k in title.lower() for k in SKIP_KEYWORDS)
is_lottery = prop_count > 25
is_low_competition = prop_count <= 10

if is_skip:
    verdict = "SKIP — não se aplica (presencial, fora de escopo)"
elif is_low_competition and is_quick_job:
    verdict = "✅ BIDAR — baixa competição + job rápido"
elif is_quick_job and not is_lottery:
    verdict = "⚠️ AVALIAR — job rápido mas competição média"
elif is_lottery:
    verdict = "❌ PULAR — loteria (>25 propostas)"
else:
    verdict = "⬜ IGNORAR — fora do foco de jobs rápidos"
```

## Pitfalls

- **Títulos podem ser truncados pelo parser**: O HTML do 99Freelas às vezes coloca o título do projeto dentro de `<a>` tags com estilos inline. Se o strip perder parte do título, o texto aparece como descrição. Solução: verificar se a "desc" capturada parece um título (curta, sem verbos).
- **Projetos sem título explícito**: Alguns projetos começam com "Olá, tudo bem?" ou "Fala, pessoal!" — são títulos reais (o cliente usou saudação como título). Classificar normalmente.
- **"Exclusivo" não aparece no digest**: Projetos Premium/Exclusivo NÃO são listados no email de "Novos projetos" — só aparecem para assinantes. Confirmar no site se necessário.
- **Descrição pode conter HTML entities**: `&#39;` = apóstrofe, `&quot;` = aspas. Fazer replace ANTES de classificar.
- **Orçamento NUNCA está no digest**: O 99Freelas não inclui budget nos emails de "Novos projetos". Para ver o budget, clicar no link do projeto.
