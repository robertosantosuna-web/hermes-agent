---
name: whatsapp
description: "Controle do WhatsApp: Edge CDP systemd persistente (porta 9224) + bridge Python. Ler, enviar, monitorar, triagem de mensagens."
version: 1.1.0
author: Roberto Rodrigues
license: MIT
metadata:
  hermes:
    tags: [whatsapp, messaging, communication, web, desktop]
    related_skills: [life-os, executive-communication, browser-automation, architecture]
---

# WhatsApp

## VIA 1 — EDGE SYSTEMD PERSISTENTE (RECOMENDADA) 🟢

Microsoft Edge com CDP ativo como serviço systemd user. Sessão persiste entre reboots,
basta escanear o QR code UMA vez. WhatsApp Web bloqueia Brave/Chromium — Edge contorna.

**Porta CDP:** 9224 | **Perfil:** `~/.config/microsoft-edge-whatsapp`
**Serviço:** `systemctl --user <start|stop|status> whatsapp-edge`
**Template:** `templates/whatsapp-edge.service`

### Instalação
```bash
# Copiar systemd unit
cp ~/.hermes/skills/core/whatsapp/templates/whatsapp-edge.service \
   ~/.config/systemd/user/whatsapp-edge.service

# Ativar
systemctl --user daemon-reload
systemctl --user enable --now whatsapp-edge.service

# Verificar
curl -s http://localhost:9224/json/version | python3 -c "import json,sys; print(json.load(sys.stdin)['Browser'])"
# → "Edg/148.0..."
```

### Primeiro uso
1. Serviço inicia Edge apontado para `https://web.whatsapp.com`
2. Aparece QR code — **escanear com o WhatsApp do celular (1x)**
3. Sessão persiste no perfil, sobrevive a reboots

### Bridge Python (`~/scripts/whatsapp_bridge.py`)
```bash
python3 ~/scripts/whatsapp_bridge.py status    # Verificar se logado
python3 ~/scripts/whatsapp_bridge.py chats     # Listar conversas
python3 ~/scripts/whatsapp_bridge.py voice     # Extrair mensagens de voz
python3 ~/scripts/whatsapp_bridge.py send "Nome" "Mensagem"
python3 ~/scripts/whatsapp_bridge.py read "Nome"
```

### Acesso CDP direto (Python)
```python
import json, urllib.request, websocket
resp = urllib.request.urlopen('http://localhost:9224/json')
pages = json.loads(resp.read())
wa = [p for p in pages if 'whatsapp' in p['url'].lower()][0]
ws = websocket.create_connection(wa['webSocketDebuggerUrl'])

def cdp(method, params=None):
    cdp.msg_id = getattr(cdp, 'msg_id', 0) + 1
    ws.send(json.dumps({'id': cdp.msg_id, 'method': method, 'params': params or {}}))
    return json.loads(ws.recv())

# Verificar se logado ou QR code
result = cdp('Runtime.evaluate', {
    'expression': "document.body.innerText.includes('Escaneie') ? 'QR' : 'LOGGED_IN'",
    'returnByValue': True
})
```

### Extrair chats
```python
result = cdp('Runtime.evaluate', {
    'expression': """
    (function() {
        var contacts = [];
        document.querySelectorAll('span[title]').forEach(function(s) {
            var t = s.getAttribute('title');
            if (t && t.length > 2 && t.length < 60 && !contacts.includes(t))
                contacts.push(t);
        });
        return JSON.stringify(contacts);
    })()""",
    'returnByValue': True
})
chats = json.loads(result['result']['result']['value'])
```

## VIA 2 — WHATSAPP DESKTOP SNAP (fallback visual)

Aplicativo nativo snap. Usar apenas se Edge CDP não disponível.

```bash
whatsapp-desktop-linux      # Abrir
pgrep -a whatsapp            # Verificar se rodando
pkill -f whatsapp-desktop-linux  # Fechar
```

Automação visual (último recurso): mss screenshot → OCR → pynput.

## TRIAGEM DE MENSAGENS

Usar a mesma lógica do `executive-communication` (skill carregada como referência).
Regra: whatsapp delega classificação e priorização ao executive-communication.

### Prioridades (de executive-communication)
| Categoria | Ação |
|-----------|------|
| CLIENTE ATIVO | Responder <1h |
| OPORTUNIDADE | Responder <4h |
| PESSOAL IMPORTANTE | Responder no dia |
| GRUPOS | Verificar menções |
| SPAM | Ignorar/Arquivar |

### Workflow Diário
```
1. browser_navigate("https://web.whatsapp.com")
2. browser_snapshot → verificar não lidos
3. Para cada chat não lido:
   - Classificar (cliente/oportunidade/pessoal/spam)
   - Se urgente: ler mensagem completa
   - Preparar resposta
4. Reportar resumo: "3 clientes, 1 oportunidade, 5 grupos"
```

## MONITORAMENTO DE GRUPOS

Verificar menções (@Roberto) e palavras-chave (freela, vaga, projeto, orçamento).

## CRON JOB SUGERIDO

```bash
# WhatsApp Check (cada 2h, horário comercial)
# Usa whatsapp_bridge.py para listar não lidos e classificar
```

## LIMITAÇÕES

- WhatsApp Web requer QR code inicial (1x, sessão persiste no perfil Edge)
- Não há API oficial do WhatsApp (Meta bloqueia)
- Envio de arquivos via CDP é limitado
- WhatsApp Web bloqueia Brave/Chromium — usar Edge

## ANTI-PADRÕES

- NÃO usar bibliotecas não-oficiais (baileys) em conta principal — risco ban
- NÃO enviar spam ou mensagens em massa
- NÃO automatizar respostas sem revisão humana em cliente
- NÃO tentar WhatsApp Web via Brave/Chromium (bloqueado)
- NÃO usar `element.click()` em React/SPA — preferir `Input.dispatchMouseEvent`
