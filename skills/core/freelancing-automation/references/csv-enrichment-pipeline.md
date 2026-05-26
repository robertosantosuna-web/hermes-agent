# CSV Enrichment Pipeline — Preenchimento B2B em Larga Escala

> Validado: 24/05/2026 — 69 clínicas radiológicas SP+RJ

## Padrão: delegate_task com batch processing

Quando uma planilha tem 50+ linhas para enriquecer, usar `delegate_task` com 3-4 tasks paralelas, cada uma responsável por um range de linhas.

```python
delegate_task(tasks=[
    {"goal": "Enrich rows 1-23 of CSV...", "toolsets": ["web","terminal","file"]},
    {"goal": "Enrich rows 24-46 of CSV...", "toolsets": ["web","terminal","file"]},
    {"goal": "Enrich rows 47-69 of CSV...", "toolsets": ["web","terminal","file"]},
])
```

**Cada subagent deve:**
1. Ler o CSV com `csv.DictReader`
2. Enriquecer APENAS seu range de linhas
3. Escrever de volta com `csv.DictWriter` (NÃO openpyxl — é CSV, não XLSX)
4. NÃO modificar linhas fora do seu range

**Resultado (69 clínicas):**
- Batch 1 (rows 1-23): Timeout após 1200s — 45 API calls
- Batch 2 (rows 24-46): ✅ Completo — 44 API calls, 1043s
- Batch 3 (rows 47-69): ✅ Completo — 55 API calls, 890s
- Follow-up: 1 batch adicional para preencher gaps → 100% completude (0 células vazias)

## Estratégia de Pesquisa por Tipo de Clínica

### Redes grandes (Fleury, DASA, Hermes Pardini, Lavoisier, CDPI, etc.)
- CNPJ: usar o CNPJ da MATRIZ (ex: Fleury = 60.840.055/0001-31)
- Coordenação Técnica / Direção Clínica: "Centralizado na matriz" (nomes de unidades não são públicos)
- CEO: pesquisar no LinkedIn ou Google "CEO [nome da rede]"
- LinkedIn: perfil corporativo + perfil do CEO

### Clínicas independentes
- CNPJ: buscar via Brasil API (`https://brasilapi.com.br/api/cnpj/v1/{CNPJ}`) ou Google "NOME DA CLINICA cnpj"
- Sócios-administradores: Brasil API retorna `quadro_societario_administradores` com nome
- LinkedIn: Google "NOME DO DECISOR linkedin"

### Clínicas sem presença web
- Marcar TODOS os campos não encontrados como "Não encontrado" (NUNCA deixar vazio)
- Adicionar nota em Observações: "Clínica sem presença web significativa"
- NÃO inventar dados

## Ferramentas de Pesquisa

| Ferramenta | URL | Usar para |
|-----------|-----|-----------|
| Brasil API | `https://brasilapi.com.br/api/cnpj/v1/{CNPJ}` | CNPJ, endereço, sócios |
| Google Search | `curl` com User-Agent real | Nome da clínica + "cnpj" |
| LinkedIn | `curl` ou CDP | Perfil do decisor |
| DuckDuckGo | `ddgs` Python library | Busca inicial por CNPJ |

## Geração do XLSX Final

Após enriquecer o CSV, converter para XLSX formatado com `openpyxl`:
- 1 aba por estado + 1 aba "Todas"
- Cabeçalho azul escuro com fonte branca
- Auto-filtro em todas as colunas
- Larguras de coluna otimizadas para cada campo
