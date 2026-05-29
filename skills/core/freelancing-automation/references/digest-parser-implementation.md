# 99Freelas Digest Parser — Implementação (29/05/2026)

## Visão Geral

Parser state-machine que extrai títulos de projetos individuais de emails digest "Novos projetos" do 99Freelas. O parser opera sobre HTML já strippado (sem `<style>`, sem tags) usando heurísticas de estrutura do email.

## Estrutura do Digest 99Freelas

```
[Linha 0] Olá, Roberto Rodrigues, há novos projetos que possam ser do seu interesse. Veja os detalhes.
[Linha 1] Visualizar no navegador          ← email chrome
[Linha 2] Cancelar inscrição                ← email chrome
[Linha 3] Olá, Roberto Rodrigues.
[Linha 4] Há novos projetos que possam ser do seu interesse:  ← INÍCIO REAL
[Linha 5] Formatação de contratos em Word – ABNT     ← PROJETO 1
[Linha 6] Edição & Revisão |                          ← categoria meta
[Linha 7] Iniciante |                                 ← nível meta
[Linha 8] Publicado: ontem às 16:55 |                 ← data meta
[Linha 9] Tempo restante: 29 dias e 10 horas |
[Linha 10] Propostas: 19 |
[Linha 11] Interessados: 39
[Linha 12] Muito prazer! Meu nome é Talita...         ← DESCRIÇÃO (skip)
[Linha 13] Estamos organizando nossa documentação...  ← DESCRIÇÃO (skip)
[Linha 14] Habilidades desejadas: Word                ← skills meta
[Linha 15] Ver projeto                                ← action link
[Linha 16] Enviar proposta                            ← action link
[Linha 17] Suporte Administrativo                     ← CATEGORIA HEADER
[Linha 18] Cadastrar roupas infantis na plataforma Tray  ← PROJETO 2
...
[Linha N] Caso deseje alterar a frequência...         ← END MARKER
```

## State Machine

```
State: WAITING_FOR_TITLE
  → linha é CATEGORY_HEADER normalizado → salva título anterior, WAITING_FOR_TITLE
  → linha é META_RE match → IN_DESCRIPTION
  → linha é ACTION_LINK → WAITING_FOR_TITLE
  → linha 10-150 chars, não 'olá' → CAPTURA COMO TÍTULO, WAITING_FOR_TITLE
  → default → WAITING_FOR_TITLE

State: IN_DESCRIPTION
  → linha é CATEGORY_HEADER normalizado → salva título, WAITING_FOR_TITLE
  → linha é ACTION_LINK → WAITING_FOR_TITLE
  → linha é END_MARKER → salva + break
  → default → continua IN_DESCRIPTION (skip)
```

## Código

```python
def parse_99freelas_digest(body):
    projects = []
    # Strip HTML
    clean = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    clean = re.sub(r'<head>.*?</head>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<br\s*/?>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'</?(?:p|div|tr|td|table)[^>]*>', '\n', clean, flags=re.IGNORECASE)
    clean = re.sub(r'<[^>]+>', ' ', clean)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'\n\s*\n+', '\n', clean)
    
    lines = [l.strip() for l in clean.split('\n') if l.strip() and len(l.strip()) > 5]
    
    # Encontrar início: "Há novos projetos que possam ser do seu interesse:"
    digest_start = -1
    for i, line in enumerate(lines):
        low = line.lower()
        if ('há novos projetos' in low and ':' in low and 'interesse' in low):
            digest_start = i
            break
    if digest_start < 0:
        return projects
    
    CATEGORY_HEADERS = {
        'Suporte Administrativo', 'Desenvolvimento', 'Design',
        'Marketing', 'Tradução', 'Escrita', 'Financeiro',
        'Edição & Revisão', 'Entrada de Dados', 'Assistente Virtual',
        'Especialista', 'Planilhas e Relatórios', 'Revisão de Texto',
        'Edição de Imagens', 'Web & Desenvolvimento'
    }
    
    ACTION_LINKS = {
        'Ver projeto', 'Enviar proposta', 'Visualizar no navegador',
        'Cancelar inscrição', 'Ver Notificações e Alertas'
    }
    
    # IMPORTANTE: usar [cç], [áa] para variantes com/sem acento
    META_RE = re.compile(
        r'^(?:Edi[cç]ão|Entrada|Assistente|Iniciante|Intermedi[áa]rio|Avan[çc]ado|'
        r'Publicado|Tempo restante|Propostas|Interessados|Habilidades)\b'
    )
    
    END_MARKERS = [
        'caso deseje alterar', 'ver notificações e alertas',
        'configurações de notificações', 'politica de privacidade',
        'atenciosamente', 'equipe 99freelas', 'este é um email automático'
    ]
    
    current_title = None
    in_description = False
    
    for line in lines[digest_start + 1:]:
        # End markers
        if any(m in line.lower() for m in END_MARKERS):
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
            break
        
        # Action links — skip, reset description mode
        if line in ACTION_LINKS:
            in_description = False
            continue
        
        # Category headers — save previous, reset
        normalized = line.rstrip('|').strip()
        if normalized in CATEGORY_HEADERS:
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
                current_title = None
            in_description = False
            continue
        
        # Meta-data lines — enter description mode
        if META_RE.match(line):
            in_description = True
            continue
        
        # Skip during description mode
        if in_description:
            continue
        
        # Potential project title
        if 10 < len(line) < 150 and not line.startswith('http') and 'olá' not in line.lower()[:6]:
            if current_title:
                projects.append({'title': current_title[:150], 'platform': '99freelas'})
            current_title = line
    
    if current_title:
        projects.append({'title': current_title[:150], 'platform': '99freelas'})
    
    return projects
```

