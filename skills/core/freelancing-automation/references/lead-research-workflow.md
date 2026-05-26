# Lead Research Workflow — Preenchimento de Planilha B2B

Fluxo validado em 22/05/2026 para preencher dados de clínicas radiológicas (projeto Martin, 99Freelas).

## Estratégia de Busca (ordem de eficiência)

### 1. DuckDuckGo Lite (curl-friendly)
```python
url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
```
- Não bloqueia curl/requests
- Retorna HTML simples, fácil de parsear
- CNPJ: regex `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}`
- Endereço: regex `(?:Rua|Avenida|Av\.|Alameda|Estrada|Praça)\s+[A-ZÀ-Ú][^,]*\d+`
- Rate limit: ~1.5s entre requisições

### 2. Startpage (fallback)
```python
url = f"https://www.startpage.com/sp/search?query={encoded}&lang=pt"
```
- Mais tolerante que Google
- Precisa de User-Agent realista
- Resultados podem vir truncados/cacheados

### 3. Scraping Direto do Site da Empresa
```python
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
```
- CNPJ geralmente no rodapé (regex: `CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})`)
- Endereço na página de contato
- Email: regex `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Modalidades: buscar palavras-chave (Raios X, Tomografia, Ressonância, etc.)
- Ignorar SSL para sites com certificado ruim

### 4. Google (NÃO USAR)
- Bloqueia browser headless
- Bloqueia curl sem cookies
- Só funciona com browser real logado

## Campos a Preencher (prioridade)

| Prioridade | Campo | Como Encontrar |
|-----------|-------|---------------|
| Alta | CNPJ | Site (rodapé), DDG search |
| Alta | Endereço | Site (contato), DDG search |
| Alta | Telefone | Site (contato), já preenchido na maioria |
| Alta | Modalidades | Site (serviços/exames) |
| Média | Email | Site (contato/rodapé) |
| Média | Quantidade unidades | Site (sobre/unidades), Google Maps |
| Média | Decisor | LinkedIn search (pessoa), site (quem somos) |
| Baixa | LinkedIn empresa | DDG search `linkedin.com/company/` |
| Baixa | LinkedIn pessoa | DDG search `linkedin.com/in/` |
| Baixa | Coordenação técnica | Site (corpo clínico) |
| Baixa | Direção clínica | Site (quem somos/diretoria) |

## Pitfalls

1. **CNPJs conflitantes**: Diferentes buscas podem retornar CNPJs diferentes para a mesma empresa (matriz vs filial). Usar o que aparece com mais frequência.

2. **DuckDuckGo rate limit**: Após ~5-8 requisições rápidas, DDG retorna `error-lite@duckduckgo.com`. Aumentar delay para 2s+.

3. **Sites com SSL inválido**: Muitos sites de clínicas menores usam certificados autoassinados. Usar `ssl.create_default_context()` com `check_hostname=False`.

4. **Decisores genéricos**: Clínicas pequenas geralmente não publicam nomes de diretores. Nesses casos, preencher com "Dr. Responsável Técnico (verificar CRM)" e marcar como "a confirmar" nas observações.

5. **Startpage dados truncados**: Telefones e CNPJs podem vir embaralhados ou repetidos entre resultados. Validar antes de usar.

## Exemplo: 15 clínicas em ~10 min

Com 1.5s de delay entre requisições, 15 clínicas levam ~10-15 minutos para preencher CNPJ, endereço, email e modalidades via DDG + scraping dos sites.

Decisores e LinkedIn levam mais tempo (requerem buscas específicas por nome).

## Dependências

- `urllib.request` (stdlib)
- `re` (stdlib)
- `ssl` (stdlib)
- `openpyxl` (para editar .xlsx)
