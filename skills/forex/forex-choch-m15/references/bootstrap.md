# Bootstrap — Recuperação Total

Script: `/home/roberto/bootstrap.sh`

Uso em qualquer PC novo:
```bash
bash bootstrap.sh
```

O que faz:
1. Instala dependências (python3, pip, curl, git, ydotool)
2. Clona repositório hermes-agent do GitHub
3. Configura SSH para GitHub
4. Restaura cron jobs
5. Verifica instalação

Requisitos:
- Ubuntu/Debian
- Acesso SSH ao GitHub (chave id_ed25519_github_hermes)
- Repo: git@github.com:robertosantosuna-web/hermes-agent.git
