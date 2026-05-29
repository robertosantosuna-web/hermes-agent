# AutoPilot — Monitor de Conectividade (28/05/2026)

Proteção contra instabilidade de rede: o AutoPilot pausa novas ordens quando detecta falha de conectividade, mas continua gerenciando posições já abertas (trailing stop, parcial).

## Funcionamento

A cada execução do AutoPilot (cron `*/3 * * * * 1-5`), ANTES de qualquer scan de entrada:

1. **Ping** em 2 hosts (Google DNS 8.8.8.8 + Cloudflare 1.1.1.1), timeout 3s cada
2. **MT5 bridge check**: verifica se `hermes_resp.json` foi atualizado nos últimos 30s
3. **Pelo menos 1 ping OK + MT5 bridge fresco** = rede OK
4. **2 falhas consecutivas** → pausa novas ordens + alerta crítico no Tálamo
5. **5 verificações estáveis consecutivas** → retoma automaticamente

## Estado

Salvo em `~/.hermes/forex/connectivity_state.json`:

```json
{
  "status": "normal|paused|unknown",
  "consecutive_failures": 0,
  "consecutive_successes": 5,
  "paused_since": null,
  "history": [...]
}
```

## Código

Implementado em `~/.hermes/brain/autopilot.py`:

- `check_connectivity()` — pings + MT5 bridge check
- `update_connectivity()` — atualiza estado, decide pausa/retoma
- `is_trading_paused()` — consulta rápida sem side effects
- `load_connectivity_state()` / `save_connectivity_state()` — persistência

## Integração em main()

```python
def main():
    if is_cooldown():
        return
    
    # 0. Conectividade (antes de qualquer scan)
    net_ok, net_state = update_connectivity()
    trading_paused = not net_ok
    
    if trading_paused:
        print("🔴 Rede instável — novas ordens BLOQUEADAS")
        # Continua monitorando posições existentes
    
    # 1. Ler MT5, gerenciar posições existentes, etc.
```

## Comportamento durante pausa

- **NOVAS ORDENS**: BLOQUEADAS (scan de entrada é pulado)
- **POSIÇÕES EXISTENTES**: Continuam sendo gerenciadas (trailing stop, parcial, close por perda)
- **ALERTAS**: Publicados no Tálamo (prioridade 10) para visibilidade
- **RECUPERAÇÃO**: Automática após 5 checks estáveis consecutivos (~15 min com cron de 3min)
