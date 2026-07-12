#!/bin/bash
set -e
CONDA="/opt/anaconda3/bin/conda"
echo "[setup] cloning al_selfdistill -> llmtransfer $(date)"
"$CONDA" create --clone al_selfdistill -n llmtransfer -y 2>&1 | tail -3
PY=/home/students/.conda/envs/llmtransfer/bin/python
echo "[setup] installing extras"
$PY -m pip install -q nanogcg open_clip_torch autoattack robustbench 2>&1 | tail -5
$PY -m nltk.downloader wordnet omw-1.4 2>&1 | tail -2 || true
echo "[setup] verifying core stack intact"
$PY -c "import torch,transformers,peft,open_clip,nanogcg; print('OK torch',torch.__version__,'tf',transformers.__version__,'cuda',torch.cuda.is_available(),'open_clip+nanogcg ok')"
echo "[setup] DONE $(date)"
