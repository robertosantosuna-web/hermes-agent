# Batch Cleanup — Lições Aprendidas

## Incidente: 2026-05-17 — 99Freelas deletado

**Erro:** Filtro genérico `no-reply@` capturou `no-reply@99freelas.com.br` durante limpeza em massa de emails. 559 emails do 99Freelas foram marcados como deletados e expurgados permanentemente via `mail.expunge()`.

**Causa raiz:** 
1. WHITELIST não foi verificada antes da limpeza
2. Padrão `no-reply@` é genérico demais — cobre plataformas legítimas de freelancing
3. `expunge()` foi chamado sem revisão humana do que seria removido

**Dados recuperados via Telegram:** O histórico da conversa "Entidade" no Telegram continha todos os dados de projetos e propostas do 99Freelas. Os projetos continuam ativos na plataforma — só as notificações de email foram perdidas.

## Processo Seguro (versão corrigida)

```python
# NUNCA fazer isso:
TRASH = ['noreply@', 'no-reply@']  # ❌ genérico demais!

# SEMPRE fazer isso:
WHITELIST = [
    '99freelas.com.br', 'fiverr.com', 'workana.com',  # Plataformas freelance
    'github.com', 'gitlab.com',                         # Dev
    'paypal.com', 'picpay.com', 'nubank.com.br',        # Financeiro
    'accounts.google.com',                              # Segurança
]

TRASH = []  # Só preencher depois de verificar WHITELIST

# Para cada possível padrão de lixo:
for pattern in candidate_patterns:
    if any(w in pattern for w in WHITELIST):
        print(f'⚠️  PULADO (whitelist): {pattern}')
        continue
    TRASH.append(pattern)

# Depois de deletar, NUNCA expunge() sem revisar
# mail.expunge() é permanente — usar só com confirmação explícita
```

## Checklist antes de limpeza em massa
1. [ ] Listar remetentes primeiro — NÃO deletar
2. [ ] Separar WHITELIST (ver acima) dos candidatos a TRASH
3. [ ] Revisar manualmente remetentes com >50 emails
4. [ ] Confirmar com usuário antes de expunge()
5. [ ] NUNCA usar `no-reply@` como padrão genérico
