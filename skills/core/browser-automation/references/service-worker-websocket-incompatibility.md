# Service Worker WebSocket — Incompatibilidade

**Fato:** Service Workers NÃO suportam a API `WebSocket`. O construtor `new WebSocket()` em contexto de Service Worker lança erro ou falha silenciosamente dependendo do navegador.

## Evidência
- Chrome/Brave: `new WebSocket('ws://...')` dentro de `sw.js` não estabelece conexão
- A API WebSocket requer um ambiente de execução de página (window), não de worker
- Service Workers só têm acesso a: `fetch`, `Cache`, `IndexedDB`, `Push`, `Notification`

## Soluções
1. **Manter WebSocket apenas no thread principal** (main.js ou module importado pela página)
2. **Comunicação SW ↔ página**: usar `self.clients.matchAll()` + `postMessage()` 
3. **Push notifications**: usar a API `Push` nativa do Service Worker (requer VAPID keys + backend de push)
4. **Background sync**: usar `BackgroundSync` API (limitada, não disponível em todos navegadores)

## Padrão correto
```javascript
// sw.js — NÃO usar WebSocket. Usar Push API + postMessage
self.addEventListener('push', e => {
  const data = e.data?.json() || {};
  self.registration.showNotification(data.title, { body: data.body });
});

self.addEventListener('message', async (event) => {
  // Comandos da página principal
});

// main.js — WebSocket aqui SIM
const ws = new WebSocket('ws://localhost:9877');
ws.onmessage = async (event) => {
  const data = JSON.parse(event.data);
  // Forward to SW if needed
  const reg = await navigator.serviceWorker.ready;
  reg.active?.postMessage(data);
};
```

## Pitfall
Se um Service Worker registrado tiver `new WebSocket()` no código, ele falha mas não causa erro visível na página — simplesmente não conecta. Isso pode levar a diagnósticos errados ("o WebSocket está offline") quando o problema real é que o SW nunca vai conseguir conectar.
