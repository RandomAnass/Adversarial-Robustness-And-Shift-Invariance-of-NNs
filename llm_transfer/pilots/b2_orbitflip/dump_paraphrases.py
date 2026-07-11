#!/usr/bin/env python
"""Dump a sample of model-generated paraphrases (x, paraphrase) so validate_oracle.py can
report the NLI paraphrase-validity FILTER pass-rate. Small, fast; GPU 1 only. Run after the
main run or standalone."""
import os, sys, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from b2_model import B2Model

random.seed(0)
DATA = os.path.join(HERE, "data"); RES = os.path.join(HERE, "results")


def main(n_per_fam=80, k=3):
    rows = [json.loads(l) for l in open(os.path.join(DATA, "corpus.jsonl"))]
    M = B2Model()
    out = []
    for fam in ["sentiment", "nli", "safety"]:
        fr = [r for r in rows if r["family"] == fam]
        for r in random.sample(fr, min(n_per_fam, len(fr))):
            x = r["x"]
            paras = M._paraphrases(x, k)
            for p in paras:
                out.append({"family": fam, "x": x, "para": p})
    path = os.path.join(RES, "paraphrase_cache.jsonl")
    with open(path, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(out)} (x,paraphrase) pairs -> {path}")


if __name__ == "__main__":
    main()
