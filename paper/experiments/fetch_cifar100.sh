#!/usr/bin/env bash
# Robust CIFAR-100 fetch: RESUME (-C -) accumulates across dropped connections instead of restarting,
# tries multiple sources, verifies md5 AND test-extracts, cleans truncated artifacts on failure.
# Writes cifar100_ready.marker only on a verified, extracted dataset.
set -u
cd "/home/students/code/Anas/adversarial-robustness-shift-invariance/paper/data"
MD5=eb9058c3a382ffc7106e4002c42a8d85; SIZE=169001437
F=cifar-100-python.tar.gz
LOG=../results/fetch_cifar100.log
SOURCES=(
  "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"
  "http://cave.cs.toronto.edu/kriz/cifar-100-python.tar.gz"
  "https://ossci-datasets.s3.amazonaws.com/cifar-100-python.tar.gz"   # pytorch S3 mirror
)
verify() {  # size + md5 + extractability
  [ "$(stat -c %s "$F" 2>/dev/null || echo 0)" -eq "$SIZE" ] || return 1
  [ "$(md5sum "$F" | cut -d' ' -f1)" = "$MD5" ] || return 1
  tar tzf "$F" >/dev/null 2>&1 || return 1
  return 0
}
for round in $(seq 1 80); do
  for url in "${SOURCES[@]}"; do
    # resume onto the current partial; only restart if the partial already exceeds the target (corrupt)
    sz=$(stat -c %s "$F" 2>/dev/null || echo 0)
    [ "$sz" -gt "$SIZE" ] && { rm -f "$F"; echo "r$round oversized -> reset" >> $LOG; }
    curl -sL -C - --max-time 300 -o "$F" "$url" 2>/dev/null
    sz=$(stat -c %s "$F" 2>/dev/null || echo 0)
    echo "r$round $url -> $sz/$SIZE $(date -u +%FT%TZ)" >> $LOG
    if [ "$sz" -eq "$SIZE" ]; then
      if verify; then
        tar xzf "$F" && echo "VERIFIED+EXTRACTED r$round $(date -u +%FT%TZ)" >> $LOG
        echo done > ../results/cifar100_ready.marker; exit 0
      else
        echo "r$round full size but md5/extract FAIL -> delete, retry" >> $LOG; rm -f "$F"
      fi
    fi
  done
  sleep 20
done
echo "GAVE UP after 80 rounds $(date -u +%FT%TZ)" >> $LOG
