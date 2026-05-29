# Critical Review Framework — Auto-Análise de Arquitetura

Metodologia aplicada ao agente Forex e Freelancer. Validada 28-29/05/2026.

## When to Run

Após completar arquitetura de um novo agente, ANTES de colocar em produção.

## Review Dimensions

### 1. Falhas Estruturais (onde vai quebrar?)
- Single points of failure (ex: dependência do CDP Brave para 99Freelas)
- Cascata de erros (3 serviços falham ao mesmo tempo → 3 alertas redundantes)
- Dependências externas não monitoradas (Brave fecha, porta muda)

### 2. Bugs Conceituais
- Cold start: sistema começa com 0 dados, sem priorização
- Feedback binário: template 9% = deprecado, 11% = ativo (diferença de 2%)
- Classificação excludente: job multi-categoria recebe 1 label
- Sem causa de falha: registra "perdeu" mas não sabe por quê

### 3. Vulnerabilidades de Detecção
- value setter + dispatchEvent NÃO dispara handlers React → plataforma detecta
- Timing previsível → assinatura de bot
- Mesmo IP para todas as ações → padrão detectável

### 4. Ferramentas Faltando
- Validação de entrega antes de enviar
- Backup de propostas
- Rate limiter por plataforma
- Detector de shadowban
- Gestão de identidade (se tomar ban, perde tudo)
- Dry-run de proposta
- Log de auditoria completo
- Circuit breaker por plataforma

## Fix Priority Matrix

```
CRÍTICO (AGORA):
  Healthcheck de dependências
  Delay randômico anti-detecção
  Keywords expandidas + negação
  Rate limiter

ALTO (ESTA SEMANA):
  Decay temporal no replay buffer
  Pesos iniciais empíricos (cold start)
  Feedback negativo categorizado
  Input char-by-char

MÉDIO (ESTE MÊS):
  Multi-label classification
  Depreciação gradual de templates
  Validação de entrega
  Detector de shadowban
```

## Output

Salvar em `<dominio>/REVISAO_CRITICA_<dominio>.md` com:
- Lista numerada de falhas (com RISCO: ALTO/MÉDIO/BAIXO)
- Bugs conceituais com FIX proposto
- Vulnerabilidades com FIX proposto
- Ferramentas faltando
- Matriz de prioridade