## Pitfalls Específicos

### 1. CSS consome os primeiros 2KB do body
**Sintoma:** Parser retorna 0 projetos.
**Causa:** Em `classify_opportunity`, `body[:3000]` inclui `<style>` de ~2KB antes do conteúdo real.
**Fix:** Strip `<style>` antes de truncar: `re.sub(r'<style[^>]*>.*?</style>', '', body[:15000], flags=re.DOTALL)`

### 2. Acentos quebram regex match
**Sintoma:** "Edição & Revisão |" não é reconhecido como meta.
**Causa:** `^(?:Edição|...)` não casa com "Edição" (c-cedilha).
**Fix:** Usar classes: `Edi[cç]ão`, `Intermedi[áa]rio`, `Avan[çc]ado`

### 3. Pipes em cabeçalhos de categoria
**Sintoma:** "Planilhas e Relatórios |" vaza como título de projeto.
**Causa:** Check `line in CATEGORY_HEADERS` falha porque "Planilhas e Relatórios |" ≠ "Planilhas e Relatórios".
**Fix:** `normalized = line.rstrip('|').strip()`

### 4. Saudação inicial como "projeto"
**Sintoma:** "Há novos projetos que possam ser do seu interesse:" aparece como título.
**Causa:** O `digest_start` apontava para a saudação (sem ":"), não para o início real (com ":").
**Fix:** Buscar linha com `':' in low` além de `'há novos projetos'` e `'interesse'`

### 5. Projetos consecutivos sem category header entre eles
**Sintoma:** Dois projetos na mesma categoria aparecem como um só.
**Causa:** Alguns digests não repetem o category header entre projetos da mesma seção.
**Mitigação atual:** O parser assume que projetos vêm em seções separadas por category headers. Projetos consecutivos sem header intermediário serão colapsados. Um parser de DOM completo (com seletores CSS) seria mais robusto mas requer HTML intacto.

## Uso no scan_and_act()

```python
# Em scan_and_act(), após classificar digests:
if d['platform'] == '99freelas':
    body_text = d.get('body', d.get('raw_snippet', ''))
    parsed = parse_99freelas_digest(body_text)
    quick_in_digest = [p for p in parsed 
                       if any(k in p['title'].lower() for k in QUICK_JOB_KEYWORDS)
                       and not any(k in p['title'].lower() for k in SKIP_KEYWORDS)]
    if quick_in_digest:
        log(f"       → {len(quick_in_digest)} projetos individuais detectados:")
        for p in quick_in_digest[:5]:
            log(f"         • {p['title'][:100]}")
```

## Decisão: NÃO gerar propostas automáticas para itens de digest

Projetos extraídos de digests são reportados mas NÃO recebem propostas automáticas porque:
1. O digest contém apenas resumos truncados — sem detalhes suficientes para proposta personalizada
2. Projetos podem estar fechados ou expirados quando o digest chega
3. Proposta genérica = spam = dano à reputação
4. O usuário deve revisar manualmente e decidir quais merecem proposta
