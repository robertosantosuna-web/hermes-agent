# Freelancer Agent Pipeline (28/05/2026)

Agente autônomo unificado para trabalhos freelancer.

## Arquivo
`~/.hermes/brain/freelancer_agent.py`

## Cron
`*/30 * * * * 1-5` (a cada 30 min, segunda a sexta)

## Pipeline

1. **Email (IMAP Gmail)** — conecta em `robertosantos.una@gmail.com`, busca emails das últimas 48h de:
   - `no-reply@99freelas.com.br` → 99Freelas
   - `notifications@freelancer.com` → Freelancer.com
   - `noreply@workana.com` → Workana
   - `noreply@fiverr.com` → Fiverr

2. **Classificação** — cada email é classificado como:
   - `new_message` — cliente enviou mensagem (URGENTE)
   - `contract_won` — proposta aceita
   - `payment_received` — pagamento liberado
   - `new_project` — novo projeto disponível
   - `login_alert` — ignorado

3. **Filtro de jobs rápidos** — keywords: planilha, excel, digitação, revisão, ABNT, tradução, PDF, Word, cadastro, lista, TCC, monografia, transcrição

4. **Geração de proposta** — 6 templates por tipo de job, personalizados com nome do cliente

5. **Follow-up** — alerta se cliente não responde há >6h

6. **CDP (99Freelas)** — varredura complementar via Brave (:9222) para projetos listados na página

## Keywords ignoradas (não são jobs rápidos)
Programação, desenvolvimento, site, app, design gráfico, vídeo, marketing digital, tráfego pago, social media

## Estado
- `~/.hermes/forex/freelancer_agent_state.json` — estado geral
- `~/.hermes/forex/proposals_sent.json` — histórico de propostas
- `~/.hermes/forex/freelancer_agent.log` — log de execuções
