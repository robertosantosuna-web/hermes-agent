---
name: proposta-99freelas
description: "Template e regras para propostas no 99Freelas. Voz unificada orgânico+máquina = Roberto."
version: 1.0.0
---

# Template de Proposta — 99Freelas (e Freelancer.com)

O mesmo template serve para 99Freelas e Freelancer.com. A diferença é o idioma: Freelancer.com usa inglês para projetos internacionais.

## Regras de ouro

1. **NUNCA** mencionar valor ou prazo no corpo do texto — os campos do formulário já mostram
2. **NUNCA** colocar valor diferente do que foi preenchido no campo "Oferta Final"
3. **SEMPRE** usar acentos e português correto
4. **SEMPRE** usar o nome do cliente na abertura
5. Máximo **3 parágrafos curtos**
6. Fechar com "abs, Roberto"

## Tom de voz

- Ao cliente, somos UMA pessoa: Roberto
- Natural, direto, sem firula
- Sem arrogância ("perfil ideal", "sou o melhor")
- Sem subserviência ("posso ajudar", "ficaria grato")
- Sem desespero ("imediatamente", "urgente", "hoje mesmo")

## Template

```
[Nome], [1 frase mostrando que entendeu o projeto].

[1-2 frases com qualificação específica para ESSE projeto. Sem lista genérica, sem bullets, sem tecniquês desnecessário].

[Fechamento curto: "Posso começar assim que confirmar" / "Se quiser, mostro um exemplo antes" / "Bora conversar?"].

abs,
Roberto
```

## Exemplos

### Projeto de formatação ABNT

> Luana, já formatei TCCs e artigos acadêmicos nas normas ABNT atualizadas.
>
> Faço sumário automático, numeração, citações, referências e margens — tudo revisado antes de entregar.
>
> Posso começar assim que você confirmar.
>
> abs, Roberto

### Projeto de planilha Excel

> Tatiana, entendi a estrutura: seleção automática por tipo de licença com validação de dados e grupos por categoria.
>
> Já montei planilhas similares com proteção contra erro de preenchimento e formato limpo.
>
> Se quiser, mostro um exemplo com 2 categorias antes de concluir.
>
> abs, Roberto

### Projeto de prospecção B2B

> Martin, pesquiso e organizo leads B2B em planilha limpa: nome, cidade, telefone, site — tudo padronizado.
>
> Já fiz trabalho similar com clínicas e empresas de saúde. Entrego uma amostra inicial pra alinharmos o formato.
>
> Posso começar hoje. abs, Roberto

## Anti-padrões (nunca usar)
## Anti-padrões (nunca usar)

- ❌ "Enviei uma proposta de R$ X..." — redundante
- ❌ "Tenho o perfil ideal para este projeto"
- ❌ "Posso ajudar com..."
- ❌ "experiencia", "formatacao" (sem acentos)
- ❌ Texto em parágrafo único sem quebras
- ❌ Sem nome do cliente na abertura

## Templates automáticos por categoria (Freelancer Agent v1)

O agente gera propostas automaticamente baseadas no tipo de job. Templates por categoria:

| Categoria | Keywords | Abertura |
|-----------|----------|----------|
| Planilhas | excel, planilha, google sheets | "Entendi a necessidade da planilha. Tenho experiência com Excel/Google Sheets..." |
| Digitação | digita, cadastro, lista, copiar | "Posso fazer essa digitação/cadastro. Sou rápido e organizado..." |
| Revisão | revisão, correção, abnt, tcc | "Faço revisão ortográfica e formatação ABNT/NBR. Já revisei artigos..." |
| Tradução | traduç, tradução | "Faço tradução PT-EN e EN-PT. Texto natural, sem tradução literal..." |
| PDF/Word | pdf, word, converter | "Faço conversão e edição de PDF/Word. Posso converter, formatar..." |
| Genérico | (fallback) | "Vi seu projeto e posso ajudar. Sou organizado, cumpro prazos..." |

Todas as propostas fecham com "abs,\nRoberto". Nunca repetir valor/prazo no corpo.
- ❌ Sem assinatura no final
- ❌ "I am confident I can..." / "I believe I am the perfect fit" (Freelancer EN)

## Template em inglês (Freelancer.com)

Para projetos internacionais, mesmo formato 3 parágrafos:

```
[Nome], I've built similar [tipo de projeto] before — [1 resultado concreto].

I can deliver [escopo claro] with [diferencial específico].

Happy to share a quick sample before we proceed.

—Roberto
```

## Pitfalls

### Valor divergente (gravissimo)
Se o campo "Oferta Final" tem R$ 37,50 e o texto diz R$ 50,00, o cliente vê dois valores diferentes. Isso quebra confiança instantaneamente.

### Acentos no CDP
Ao digitar via `Input.insertText`, usar caracteres Unicode normalmente — o campo aceita. Não usar `Input.dispatchKeyEvent` com key codes para acentos (mais frágil).
