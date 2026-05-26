# Disk Quota Workaround — /tmp tmpfs

## Problema

`pip install` falha com:
```
ERROR: Could not install packages due to an OSError: [Errno 122] Cota da disco excedida
```

Mesmo com `df -h /` mostrando espaço livre (ex: 258G). Causa: `/tmp` é um tmpfs com
quota pequena (~3.3G) e `usrquota` ativada. Pacotes grandes (CUDA libs, ultralytics,
transformers) baixam para /tmp e estouram a quota.

## Diagnóstico

```bash
df -h /tmp
# tmpfs  3.4G  111M  3.3G  4% /tmp

mount | grep /tmp
# tmpfs on /tmp type tmpfs (...,usrquota)
```

Se `usrquota` aparece no mount: confirma o problema.

## Solução

Redirecionar TMPDIR para diretório no disco principal:

```bash
mkdir -p ~/tmp
TMPDIR=~/tmp pip install --no-cache-dir <pacotes>
```

## Limpeza pós-instalação

```bash
rm -rf ~/tmp/*
```

## Pacotes que costumam falhar (maiores)

- `ultralytics` — baixa CUDA bindings (~2GB)
- `transformers` — baixa torch (~3GB)
- `chromadb` — dependências pesadas
- `llama-cpp-python` — compila do source com CUDA

## Observação

Isso NÃO é falta de espaço em disco real. `df -h /` mostra espaço real disponível.
O tmpfs /tmp é um filesystem em RAM com tamanho fixo independente do disco.
