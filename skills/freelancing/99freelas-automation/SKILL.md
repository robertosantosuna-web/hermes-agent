---
name: 99freelas-automation
description: "Automação do 99Freelas via Desktop Daemon + ydotool. Contorna Cloudflare Turnstile e React controlled components usando input kernel-level."
version: 1.0.0
---

# 99Freelas Automation — Pipeline Validado

## Regra de Ouro

**CDP FUNCIONA para envio de mensagens no 99Freelas** (validado 25/05/2026). O segredo é:
1. **Preencher textarea via native setter + input event** (mantém acentos)
2. **Clicar botões via `Input.dispatchMouseEvent`** (funciona se o botão estiver visível)
3. **NUNCA usar `textarea.value = "..."` puro** — React ignora. Sempre disparar `new Event('input', {bubbles: true})` após setar.

**Desktop Daemon + ydotool é fallback** quando a janela está visível no display.

## Pipeline Primário: CDP (validado 25/05)

```python
# FASE 1: Preencher textarea (native setter + input event)
cdp('Runtime.evaluate', {'expression': '''
  (() => {
    const ta = [...document.querySelectorAll('textarea.send-message-textarea')]
      .find(t => t.getBoundingClientRect().width > 0);
    const ns = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    ns.call(ta, MSG);
    ta.dispatchEvent(new Event('input', {bubbles: true}));
    ta.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok';
  })()
'''})

# FASE 2: Clicar Enviar (Input.dispatchMouseEvent)
coords = getButtonCoords('Enviar')
cdp('Input.dispatchMouseEvent', {type:'mousePressed', x:coords.x, y:coords.y, button:'left', clickCount:1})
cdp('Input.dispatchMouseEvent', {type:'mouseReleased', x:coords.x, y:coords.y, button:'left', clickCount:1})

# FASE 3: Verificar (textarea limpa = enviado)
check = cdp('Runtime.evaluate', {
  'expression': 'document.querySelector("textarea.send-message-textarea")?.value?.length === 0 ? "SENT" : "NOT SENT"'
})
```

### ⚠️ Textarea CORRETO
99Freelas tem 5 textareas. O visível é SEMPRE o índice 1:
- Classe: `send-message-textarea elastic-textarea`
- Placeholder: `Escreva sua mensagem`
- NUNCA usar `document.querySelector('textarea')` (retorna índice 0, 0×0)
- SEMPRE filtrar: `.find(t => t.getBoundingClientRect().width > 0)`

### Concluir Projeto
```python
# 1. Navegar para página do projeto (link no header, /p/ID → redireciona)
# 2. Clicar "Concluir Projeto" (btn green clickable, ~182×62)
# 3. Confirmar modal — clicar "Sim" (~80×39)
# 4. Verificar — texto "Avaliação" indica sucesso
```

## Pipeline Fallback: Desktop Daemon (ydotool)

## Coordenadas

Tela 1920x1080 (monitor único donde Brave está). Brave Wayland na porta 9222.

**Obter coordenadas absolutas:**
```js
const rect = element.getBoundingClientRect();
const absX = Math.round(rect.left + window.screenX + rect.width/2);
const absY = Math.round(rect.top + window.screenY + rect.height/2);
```

⚠️ `mss` no daemon reporta 3840 (dois monitores), mas o navegador está em 1920.

## Digitação ABNT2-safe

ydotool com ABNT2 corrompe: `ç ã é í ó ú ê ô à õ / :`

**Solução:** Mensagens em ASCII puro. Substituir acentos por equivalentes sem acento.

## Anexar Arquivos

```python
# 1. Daemon: clicar "Anexar Arquivo(s)"
# 2. CDP DOM.setFileInputFiles no input[type="file"]
# 3. CDP: dispatchEvent(new Event('change', {bubbles: true}))
# 4. Arquivo é enviado junto com a próxima mensagem
```

## Verificação

Após cada ação, verificar via CDP `document.body.innerText`.

## Pitfalls (atualizado 25/05)

1. ✅ `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set` + `dispatchEvent(new Event('input'))` → React reconhece
2. ✅ `Input.dispatchMouseEvent` → Funciona para clicar botões visíveis
3. ❌ `textarea.value = "..."` puro → React ignora (sem evento)
4. ❌ `Input.insertText` → React ignora
5. ❌ `navigator.clipboard.writeText` → requer user gesture
6. ⚠️ `Input.dispatchKeyEvent` char-by-char → Funciona mas perde acentos
7. ⚠️ `element.click()` → ~20% de sucesso (React pode ignorar)
8. ⚠️ Desktop Daemon → Funciona mas requer janela visível no display
9. 🔑 Textarea #0 sempre é 0×0 — filtrar por `.getBoundingClientRect().width > 0`
10. 🔑 Sempre verificar envio: textarea limpa após sucesso

## Fluxo Típico

```python
# 1. CDP: verificar estado e pegar coordenadas
coords = cdp_eval('getBoundingClientRect + window.screenX/Y')

# 2. Daemon: clicar no textarea
daemon.click(tax, tay)

# 3. Daemon: digitar (ASCII puro)
daemon.type("Mensagem sem acentos")

# 4. Daemon: clicar Enviar
daemon.click(btnx, btny)

# 5. CDP: verificar
assert 'minha mensagem' in cdp_eval('document.body.innerText')
```
