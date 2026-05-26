# gcloud Auth Flow — V569+ Remote Bootstrap

## Comportamento observado (2026-05-25)

gcloud v569.0.0 (snap) mudou o comportamento de `--no-browser`:

### Tentativa 1: `gcloud auth login --no-browser` (antigo fluxo)
```
$ gcloud auth login --no-browser
You are authorizing gcloud CLI without access to a web browser. Please run
the following command on a machine with a web browser and copy its output
back here.

gcloud auth login --remote-bootstrap="https://accounts.google.com/o/oauth2/auth?..."
```
**Resultado**: Não imprime URL visitável. Exige rodar comando remoto em máquina com browser.

### Tentativa 2: Piping do código de verificação
Usuário visitou URL, pegou código `4/0AeoWuM99Dt-...`, mas eu reiniciei o `gcloud auth login` (novo code_challenge). Código inválido: `invalid_grant: Invalid code verifier`.

**Conclusão**: PKCE code_challenge é vinculado à chamada específica. Não reutilizar códigos.

### Tentativa 3: `gcloud auth application-default login --no-browser`
Mesmo comportamento — remote-bootstrap mode.

### Tentativa 4: Rodar `--remote-bootstrap` na mesma máquina + CDP browser
- gcloud inicia servidor HTTP em `localhost:8085`
- Naveguei CDP browser (porta 9223) para URL do OAuth
- Google detectou headless Chrome: **"Esse navegador ou app pode não ser seguro"**
- Login bloqueado

### Tentativa 5: Desktop Daemon + Brave real (planejada, não executada)
Script `/tmp/gcloud_oauth_auto.py` usaria WebSocket :9876 para digitar URL no Brave real (display :0).
Não executado — depende de desktop desbloqueado + Brave rodando.

## Solução correta: Service Account Key

```bash
# 1. Criar SA no console GCP com role Editor
# 2. Baixar JSON key
# 3. Autenticar:
gcloud auth activate-service-account \
  --key-file=/caminho/para/key.json \
  --project=PROJECT_ID

# 4. Verificar:
gcloud auth list
# Deve mostrar a SA como ACTIVE
```

## Linha do tempo de falhas

| # | Método | Falha |
|---|--------|-------|
| 1 | `--no-browser` direto | Remote-bootstrap mode, sem URL |
| 2 | Pipe do código do usuário | PKCE challenge expirado |
| 3 | `application-default --no-browser` | Mesmo problema |
| 4 | Remote-bootstrap + CDP browser | Google bloqueia headless |
| 5 | Desktop Daemon script | Não testado (depende de desktop) |
| ✅ | Service account key | **Funciona headless** |
