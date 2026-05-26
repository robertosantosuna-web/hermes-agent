# TMPFS Quota Workaround

## Problema
/tmp pode ser montado como tmpfs com `usrquota` (ex: 3.3G em sistema com 6.6G RAM).
Instalações pip de pacotes pesados (ultralytics, transformers, chromadb, lancedb) 
baixam bibliotecas CUDA (nvidia-cublas 423MB, nvidia-cusolver 200MB, etc.) que 
estouram a quota do /tmp mesmo com disco livre em /home.

Erro: `OSError(122, 'Cota da disco excedida')` / `EDQUOT`

## Solução
```bash
mkdir -p ~/tmp
TMPDIR=~/tmp pip install --break-system-packages --no-cache-dir <pacotes>
```

## Verificação
```bash
df -h /tmp
mount | grep /tmp  # procura por 'usrquota'
```

## Pacotes afetados
- ultralytics (YOLO + CUDA dependencies)
- transformers (PyTorch + CUDA)
- chromadb (onnxruntime + dependências)
- lancedb (pyarrow, polars)
