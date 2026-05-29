# Instagram Monitor

Módulo integrado ao Córtex Insular para monitoramento de atividade social no Instagram.

**Script:** `~/.hermes/brain/instagram_monitor.py`

## Funcionamento

Usa CDP no Brave (:9222) para acessar Instagram sem ser bloqueado por anti-bot.
Chromium headless (:9226) é detectado e bloqueado pelo Instagram — Brave é navegador real.

## Métricas coletadas

- Tempo de sessão (minutos)
- Notificações pendentes
- Mensagens diretas não lidas
- Análise de feed (posts visíveis, tipo de conteúdo)
- Frequência de acesso (sessões por dia)
- Padrão de uso (saudável/moderado/elevado/excessivo)
- Score social (0-10)

## Integração

O `cortex_insular.py` chama `instagram_monitor.analyze_social_health()` durante a análise de padrões sociais.
Resultados alimentam insights e recomendações do agente psicológico/social.

## Requisitos

- Brave rodando com CDP na porta 9222
- Instagram logado no Brave (login manual único)
- `pip install websockets`

## Pitfalls

- Instagram bloqueia Chromium headless — usar Brave ou Edge
- Login manual necessário uma vez no navegador real
- Detecção de login: verificar `body.innerText` por "Entrar no Instagram" vs navegação normal
- `document.querySelector('input[name="username"]')` não é confiável (DOM varia)
