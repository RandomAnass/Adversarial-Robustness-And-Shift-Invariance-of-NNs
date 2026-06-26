#!/usr/bin/env python3
"""Curate the calibration corpus.

  analyze         : bucket every on-topic, full-thread pulled forum by outcome and
                    print conf/year/scores/decision/title so a human can hand-pick.
  build --ids ...  : for the hand-picked forum ids, (re)render a canonical
                    {conf}_{year}_{forum}.md from raw, write reviews/records.json
                    (curated) and reviews/INDEX.md, bucketed by outcome.

Score scales differ by venue (noted in INDEX.md): ICLR 2024/2025 & NeurIPS 2023/2024
use 1-10; ICLR 2020 uses {1,3,6,8}; ICLR 2021/2022 use 1-10 (vals 1,3,5,6,8,10);
NeurIPS 2025 uses a compressed 1-6 scale. We normalize mean rating by the venue's
max to split weak-reject (near bar) from clear reject.
"""
import argparse
import glob
import json
import os
import re
import sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_calibration_reviews as F  # noqa

REV = os.path.join(HERE, "reviews")
RAW = os.path.join(REV, "raw")


def scale_max(conf, year):
    if conf == "NeurIPS" and year == "2025":
        return 6.0
    if conf == "ICLR" and year == "2020":
        return 8.0
    return 10.0


def bucket(rec):
    """Return one of: strong-accept, borderline-accept, weak-reject, reject."""
    d = (rec.get("decision") or "").lower()
    ratings = rec.get("ratings") or []
    m = mean(ratings) if ratings else None
    norm = (m / scale_max(rec["conf"], rec["year"])) if m is not None else None
    if any(w in d for w in ("oral", "spotlight")):
        return "strong-accept"
    if "accept" in d or "poster" in d:
        # an "accept" with very high scores can still be called strong
        if norm is not None and norm >= 0.78:
            return "strong-accept"
        return "borderline-accept"
    if "reject" in d or "withdraw" in d or d == "":
        if "withdraw" in d:
            return "reject"
        if norm is not None and norm >= 0.50:
            return "weak-reject"
        return "reject"
    return "reject"


def load_all():
    recs = json.load(open(os.path.join(REV, "_all_records.json")))
    return recs


def is_full(r):
    return (r.get("ontopic") and r.get("n_reviews", 0) >= 2
            and r.get("has_author_response"))


def do_analyze(_):
    recs = [r for r in load_all() if is_full(r)]
    buckets = {"strong-accept": [], "borderline-accept": [], "weak-reject": [], "reject": []}
    for r in recs:
        buckets[bucket(r)].append(r)
    for b, rows in buckets.items():
        print(f"\n========== {b}  ({len(rows)}) ==========")
        for r in sorted(rows, key=lambda x: (x["conf"], x["year"])):
            rr = "[" + ",".join(f"{x:g}" for x in (r["ratings"] or [])) + "]"
            print(f"  {r['conf']:8s}{r['year']:5s} {r['forum']:13s} {rr:20s} "
                  f"dec={r['decision']!s:20.20} | {r['title'][:60]}")


def do_build(args):
    want = set(args.ids)
    allrecs = {r["forum"]: r for r in load_all()}
    out = []
    for forum in args.ids:
        path = os.path.join(RAW, f"{forum}.json")
        if not os.path.exists(path):
            print(f"[miss] {forum} no raw"); continue
        notes = json.load(open(path)).get("notes") or []
        r = allrecs.get(forum) or {}
        conf = r.get("conf") or "NA"; year = r.get("year") or "NA"
        label = re.sub(r"[^A-Za-z0-9_.-]", "_", f"{conf}_{year}_{forum}")
        md, meta = F.render_thread(label, forum, notes)
        open(os.path.join(REV, f"{label}.md"), "w").write(md)
        # Display decision: prefer the official Decision note; otherwise derive from
        # the venue string (Withdrawn / Desk Rejected) so 'None' is never shown raw.
        decision = r.get("decision")
        venue = (r.get("venue") or "")
        if not decision:
            vl = venue.lower()
            if "withdraw" in vl:
                decision = "Withdrawn (after reviews)"
            elif "desk" in vl:
                decision = "Desk Rejected"
            else:
                decision = "Reject (no decision note)"
        rb = dict(r); rb["decision"] = decision
        rec = {"label": label, "forum": forum, "conf": meta["conf"], "year": meta["year"],
               "title": meta["title"], "n_reviews": r.get("n_reviews"),
               "ratings": r.get("ratings"), "decision": decision,
               "bucket": bucket(rb) if r else None,
               "n_rebuttal": r.get("n_rebuttal"), "n_author_comments": r.get("n_author_comments"),
               "md": f"{label}.md"}
        out.append(rec)
    json.dump(out, open(os.path.join(REV, "records.json"), "w"), indent=1)
    write_index(out)
    print(f"[build] {len(out)} curated -> records.json + INDEX.md")


BUCKET_ORDER = [
    ("strong-accept", "Strong accept / oral / spotlight"),
    ("borderline-accept", "Borderline accept / poster"),
    ("weak-reject", "Weak reject (borderline, just below bar)"),
    ("reject", "Clear/strong reject or withdrawn"),
]


def write_index(out):
    by = {}
    for r in out:
        by.setdefault(r["bucket"], []).append(r)
    lines = ["# Calibration corpus index", "",
             f"Curated full review threads: **{len(out)}** "
             "(on-topic: adversarial / certified / Lipschitz / randomized-smoothing / "
             "invariance / equivariance / anti-aliasing robustness).", "",
             "## Rating scales per venue (scores are NOT directly comparable across venues)",
             "",
             "- **ICLR 2024 / 2025**: 1-10 (values 1,3,5,6,8,10). 6 = marginal accept, 5 = marginal reject, 8 = accept.",
             "- **ICLR 2021 / 2022**: 1-10 (values 1,3,5,6,8,10). Same reading as above.",
             "- **ICLR 2020**: 1-8 (values 1,3,6,8). 6 = weak accept, 3 = weak reject.",
             "- **NeurIPS 2023 / 2024**: 1-10. 6 = weak accept, 5 = borderline, 4 = borderline reject.",
             "- **NeurIPS 2025**: compressed **1-6** scale (e.g. 5 = accept). A row of 5s here is a strong outcome, unlike a 5 on the 1-10 venues.",
             "- Decision string is taken from the venue's official Decision note (or meta-review recommendation).",
             ""]
    for b, heading in BUCKET_ORDER:
        rows = by.get(b, [])
        lines.append(f"## {heading} ({len(rows)})")
        lines.append("")
        for r in sorted(rows, key=lambda x: (x["conf"], x["year"])):
            rr = "[" + ", ".join(f"{x:g}" for x in (r["ratings"] or [])) + "]"
            lines.append(
                f"- **{r['conf']} {r['year']}** scores {rr} -> _{r['decision']}_  "
                f"([thread](./{r['md']}))  \n  {r['title']}")
        lines.append("")
    open(os.path.join(REV, "INDEX.md"), "w").write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("analyze")
    b = sub.add_parser("build")
    b.add_argument("--ids", nargs="+", required=True)
    args = ap.parse_args()
    {"analyze": do_analyze, "build": do_build}[args.mode](args)


if __name__ == "__main__":
    main()
