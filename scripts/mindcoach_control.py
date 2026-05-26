#!/usr/bin/env python3
"""
Hermes → MindCoach Control
Script que eu (Hermes Agent) chamo para controlar o app remotamente.

Uso:
  python3 mindcoach_control.py render dashboard
  python3 mindcoach_control.py update_pilar financeiro '{"saldo":"R$ 1.234","receitas":3}'
  python3 mindcoach_control.py alerta "Forex Alert" "EURUSD sinal BUY" warn
  python3 mindcoach_control.py theme '{"accent":"#ff6b6b","bg":"#1a0a0a"}'
  python3 mindcoach_control.py bubble "🔥" true "Sinal de trade!"
  python3 mindcoach_control.py chat '[{"role":"hermes","texto":"Olá! Seu humor parece baixo hoje."}]'
  python3 mindcoach_control.py analysis "Diagnóstico TCC: ansiedade elevada..."
  python3 mindcoach_control.py goals '[{"titulo":"Economizar R$1k","progresso":30}]'
  python3 mindcoach_control.py update_app v2
"""
import json, sys, asyncio, websockets

WS_URL = 'ws://127.0.0.1:9877'

COMMANDS = {
    'render': lambda args: {'type': 'render', 'screen': args[0] if args else 'dashboard'},
    'update_pilar': lambda args: {'type': 'update_pilar', 'pilar': args[0], 'dados': json.loads(args[1])},
    'alerta': lambda args: {'type': 'alerta', 'titulo': args[0], 'msg': args[1] if len(args)>1 else '', 'tipo': args[2] if len(args)>2 else 'info'},
    'theme': lambda args: {'type': 'theme', 'theme': json.loads(args[0])},
    'bubble': lambda args: {'type': 'bubble', 'emoji': args[0], 'alert': args[1]=='true' if len(args)>1 else False, 'text': args[2] if len(args)>2 else ''},
    'chat': lambda args: {'type': 'chat', 'mensagens': json.loads(args[0])},
    'analysis': lambda args: {'type': 'analysis', 'diagnostico': args[0], 'plano_acao': json.loads(args[1]) if len(args)>1 else []},
    'goals': lambda args: {'type': 'goals', 'metas': json.loads(args[0])},
    'update_app': lambda args: {
        'type': 'update_app',
        'version': int(args[0].replace('v','')) if args else 2,
        'files': {
            '/index.html': open('/home/roberto/.hermes/mindcoach-pro/index.html').read(),
            '/core/main.js': open('/home/roberto/.hermes/mindcoach-pro/core/main.js').read(),
            '/sw.js': open('/home/roberto/.hermes/mindcoach-pro/sw.js').read(),
        }
    },
}

async def send(cmd):
    try:
        async with websockets.connect(WS_URL) as ws:
            # Descartar estado inicial enviado pelo bridge
            await asyncio.wait_for(ws.recv(), timeout=2)
            # Enviar comando
            await ws.send(json.dumps(cmd))
            # Aguardar resposta real
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            print(json.dumps(json.loads(resp), indent=2))
    except asyncio.TimeoutError:
        print('Timeout')
    except Exception as e:
        print(f'Erro: {e}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd_name = sys.argv[1]
    cmd_args = sys.argv[2:]
    
    if cmd_name not in COMMANDS:
        print(f'Comando desconhecido: {cmd_name}')
        print(f'Disponíveis: {", ".join(COMMANDS.keys())}')
        sys.exit(1)
    
    cmd = COMMANDS[cmd_name](cmd_args)
    asyncio.run(send(cmd))
