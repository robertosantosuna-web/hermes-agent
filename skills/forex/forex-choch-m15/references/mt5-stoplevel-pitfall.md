# ☠️ PITFALL: SL ignorado pelo broker (STOPLEVEL)

## Sintoma
- Ordens executadas com sucesso (retcode 10009)
- SL e TP configurados no OrderSend
- Mas posições perdem 5-14x mais que o SL configurado
- Ex: SL=3.5p, perda real=27.6p (7.9x)

## Causa
Todo broker forex tem um `SYMBOL_TRADE_STOPS_LEVEL` (STOPLEVEL) — distância mínima
entre o preço de entrada e os níveis de SL/TP.

IC Markets demo: STOPLEVEL ≈ 8-10 pips (varia por par).

Se o SL configurado for menor que o STOPLEVEL, o MT5 **rejeita o stop silenciosamente**.
A ordem abre, mas SEM stop loss. O resultado é que a posição fica nua e a perda
é o movimento total do mercado, não o limitado pelo SL.

## Solução no EA (MQL5)
```cpp
long stoplevel = SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL);
double min_distance = stoplevel * point;
if(sl > 0 && MathAbs(entry_price - sl) < min_distance * 1.5) {
    // REJEITAR — SL muito próximo
    return error;
}
```

## Solução no Bot (Python)
```python
MIN_SL_PIPS = 15  # Bem acima de qualquer STOPLEVEL
```

NUNCA usar SL < 15 pips em forex. O backtest pode mostrar SL=3p funcionando,
mas no mercado real o broker rejeita.

## Verificação
Para confirmar se SL está sendo respeitado, comparar `exit_price` com `sl` no trade_log.
Se `abs(exit - sl) > 2 * sl_pips`, o SL não foi executado.

## Data: 2026-05-26
Descoberto após 7 trades com -55 pips de loss quando o SL deveria ter limitado a ~25 pips.
