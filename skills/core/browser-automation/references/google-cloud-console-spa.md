# Google Cloud Console — Angular Material SPA Patterns

## Resumo

Google Cloud Console usa Angular Material + custom components (CFC). CDP funciona para LEITURA e navegação de dropdowns, mas ações de submit (Criar, Salvar, Add Secret) são bloqueadas — Google verifica `isTrusted` do evento. Para ações finais: Desktop Daemon (ydotool) ou interação manual do usuário.

## Pipeline validado

```
CDP → ler DOM, extrair coordenadas, preencher campos (setter nativo), abrir/selecionar dropdowns
Daemon → clicar em Criar/Salvar/Add Secret, digitar senha (kernel-level input)
```

## Preencher inputs Angular Material

### Funciona: setter nativo + eventos

```javascript
var input = document.querySelector('mat-form-field input[type=text]:not([type=search])');
var setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
setter.call(input, 'MindCoach');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
input.dispatchEvent(new Event('blur', { bubbles: true }));
```

### NÃO funciona:
- `Input.dispatchKeyEvent` (Angular ignora)
- `Input.insertText` (não dispara state update)
- `element.value = "texto"` puro (sem eventos)

## Selecionar dropdowns (cfc-select)

CFC-SELECT é o dropdown customizado do Google Cloud (ex: tipo de app, email de suporte).

```javascript
// 1. Clicar no select para abrir
var select = document.querySelector('cfc-select[formcontrolname="userSupportEmail"]');
select.click();

// 2. Aguardar e selecionar opção
var options = document.querySelectorAll('mat-option');
for (var opt of options) {
    if (opt.innerText.includes('robertosantos.una@gmail.com')) {
        opt.click();
        break;
    }
}
```

## Botões de submit (Criar, Salvar, Add Secret)

**NEM TODOS são bloqueados.** O comportamento varia por página:

### Bloqueados (isTrusted check):
- **OAuth Consent Screen**: botão "Criar" no passo final
- **OAuth Client Creation**: botão "Criar" após preencher formulário
- Solução: Desktop Daemon (ydotool) ou clique manual do usuário

### Funcionam via CDP JS .click():
- **Cloud Run Security page**: botão "Salvar" após alterar radio de acesso público
- **Service Account creation**: botões "Criar e continuar", "Continuar", "Concluído"
- **API enablement**: botão "Ativar" (aria-label)
- **Service account actions menu**: "Gerenciar chaves" etc.

### Cloud Run Security — Radio buttons (caso especial)
`mat-radio-button.click()` NÃO altera o estado no GCP Console. É necessário manipular o DOM diretamente:

```javascript
// Set public radio
document.getElementById('_0rif_mat-radio-0-input').checked = true;
document.getElementById('_0rif_mat-radio-0-input').dispatchEvent(new Event('change', {bubbles: true}));
document.getElementById('_0rif_mat-radio-0').classList.add('mat-radio-checked');

// Unset restricted
document.getElementById('_0rif_mat-radio-1-input').checked = false;
document.getElementById('_0rif_mat-radio-1').classList.remove('mat-radio-checked');
```

Após essa manipulação, os botões "Cancelar" e **"Salvar"** aparecem e respondem a JS `.click()`.

## Estrutura de formulários

### OAuth Consent Screen (4 passos)
- **Passo 1**: `mat-form-field input` para nome, `cfc-select` para email
- **Passo 2**: `mat-radio-button` para Interno/Externo
- **Passo 3**: Dados de contato (auto-preenchido)
- **Passo 4**: Concluir — checkbox + botão Criar (requer interação real)

### OAuth Client Creation
- **Tipo**: `cfc-select` com opções (Web, Android, iOS, etc.)
- **Nome**: `input[type=text]`
- **URIs**: inputs dinâmicos após clicar "Adicionar URI"
- **Criar**: botão bloqueado para CDP

## Client Secret — Google não mostra mais

A partir de 2026, o Google Cloud Console não permite mais visualizar/download de secrets existentes:
- Secrets aparecem mascaradas: `****YBkB`
- Só é possível criar NOVAS secrets (Add Secret)
- O valor completo só aparece brevemente no popup de criação
- Alternativa: gcloud CLI com auth ou download no momento da criação do cliente

## Cliente criado com sucesso

Após criar, o diálogo mostra:
- Client ID completo
- Botão "Baixar o JSON" (única chance de salvar a secret)
- Se fechar sem baixar → secret fica mascarada para sempre

## Páginas importantes

| Página | URL |
|--------|-----|
| Consent OAuth | `/auth/overview?project=PROJECT` |
| Criar branding | `/auth/overview/create?project=PROJECT` |
| Lista clientes | `/auth/clients?project=PROJECT` |
| Criar cliente | `/auth/clients/create?project=PROJECT` |
| Editar cliente | `/auth/clients/CLIENT_ID?project=PROJECT` |
