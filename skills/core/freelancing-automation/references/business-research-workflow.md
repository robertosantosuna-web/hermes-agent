# Pesquisa de Dados Empresariais — Técnicas

Workflow usado no projeto Martin (clínicas radiológicas, 22/05/2026).

## Pipeline de Pesquisa

### 1. Extrair CNPJ
```python
import urllib.request, re

query = f"{nome_empresa} {cidade} CNPJ"
url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
html = urllib.request.urlopen(url).read().decode()

cnpjs = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', html)
```

### 2. Extrair dados do site da empresa
```python
# Scraping direto do site (mais confiável que busca)
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, timeout=15).read().decode()

# CNPJ (geralmente no rodapé)
cnpj = re.findall(r'CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', html)

# Endereço
endereco = re.findall(r'(?:Rua|Avenida|Av\.|Alameda|Estrada|Praça)\s+[A-ZÀ-Ú][^,<]{10,80}(?:\d+|s/n|S/N)', html)

# Email
email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
# Filtrar: ignorar example.com, w3.org, schema.org

# Telefone
tel = re.findall(r'(?:\(?\d{2}\)?\s*)?\d{4,5}[-\s]?\d{4}', html)

# Modalidades de saúde (exemplo)
mods = re.findall(r'(?:Raios.?X|Tomografia|Ressonância|Mamografia|Ultrassonografia|Densitometria|PET.?CT|Medicina Nuclear)', html, re.IGNORECASE)
```

### 3. Buscar decisores e LinkedIn
```python
# LinkedIn da empresa
li_emp = re.findall(r'linkedin\.com/company/([a-zA-Z0-9_-]+)', html)

# LinkedIn de pessoas
li_pes = re.findall(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', html)

# Decisor (Dr., Diretor)
decisor = re.findall(r'(?:Dr\.?|Dra\.?)\s+([A-ZÀ-Ú][a-zà-ú]+(?:\s+[A-ZÀ-Ú][a-zà-ú]+){1,3})', html)
```

## Fontes de Dados

| Fonte | O que oferece | Confiabilidade |
|-------|--------------|----------------|
| DuckDuckGo Lite | CNPJ, telefone, links | Média (rate limit ~1/s) |
| Site da empresa | Endereço, email, modalidades | Alta |
| Google Search (bloqueado) | Tudo | — |
| Startpage | CNPJ (ruim) | Baixa (dados truncados) |
| BrasilAPI / ReceitaWS | CNPJ oficial | Alta (precisa CNPJ primeiro) |

## Pitfalls

1. **DuckDuckGo rate limit**: ~15 requisições antes de bloquear. Usar sleep(1.5) entre chamadas.
2. **CNPJ conflitante**: Empresas com múltiplas filiais retornam CNPJs diferentes. Verificar se o CNPJ corresponde à unidade correta.
3. **Startpage retorna dados truncados**: Telefones repetidos (0490-0491) para múltiplas empresas. Não confiável.
4. **Google bloqueia curl e browser tools**: Impossível usar. Fallback para DuckDuckGo Lite.
5. **Sites com SSL inválido**: Usar `ssl.create_default_context()` com `check_hostname=False`.
6. **Deletar duplicatas**: Planilhas frequentemente têm linhas duplicadas. Remover comparando `nome.lower().replace(' ', '')`.

## Template de preenchimento de planilha

```python
import openpyxl

wb = openpyxl.load_workbook('planilha.xlsx')
ws = wb['Aba']

# Mapear colunas por nome
col_map = {'CNPJ': 4, 'Endereço completo': 5, 'E-mail': 8, ...}

for r in range(2, ws.max_row + 1):
    nome = ws.cell(r, 1).value
    dados = pesquisar_empresa(nome, cidade)
    for campo, col in col_map.items():
        if campo in dados and not ws.cell(r, col).value:
            ws.cell(r, col).value = dados[campo]

wb.save('planilha_preenchida.xlsx')
```
