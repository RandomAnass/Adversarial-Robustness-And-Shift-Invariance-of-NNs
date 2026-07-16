#!/bin/bash
# Sleep for an IP-level Google Drive cooldown (no requests), then run the
# gentle downloader. Meant to be launched detached via setsid.
cd /home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/pilots/c1_tower/robustbench_val
COOLDOWN="${1:-2400}"   # seconds, default 40 min
echo "[$(date)] cooldown start: sleeping ${COOLDOWN}s (no gdrive requests)" >> downloader.log
sleep "$COOLDOWN"
echo "[$(date)] cooldown done: starting gentle downloader" >> downloader.log
PYTHONNOUSERSITE=1 /home/students/code/Anas/adversarial-robustness-shift-invariance/paper/env/cenv/bin/python download_models.py 5 >> downloader.log 2>&1
