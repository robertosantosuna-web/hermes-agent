# MT5 Vision OCR — Test Notes (2026-05-20)

## Environment
- MT5 OANDA Demo 1715539800 rodando em Wine + Xvfb :99
- Tela 1280x720, sem window manager
- Tesseract 5, idiomas por+eng

## Test 1: Tela cheia (Xvfb root)
```
Comando: vision_engine.py xvfb
Confiança: 95%
Texto: "Arquivo Pesquisa Exibir Fesramentas Janela Ajuda\n\n2 Olefeal - |..."
Resultado: Menu bar capturado (~60% precisão). Dados de gráfico e tabela ilegíveis.
```

## Test 2: Região inferior (conta)
```
Comando: vision_engine.py xvfb_region --region 0,880,1920,200 --numbers-only
Resultado: A extrair - região de saldo/equity/margem
```

## Test 3: Janela de ordem (F9)
```
Comando: F9 enviado via xdotool, screenshot, OCR
Resultado: OCR não detectou campos da janela de ordem. Fonte muito pequena.
```

## Conclusão
OCR no MT5 é viável para verificação de estado (está logado? tem ordens?),
mas NÃO para extração de dados numéricos precisos (preços, P&L).
Para dados de trading, usar Yahoo Finance API ou TradingView.
