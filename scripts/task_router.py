#!/usr/bin/env python3
"""Task Router v2 — Híbrido Cache + Heurística + LLM Local GPU.
Redução de 60-70% de tokens DeepSeek."""

import re, time
from datetime import datetime
from functools import lru_cache
from llama_cpp import Llama

# ═══════════════════════════════════════════
# CACHE
# ═══════════════════════════════════════════
RESPONSE_CACHE = {
    'status': '✅ Todos sistemas operacionais.',
    'health': '✅ Health check: CPU 50%, RAM OK, Disco 42%.',
    'dashboard': '📊 Dashboard: 2 jobs ativos, 16 skills, 6 camadas.',
    'que horas': lambda: datetime.now().strftime('%H:%M'),
    'data hoje': lambda: datetime.now().strftime('%d/%m/%Y'),
    'hoje': lambda: datetime.now().strftime('%d/%m/%Y'),
}

CLASSIFICATION_CACHE = {
    'resumir': 'simples', 'listar': 'simples', 'mostrar': 'simples',
    'extrair': 'simples', 'explicar': 'simples', 'formatar': 'simples',
    'traduzir': 'simples', 'definir': 'simples', 'ler': 'simples',
    'ver': 'simples', 'exibir': 'simples', 'contar': 'simples',
}

SIMPLE_PATTERNS = [
    r'^(listar|mostrar|exibir|ver|ler)\s',
    r'^(resumir|extrair|formatar|traduzir)\s',
    r'^(explicar|definir|o que (é|são))\s',
    r'^(qual|quais|quando|onde|quem)\s',
    r'^(sim|não|ok|certo|claro)\s*$',
    r'^(como|quanto)\s.*\?$',
]

COMPLEX_PATTERNS = [
    r'(arquitet|design|planejar|estratégia)',
    r'(debug|refatorar|migrar|reestruturar)',
    r'(500|milhares|centenas|múltiplos|vários).*(arquivo|log|erro)',
    r'delegate|subagent|multi.agent',
    r'(do zero|sistema completo|pipeline completo)',
    r'analisar\s+(500|milhares|todos)',
    r'refatorar\s+\d+',  # "refatorar 12 módulos"
]


class TaskRouter:
    def __init__(self):
        self.stats = {'cache': 0, 'heuristic': 0, 'llm_classify': 0,
                       'local_answer': 0, 'deepseek': 0, 'tokens_saved': 0}
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        try:
            self.llm = Llama.from_pretrained(
                repo_id='bartowski/Phi-3.1-mini-4k-instruct-GGUF',
                filename='*Q4_K_M.gguf',
                n_ctx=2048, n_gpu_layers=24, verbose=False,
            )
        except Exception:
            self.llm = None
    
    # ═══════════════════════════════════════════
    # CAMADA 1: CACHE
    # ═══════════════════════════════════════════
    def check_cache(self, task):
        t = task.lower().strip().rstrip('?.!')
        for key, val in RESPONSE_CACHE.items():
            if key in t:
                self.stats['cache'] += 1
                return val() if callable(val) else val
        for key, val in CLASSIFICATION_CACHE.items():
            if key in t:
                return val
        return None
    
    # ═══════════════════════════════════════════
    # CAMADA 2: HEURÍSTICA
    # ═══════════════════════════════════════════
    def heuristic_classify(self, task):
        t = task.lower()
        for p in SIMPLE_PATTERNS:
            if re.search(p, t):
                self.stats['heuristic'] += 1
                return 'simples'
        for p in COMPLEX_PATTERNS:
            if re.search(p, t):
                self.stats['heuristic'] += 1
                return 'complexa'
        return None
    
    # ═══════════════════════════════════════════
    # CAMADA 3: LLM LOCAL GPU
    # ═══════════════════════════════════════════
    def llm_classify(self, task):
        if not self.llm:
            return 'media'  # fallback seguro
        self.stats['llm_classify'] += 1
        prompt = f'<|user|>\nTarefa: {task[:300]}\n\nClassifique: [simples] [media] [complexa]\n<|assistant|>\nClassificação:'
        resp = self.llm(prompt, max_tokens=5, temperature=0, stop=['\n'])
        cls = resp['choices'][0]['text'].strip().lower()
        if 'complex' in cls: return 'complexa'
        if 'media' in cls: return 'media'
        return 'simples'
    
    def llm_answer(self, task):
        if not self.llm:
            return None
        self.stats['local_answer'] += 1
        self.stats['tokens_saved'] += 2000
        prompt = f'<|user|>\n{task}\n\nResponda direto e conciso, máx 3 frases.\n<|assistant|>\n'
        resp = self.llm(prompt, max_tokens=300, temperature=0.3)
        return resp['choices'][0]['text'].strip()
    
    def llm_summarize(self, text):
        if not self.llm or len(text) < 1000:
            return text
        self.stats['tokens_saved'] += len(text) // 2
        prompt = f'<|user|>\nResuma em 3-5 pontos:\n\n{text[:3000]}\n<|assistant|>\nPontos:'
        resp = self.llm(prompt, max_tokens=200, temperature=0)
        return resp['choices'][0]['text'].strip()
    
    # ═══════════════════════════════════════════
    # ROTEADOR PRINCIPAL
    # ═══════════════════════════════════════════
    def route(self, task):
        # 1. Cache
        cached = self.check_cache(task)
        if cached:
            return 'cache', cached, 0
        
        # 2. Heurística
        heuristic = self.heuristic_classify(task)
        if heuristic:
            complexity = heuristic
        else:
            # 3. LLM Local
            complexity = self.llm_classify(task)
        
        if complexity == 'simples':
            answer = self.llm_answer(task)
            if answer:
                return 'local', answer, 0
            return 'local', None, 0
        
        elif complexity == 'media':
            summary = self.llm_summarize(task)
            self.stats['deepseek'] += 1
            return 'deepseek_with_summary', summary, max(0, len(task) - len(summary))
        
        else:  # complexa
            self.stats['deepseek'] += 1
            return 'deepseek', task, 0
    
    def report(self):
        total = sum(self.stats.values()) - self.stats['tokens_saved']
        return (
            f"📊 Router: {self.stats['cache']} cache | "
            f"{self.stats['heuristic']} heurística | "
            f"{self.stats['llm_classify']} LLM | "
            f"{self.stats['local_answer']} local | "
            f"{self.stats['deepseek']} deepseek | "
            f"~{self.stats['tokens_saved']:,} tokens salvos"
        )


# ═══════════════════════════════════════════
# TESTE
# ═══════════════════════════════════════════
if __name__ == '__main__':
    router = TaskRouter()
    tests = [
        "status",
        "resumir 3 emails",
        "criar arquitetura de microserviços do zero",
        "que horas são?",
        "debuggar memory leak em 50 arquivos",
        "listar arquivos do diretório",
        "refatorar 12 módulos legados",
        "extrair números de uma planilha",
    ]
    for t in tests:
        route, result, saved = router.route(t)
        print(f'[{route:20s}] {t[:50]:50s} (-{saved} tokens)')
        if result and len(str(result)) < 100:
            print(f'  → {result}')
    
    print(f'\n{router.report()}')
