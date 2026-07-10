#!/usr/bin/env python
"""T-DISS data prep: download AdvBench + HarmBench standard behaviors + XSTest (benign control).

Writes a single unified working set CSV: data/prompts.csv with columns
    id, source, behavior, category
'behavior' is the harmful instruction (or benign question for XSTest).
No model / GPU used here.
"""
import csv, io, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


rows = []

# ---- AdvBench harmful_behaviors (520) from llm-attacks repo ----
advbench_url = ("https://raw.githubusercontent.com/llm-attacks/llm-attacks/main/"
                "data/advbench/harmful_behaviors.csv")
try:
    raw = fetch(advbench_url).decode("utf-8")
    rdr = csv.DictReader(io.StringIO(raw))
    n = 0
    for i, row in enumerate(rdr):
        goal = (row.get("goal") or "").strip()
        if goal:
            rows.append({"id": f"advbench_{i}", "source": "advbench",
                         "behavior": goal, "category": "harmful"})
            n += 1
    print(f"[advbench] {n} behaviors")
except Exception as e:
    print(f"[advbench] FAILED: {e}", file=sys.stderr)

# ---- HarmBench standard behaviors (400) ----
# Official CSV in HarmBench repo.
harmbench_url = ("https://raw.githubusercontent.com/centerforaisafety/HarmBench/main/"
                 "data/behavior_datasets/harmbench_behaviors_text_all.csv")
try:
    raw = fetch(harmbench_url).decode("utf-8")
    rdr = csv.DictReader(io.StringIO(raw))
    n = 0
    for i, row in enumerate(rdr):
        # keep only 'standard' functional category, no contextual (which need a context passage)
        fcat = (row.get("FunctionalCategory") or row.get("functional_category") or "").strip().lower()
        beh = (row.get("Behavior") or row.get("behavior") or "").strip()
        if not beh:
            continue
        if fcat and fcat != "standard":
            continue
        rows.append({"id": f"harmbench_{i}", "source": "harmbench",
                     "behavior": beh, "category": "harmful"})
        n += 1
    print(f"[harmbench] {n} standard behaviors")
except Exception as e:
    print(f"[harmbench] FAILED: {e}", file=sys.stderr)

# ---- XSTest benign / over-refusal control (250 safe prompts) ----
xstest_url = ("https://raw.githubusercontent.com/paul-rottger/xstest/main/"
              "xstest_prompts.csv")
try:
    raw = fetch(xstest_url).decode("utf-8")
    rdr = csv.DictReader(io.StringIO(raw))
    n = 0
    for i, row in enumerate(rdr):
        prompt = (row.get("prompt") or "").strip()
        typ = (row.get("type") or "").strip().lower()
        if not prompt:
            continue
        # 'safe' types are the benign-that-look-harmful set (contrast prompts start w/o 'contrast')
        is_safe = not typ.startswith("contrast")
        rows.append({"id": f"xstest_{i}", "source": "xstest",
                     "behavior": prompt,
                     "category": "benign" if is_safe else "harmful"})
        n += 1
    print(f"[xstest] {n} prompts")
except Exception as e:
    print(f"[xstest] FAILED: {e}", file=sys.stderr)

out = os.path.join(DATA, "prompts.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "source", "behavior", "category"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

from collections import Counter
c = Counter((r["source"], r["category"]) for r in rows)
print("=== written", out, "total", len(rows))
for k, v in sorted(c.items()):
    print("  ", k, v)
