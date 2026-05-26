# Técnicas de Pesquisa e Enriquecimento de Dados

Técnicas usadas no projeto Martin (planilha de clínicas radiológicas, 15 clínicas, 22/05/2026).

## Fontes de Dados

### 1. DuckDuckGo Lite (busca via terminal)
- URL: `https://lite.duckduckgo.com/lite/?q=...`
- Vantagem: não bloqueia curl/requests, retorna HTML simples
- Rate limit: ~1 req/segundo. Acima disso retorna `error-lite@duckduckgo.com`
- Alternativa quando rate-limited: Startpage (`startpage.com/sp/search`)

### 2. Scraping direto dos sites
- Extrair CNPJ do rodapé: regex `CNPJ[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})`
- Extrair endereço: regex `(?:Rua|Avenida|Av\.|Alameda|Estrada|Praça)\s+[A-ZÀ-Ú][^,;.]*(?:\d+|s/n|S/N|\d{5}-\d{3})`
- Extrair email: regex `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Modalidades: buscar keywords (Raios X, Tomografia, Ressonância, Mamografia, etc.)
- Ignorar SSL errors com `ssl._create_unverified_context()` para sites com certificado ruim

### 3. BrasilAPI / ReceitaWS
- Para buscar CNPJ quando não disponível no site
- Uso: `https://brasilapi.com.br/api/cnpj/v1/{cnpj}` (requer CNPJ primeiro)

## Pipeline de Enriquecimento

```
1. Extrair nome + cidade da planilha
2. Buscar no DuckDuckGo Lite: "{nome} {cidade} CNPJ endereço diretor"
3. Extrair CNPJ, endereço, email da página de resultados
4. Acessar site da clínica para confirmar e extrair modalidades
5. Buscar LinkedIn: "{nome} {cidade} LinkedIn diretor médico"
6. Preencher planilha com openpyxl
```

## Pitfalls

- CNPJs conflitantes: clínicas com múltiplas filiais retornam CNPJs diferentes. Usar o da matriz.
- Clínicas pequenas: dono/médico é o decisor mas nome não está público. Marcar como "Dr. Responsável (confirmar via telefone)".
- Grandes redes: endereço da SEDE, não da filial. Especificar "(sede)" ou "(matriz)".
- Emails genéricos (contato@, relacionamento@) são melhores que nada. Marcá-los como "email institucional".
