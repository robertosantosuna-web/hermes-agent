# Calendar Panel Fix — v38

5 correções em `index.html` para unificar controle de estado do Calendar.

## Problema

Calendar usava `classList.toggle('open')` E `style.display` em funções diferentes,
causando dessincronização: uma função setava `display:none` sem remover a classe `open`,
a próxima chamada de `toggleCalendar()` removia a classe achando que estava aberto
mas o display continuava `none`.

## Correções (v38)

### 1. togglePanel() — linha 387
```diff
-      if (cal) cal.style.display = 'none';
+      if (cal) { cal.style.display = 'none'; cal.classList.remove('open'); }
```

### 2. toggleChat() — linha 312
```diff
         document.getElementById('calendar-panel').style.display = 'none';
+        document.getElementById('calendar-panel').classList.remove('open');
```

### 3. toggleChat() — linha 317
```diff
-            document.getElementById('calendar-panel').style.display !== 'flex') {
+            !document.getElementById('calendar-panel').classList.contains('open')) {
```

### 4. toggleAuth() — linha 368
```diff
         document.getElementById('calendar-panel').style.display = 'none';
+        document.getElementById('calendar-panel').classList.remove('open');
```

### 5. toggleAuth() — linha 373
```diff
-            document.getElementById('calendar-panel').style.display !== 'flex') {
+            !document.getElementById('calendar-panel').classList.contains('open')) {
```

---

# Painel Button Fix — v39

Correção em `core/main.js` linha 129.

## Problema

`main.js` sobrescrevia `dockPainel.onclick` com `cyclePilar()` sem chamar `togglePanel()`,
impedindo que o botão Painel fechasse painéis abertos (Calendar, Chat, Auth).

## Correção (v39)

```diff
 dockPainel.onclick = () => {
+  togglePanel(); // Fecha todos os painéis (Calendar, Chat, Auth)
   const next = cyclePilar();
```
