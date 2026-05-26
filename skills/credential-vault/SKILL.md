---
name: credential-vault
description: "Gerenciamento seguro de credenciais, chaves API, tokens e segredos. Cofre centralizado em ~/.hermes/vault/ com busca rápida e classificação por plataforma."
version: 1.0.0
category: core
metadata:
  hermes:
    tags: [vault, credentials, secrets, security]
---

# Credential Vault

Cofre centralizado para todas as credenciais, chaves API, tokens e segredos.

## Estrutura

```
~/.hermes/vault/
├── credentials.json   # JSON estruturado com todas as credenciais
├── README.md          # Índice rápido de consulta
└── .gitignore         # vault/ inteiro no .gitignore
```

## Organização do credentials.json

Categorias:
- `google-cloud` — projetos, OAuth clients, secrets
- `google-account` — email principal
- `forex` — contas MT5, brokers
- `freelancing` — 99Freelas, Fiverr, Workana
- `microtasks` — TimeBucks, Toloka, Neevo
- `apis` — TradingView Scanner, OpenWeatherMap, etc.
- `messaging` — Telegram, WhatsApp
- `browsers` — Edge CDP, Brain Browser, Desktop Daemon

Cada entrada inclui: `label`, campos específicos da plataforma, `status`, `created`, URLs de acesso.

## Adicionar nova credencial

```bash
python3 -c "
import json
from pathlib import Path
vault = json.loads(Path.home().joinpath('.hermes/vault/credentials.json').read_text())
vault['categoria']['nova_entrada'] = {
    'label': 'Nome amigável',
    'status': 'active',
    # campos específicos
}
Path.home().joinpath('.hermes/vault/credentials.json').write_text(json.dumps(vault, indent=2, ensure_ascii=False))
"
```

## Buscar credencial

```bash
cat ~/.hermes/vault/README.md  # índice rápido
# ou
python3 -c "import json; from pathlib import Path; v=json.loads(Path.home().joinpath('.hermes/vault/credentials.json').read_text()); print(json.dumps(v['google-cloud']['mindcoach'], indent=2))"
```

## Segurança

- Arquivo NUNCA é commitado (adicionar `vault/` ao `.gitignore`)
- Secrets mascaradas quando possível (`****XXXX`)
- Nota quando secret está pendente de renovação
- Chaves de API rotuladas com escopo e data de criação
