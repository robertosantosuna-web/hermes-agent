#!/bin/bash
# NN Engine Daily Maintenance — 09:00 UTC
# Mantém as 3 redes neurais saudáveis: absorve, compartilha, corrige, limpa

cd /home/roberto/.hermes || exit 1

echo "=== NN Engine Daily Maintenance $(date -Iseconds) ==="

# 1. Absorb (puxa knowledge bridge → redes)
echo "[1/5] Absorbing knowledge bridge..."
python3 scripts/nn_engine.py absorb 2>&1 | tail -1

# 2. Cross-pollinate (transfere sinapses → shared)
echo "[2/5] Cross-pollinating..."
python3 scripts/nn_engine.py cross_pollinate 2>&1 | tail -1

# 3. Backprop (corrige pesos)
echo "[3/5] Backpropagation..."
python3 scripts/nn_engine.py backprop all 2>&1 | tail -3

# 4. Consolidate (mescla duplicatas)
echo "[4/5] Consolidating..."
python3 scripts/nn_engine.py consolidate all 2>&1 | tail -3

# 5. Prune (remove sinapses fracas)
echo "[5/5] Pruning..."
python3 scripts/nn_engine.py prune all 2>&1 | tail -3

# Status final
echo ""
python3 scripts/nn_engine.py status 2>&1

echo "=== Maintenance complete ==="
