#!/usr/bin/env python3
"""Rebuild a master records list directly from every pulled reviews/raw/<forum>.json,
so we never lose data when `pull` overwrites records.json. Also counts rebuttals and
author-comment rounds (for the 'full thread' completeness gate) and flags on-topic.

Writes reviews/_all_records.json (every pulled forum, with derived fields).
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_calibration_reviews as F  # noqa

RAW = os.path.join(HERE, "reviews", "raw")

ONTOPIC = ["robust", "adversarial", "invarian", "equivarian", "certif", "lipschitz",
           "smoothing", "alias", "shift", "translation", "perturbation", "margin",
           "rotation", "spatial transform", "equivar"]


def author_signed(note):
    return any("Author" in s for s in (note.get("signatures") or []))


def derive(forum_id, notes):
    sub = next((n for n in notes if F.note_kind(n) == "submission"), None)
    title = conf = year = venue = ""
    abstract = ""
    if sub:
        c = F.get_content(sub)
        title = str(c.get("title", "") or "")
        abstract = str(c.get("abstract", "") or "")
        conf, year, venue = F.venue_year(sub)
    ratings, decision = F.extract_scores(notes)
    kinds = {}
    n_author_comments = 0
    for n in notes:
        if n is sub:
            continue
        k = F.note_kind(n)
        kinds[k] = kinds.get(k, 0) + 1
        if k == "official_comment" and author_signed(n):
            n_author_comments += 1
    n_rev = kinds.get("official_review", 0)
    blob = (title + " " + abstract).lower()
    ontopic = any(k in blob for k in ONTOPIC)
    has_author_response = kinds.get("rebuttal", 0) > 0 or n_author_comments > 0
    return {
        "forum": forum_id, "title": title, "conf": conf, "year": year, "venue": venue,
        "n_reviews": n_rev, "ratings": ratings, "decision": decision,
        "n_rebuttal": kinds.get("rebuttal", 0), "n_author_comments": n_author_comments,
        "n_meta": kinds.get("meta_review", 0), "n_decision": kinds.get("decision", 0),
        "has_author_response": has_author_response, "ontopic": ontopic,
    }


def main():
    recs = []
    for path in sorted(glob.glob(os.path.join(RAW, "*.json"))):
        forum_id = os.path.splitext(os.path.basename(path))[0]
        try:
            d = json.load(open(path))
        except Exception as e:
            print("skip", forum_id, e); continue
        notes = d.get("notes") or []
        if not notes:
            continue
        recs.append(derive(forum_id, notes))
    out = os.path.join(HERE, "reviews", "_all_records.json")
    json.dump(recs, open(out, "w"), indent=1)
    print(f"[rebuild] {len(recs)} forums -> {out}")
    # quick on-topic + full-thread summary
    full = [r for r in recs if r["ontopic"] and r["n_reviews"] >= 2 and r["has_author_response"]]
    print(f"  on-topic & full-thread: {len(full)} / {len(recs)}")


if __name__ == "__main__":
    main()
