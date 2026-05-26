# B2B Prospecting Research Workflow — Preenchimento de Planilhas

## Contexto (22/05/2026)

Workflow usado no projeto Martin L. — pesquisa e prospecção B2B de clínicas radiológicas para 99Freelas. Planilha com 23 colunas: nome, cidade, estado, CNPJ, endereço, telefone, site, email, modalidades, unidades, decisor, cargo, LinkedIn, etc.

## Estratégia de Pesquisa (ordem de eficácia)

### Camada 1: Sites das próprias empresas
- Navegar no site oficial (já listado na planilha)
- Extrair: CNPJ (rodapé), endereço (contato), email, telefone, modalidades (página "Exames" ou "Serviços")
- Ferramenta: `curl` + regex ou `browser_navigate` + `browser_console`

```python
# Extrair CNPJ do rodapé do site
cnpjs = re.findall(r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', html)
# Extrair endereço
addrs = re.findall(r'(?:Rua|Avenida|Av\.|Alameda|Estrada|Praça)\s+[A-ZÀ-Ú][^,<]{10,80}(?:\d+|s/n)', html)
# Extrair modalidades
for mod in ['Tomografia', 'Ressonância', 'Mamografia', 'Ultrassonografia', 'Raio X', 'PET-CT', 'Medicina Nuclear', 'Densitometria']:
    if mod.lower() in html.lower(): modalidades.append(mod)
```

### Camada 2: DuckDuckGo Lite (não requer proxy)
- URL: `https://lite.duckduckgo.com/lite/?q=CNPJ+NOME+EMPRESA+CIDADE`
- Vantagem: não bloqueia curl como Google
- Limitação: rate limit após ~10 consultas (15s entre cada)
- Padrão de retorno: CNPJ em formato XX.XXX.XXX/XXXX-XX no texto dos resultados

### Camada 3: Startpage (fallback)
- URL: `https://www.startpage.com/sp/search?query=...`
- Mais tolerante que Google, mas resultados menos precisos
- Bons User-Agent headers necessários

### Camada 4: Google Search via Desktop Daemon (último recurso)
- Usar ydotool para abrir Brave, navegar para google.com, digitar busca, copiar resultados
- Só usar quando DuckDuckGo e Startpage falharem

## Campos e Fontes

| Campo | Melhor Fonte | Dificuldade |
|-------|-------------|-------------|
| CNPJ | Site oficial (rodapé) ou DuckDuckGo | Fácil |
| Endereço | Site oficial (página Contato) | Fácil |
| Telefone | Site oficial ou Google Maps | Fácil |
| Email | Site oficial (página Contato) | Médio |
| Modalidades | Site oficial (página Exames/Serviços) | Fácil |
| Quantidade de unidades | Site oficial (página Unidades) ou Google | Médio |
| Nome do decisor | LinkedIn ou site (página Institucional/Quem Somos) | Difícil |
| Cargo | LinkedIn ou site | Difícil |
| LinkedIn empresa | Google: "NOME_EMPRESA linkedin" | Fácil |
| LinkedIn pessoa | Google: "NOME_PESSOA linkedin CIDADE" | Difícil |

## Pitfalls

1. **Grandes redes têm múltiplos CNPJs** — usar CNPJ da matriz/sede, anotar na observação
2. **Clínicas pequenas sem site próprio** — usar Doctoralia, Google Maps, ou contato telefônico
3. **Decisor genérico é aceitável** — para clínicas pequenas, "Dr. Responsável Técnico (verificar CRM)" é suficiente como placeholder
4. **Duplicatas na planilha** — verificar nomes similares antes de preencher (ex: Nova Imagem Radiologia aparecia 2x)
5. **Dados de busca podem conter CNPJs de filiais** — sempre verificar se o CNPJ corresponde à cidade certa

## Exemplo: Planilha Martin (15 clínicas)

Resultado final:
- CNPJ: 15/15 (100%) — DuckDuckGo + sites oficiais
- Endereço: 15/15 (100%) — sites oficiais
- Modalidades: 15/15 (100%) — sites oficiais
- Decisor: 15/15 (100%) — 12 confirmados, 3 genéricos (clínicas pequenas)
- Email: 9/15 (60%) — sites oficiais + contato genérico
- LinkedIn: 9/15 (60%) — busca web

Tempo total: ~4 horas de pesquisa para 15 clínicas.
