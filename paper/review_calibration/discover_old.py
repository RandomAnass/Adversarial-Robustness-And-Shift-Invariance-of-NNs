#!/usr/bin/env python3
"""Strict older-year (2020-2022) discovery: list a venue's submissions and keep only
papers whose TITLE clearly signals our topic (adversarial / certified / Lipschitz /
randomized smoothing / equivariance / anti-aliasing / invariance-robustness). Writes
reviews/candidates_old.json (separate file; does NOT touch candidates.json)."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_calibration_reviews as F  # noqa

# Title must contain at least one of these to count as on-topic. Tight on purpose:
# avoids "distribution shift", "machine translation", generic "robust optimization".
STRICT = [
    "adversarial", "certified", "certifiable", "certify", "lipschitz",
    "randomized smoothing", "equivarian", "equivariant", "anti-alias", "antialias",
    "anti aliasing", "provably robust", "provable defense", "provable robustness",
    "robustness verification", "verified robust", "shift-invarian", "shift invarian",
    "translation-invarian", "translation invarian", "rotation-invarian",
    "rotation invarian", "group-invarian", "group invarian", "group equivarian",
    "spatial transform", "smoothed classifier", "robust generalization",
    "adversarial training", "adversarial example", "adversarial robust",
    "perturbation", "robust accuracy",
]
# Drop obvious false positives even if a STRICT word appears.
NEG = ["machine translation", "distribution shift", "covariate shift", "domain shift",
       "red teaming", "language model", "reinforcement learning"]

VENUES = [
    "ICLR.cc/2020/Conference",
    "ICLR.cc/2021/Conference",
    "ICLR.cc/2022/Conference",
    "NeurIPS.cc/2022/Conference",
]


def main():
    cands = {}
    for vid in VENUES:
        print(f"[venue] {vid}")
        base, inv, notes = F.list_venue_submissions(vid)
        print(f"   -> {len(notes)} submissions via {inv} ({base})")
        kept = 0
        for n in notes:
            c = F.get_content(n)
            title = str(c.get("title", "") or "")
            tl = title.lower()
            if not any(k in tl for k in STRICT):
                continue
            if any(k in tl for k in NEG):
                continue
            fid = n.get("forum") or n.get("id")
            conf, year, venue = F.venue_year(n)
            if fid and fid not in cands:
                cands[fid] = {"forum": fid, "title": title[:140], "conf": conf,
                              "year": year, "venue": venue, "query": f"venue:{vid}"}
                kept += 1
        print(f"   kept {kept} on-topic by title")
    out = os.path.join(HERE, "reviews", "candidates_old.json")
    json.dump(list(cands.values()), open(out, "w"), indent=1)
    print(f"\n[done] {len(cands)} older on-topic candidates -> {out}")
    for c in sorted(cands.values(), key=lambda x: (x["conf"], x["year"], x["title"])):
        print(f"  {c['conf']:8s} {c['year']:4s} {c['forum']:14s} {c['title'][:75]}")


if __name__ == "__main__":
    main()
