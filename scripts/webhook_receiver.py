#!/usr/bin/env python3
"""
Webhook Receiver — recebe alertas do TradingView e executa no MT5.
Formato esperado do webhook (JSON):
{
    "pair": "EURUSD",
    "direction": "BUY",
    "entry": 1.16279,
    "sl": 1.16129,
    "tp": 1.16729,
    "fvg_pips": 5.0,
    "atr_pips": 9.5,
    "strategy": "CHoCH+FVG",
    "timestamp": "2026-05-20T14:00:00"
}
"""
import json, sys, os, time
from datetime import datetime
from pathlib import Path

# Adicionar scripts ao path
sys.path.insert(0, str(Path.home() / '.hermes' / 'scripts'))

LOG_FILE = Path.home() / '.hermes' / 'forex' / 'webhook_log.jsonl'
os.makedirs(LOG_FILE.parent, exist_ok=True)

def receive_webhook(data):
    """Processa alerta do TradingView"""
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        'timestamp': timestamp,
        'received': data
    }
    
    # Validar campos obrigatórios
    required = ['pair', 'direction', 'entry', 'sl', 'tp']
    missing = [f for f in required if f not in data]
    if missing:
        log_entry['status'] = 'rejected'
        log_entry['reason'] = f'campos faltando: {missing}'
        _log(log_entry)
        return {'status': 'rejected', 'reason': log_entry['reason']}
    
    # Normalizar
    pair = data['pair'].replace('/', '')
    direction = data['direction'].upper()
    
    # Validar direção
    if direction not in ('BUY', 'SELL', 'LONG', 'SHORT'):
        log_entry['status'] = 'rejected'
        log_entry['reason'] = f'direção inválida: {direction}'
        _log(log_entry)
        return {'status': 'rejected', 'reason': log_entry['reason']}
    
    # Normalizar direção
    if direction in ('LONG',):
        direction = 'BUY'
    elif direction in ('SHORT',):
        direction = 'SELL'
    
    try:
        from mt5_direct import place_choch_order
        
        result = place_choch_order(
            pair=pair if '/' not in pair else data['pair'],
            direction=direction,
            entry_price=float(data['entry']),
            fvg_pips=float(data.get('fvg_pips', 2.0)),
            atr_pips=float(data.get('atr_pips', 5.0))
        )
        
        log_entry['status'] = 'executed'
        log_entry['result'] = result
        _log(log_entry)
        
        return {
            'status': 'executed',
            'symbol': result.get('symbol', pair),
            'direction': direction,
            'entry': data['entry'],
            'sl': result.get('sl'),
            'tp': result.get('tp')
        }
        
    except Exception as e:
        log_entry['status'] = 'error'
        log_entry['error'] = str(e)
        _log(log_entry)
        return {'status': 'error', 'error': str(e)}

def _log(entry):
    """Log em JSON Lines"""
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ══════════════════════════════════════════
# HTTP Server (minimal, sem dependências)
# ══════════════════════════════════════════
if __name__ == '__main__':
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class WebhookHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                result = receive_webhook(data)
                self.send_response(200 if result['status'] != 'error' else 500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "invalid JSON"}')
        
        def do_GET(self):
            # Health check
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "hermes-webhook"}\n')
        
        def log_message(self, format, *args):
            pass  # Silent
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    server = HTTPServer(('127.0.0.1', port), WebhookHandler)
    print(f"🪝 Webhook receiver: http://127.0.0.1:{port}/webhook")
    print(f"   Health: http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
