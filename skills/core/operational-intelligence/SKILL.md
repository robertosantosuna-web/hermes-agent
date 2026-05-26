---
name: operational-intelligence
description: "Inteligência operacional: análise estratégica, priorização dinâmica, previsão operacional, detecção de risco, otimização de workflows e tomada de decisão contextual."
version: 1.0.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [strategy, analysis, prioritization, risk, optimization, decision]
    related_skills: [life-os, plan, writing-plans, system-health, freelancing-automation]
---

# Operational Intelligence

Camada de inteligência que analisa, prioriza e otimiza. Não executa — informa decisões. Usar quando enfrentar escolhas complexas, múltiplas demandas concorrentes, ou necessidade de otimizar sistema.

## MATRIZ DE PRIORIZAÇÃO

Toda demanda é classificada em 2 eixos:

```
URGÊNCIA (tempo até consequência)
  ALTA |  FAZER AGORA   |  PLANEJAR HOJE  |
       |  (emergência)   |  (importante)    |
  BAIXA|  DELEGAR/TIMER  |  BACKLOG         |
       |  (distração)     |  (futuro)        |
       +-------------------------------------
         BAIXO            ALTO
              IMPACTO (ganho potencial)
```

### Regra de Priorização
1. Alta urgência + Alto impacto → AÇÃO IMEDIATA
2. Alta urgência + Baixo impacto → Resolver rápido, não investir muito
3. Baixa urgência + Alto impacto → Planejar, bloquear tempo
4. Baixa urgência + Baixo impacto → Backlog ou descartar

## ANÁLISE ESTRATÉGICA

### Framework RACE
```
R - Resultado desejado (o que é sucesso?)
A - Abordagem (como chegar lá?)
C - Capacidade (temos recursos/tempo/skills?)
E - Externalidades (o que pode dar errado?)
```

### Tomada de Decisão
Para decisões com trade-off:
1. Listar opções (2-5)
2. Para cada: prós (3), contras (3), risco (1-5), ganho (1-5)
3. Score = (ganho * 2 - risco) / esforço estimado
4. Recomendar top 2 com justificativa
5. Roberto decide

## DETECÇÃO DE RISCO

### Sinais de Alerta
- Múltiplas tasks pendentes sem progresso → sobrecarga
- Mesmo erro repetindo → abordagem errada
- Contexto crescendo sem limpeza → degradação
- Cron jobs falhando silenciosamente → perda de monitoramento
- Memória cheia → perda de persistência
- 3+ [FALHA] seguidas → precisa intervenção

### Resposta a Risco
```
Risco Baixo (1-2): Monitorar, seguir
Risco Médio (3): Mitigar (plano B), seguir com cautela
Risco Alto (4): Reportar, sugerir alternativas, esperar confirmação
Risco Crítico (5): Bloquear ação, alertar imediatamente
```

## OTIMIZAÇÃO DE WORKFLOWS

### Análise de Gargalos
1. Onde o tempo é gasto?
2. O que pode ser paralelizado?
3. O que pode ser automatizado?
4. O que pode ser eliminado?

### Métricas de Eficiência
- Tool calls por tarefa (menos = melhor)
- Tokens gastos por resultado
- Tempo até conclusão
- Taxa de acerto (ações bem-sucedidas/total)

## PREVISÃO OPERACIONAL

### Look-Ahead (diário)
Antes de iniciar tasks:
1. Dependências: algo bloqueado esperando algo?
2. Recursos: tenho memória/tokens/timeout suficiente?
3. Conflitos: tasks competem pelo mesmo recurso?
4. Sequenciamento: ordem ótima das tasks?

### Capacity Planning
- Memória disponível: 2200 chars (monitorar % uso)
- Contexto: evitar acumular >50% com informação repetida
- Cron jobs: máximo prático ~5 ativos simultâneos
- Subagentes: máx 3 paralelos (config atual)

## TOMADA DE DECISÃO CONTEXTUAL

### Quando Autonomia Total (EXECUTAR SEM PERGUNTAR)

Ações locais, reversíveis e sem custo financeiro NUNCA devem gerar pergunta. Executar direto.

Exemplos que NÃO precisam de confirmação:
- Instalação de pacotes: `pip install`, `snap install`, `npm install -g`, `sudo apt-get install`
- Leitura, busca, análise de arquivos
- Criação/edição de skills e arquivos locais
- Start/stop de serviços locais
- Download de ferramentas solicitadas
- Testes e validações locais

Se o usuário pediu para instalar algo → instale TUDO sem perguntar item por item.
Se o usuário deu uma lista de ferramentas → processe a lista inteira em paralelo, sem confirmação.

### Quando Confirmar com Roberto
- Ação externa irreversível (post, pagamento, email para cliente)
- Decisão com impacto financeiro >R$100
- Mudança de configuração de produção
- Compra/contratação de serviço
- Primeiro uso de nova ferramenta/serviço

### Quando Perguntar (insuficiência de contexto)
- Objetivo ambíguo com múltiplas interpretações
- Falta informação crítica (credenciais, endpoint, path)
- Trade-off com preferência pessoal (estilo, formato, tom)

## ANÁLISE DE IMPACTO

### Calculadora Rápida
```
Impacto = Alcance * Profundidade * Duração

Alcance:  1=pessoal, 2=time, 3=empresa, 5=mercado
Profundidade: 1=superficial, 3=significativo, 5=transformador
Duração: 1=efêmero, 3=meses, 5=permanente

Score 1-8:   baixo impacto
Score 9-27:  médio impacto
Score 28-125: alto impacto
```

## ANTI-PADRÕES

- NÃO paralisar por análise (analysis paralysis)
- NÃO priorizar tudo como urgente
- NÃO ignorar riscos por otimismo
- NÃO otimizar prematuramente (sem dados)
- NÃO decidir pelo Roberto em matéria irreversível
