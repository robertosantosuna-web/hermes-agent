# GPU Setup — llama-cpp CUDA

Receita completa para ativar aceleração CUDA no llama-cpp-python.

## Hardware

- GPU: NVIDIA GeForce GTX 1650 Mobile (4GB VRAM)
- Driver: 595.58.03
- CUDA: 13.2 (driver), 12.4 (toolkit/nvcc)

## Instalação

### Passo 1: Toolkit CUDA

```bash
sudo apt-get install -y nvidia-cuda-toolkit
which nvcc  # /usr/bin/nvcc
```

### Passo 2: Recompilar llama-cpp-python

```bash
# /tmp pode ser tmpfs pequeno (quota). Usar ~/tmp:
mkdir -p ~/tmp

CMAKE_ARGS="-DGGML_CUDA=on" TMPDIR=~/tmp \
  pip install --break-system-packages --force-reinstall --no-cache-dir llama-cpp-python
```

Tempo: ~8-10 minutos (compila kernels CUDA do zero).

### Passo 3: Carregar modelo com GPU

```python
from llama_cpp import Llama

llm = Llama.from_pretrained(
    repo_id='bartowski/Phi-3.1-mini-4k-instruct-GGUF',
    filename='*Q4_K_M.gguf',
    n_ctx=2048,        # contexto reduzido para caber
    n_gpu_layers=24,   # 24/33 layers na GPU (~2.4GB VRAM)
)
```

## VRAM Tuning

| n_gpu_layers | VRAM usado | Status |
|-------------|-----------|--------|
| 0 (CPU) | 0 GB | Funciona |
| 24 | ~2.4 GB | Funciona ✅ |
| 33 | ~3.0 GB | Funciona (justo) |
| 99 (todas) | — | QUEBRA ("Failed to create llama_context") |

**Regra**: n_gpu_layers=99 tenta offload total e falha se VRAM < tamanho modelo + contexto.
Para GTX 1650 4GB: máximo seguro é 24 layers com n_ctx=2048.

## Verificação

```bash
python3 -c "
from llama_cpp import Llama
llm = Llama.from_pretrained(
    'bartowski/Phi-3.1-mini-4k-instruct-GGUF',
    filename='*Q4_K_M.gguf',
    n_gpu_layers=24, n_ctx=2048, verbose=False
)
resp = llm('2+2=', max_tokens=5, temperature=0)
print('OK:', resp['choices'][0]['text'].strip())
"

nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
# Output: 2434 MiB, 4096 MiB
```
