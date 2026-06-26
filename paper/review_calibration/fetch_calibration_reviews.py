#!/usr/bin/env python3
"""
Pull FULL OpenReview review threads (all official reviews + every rebuttal round +
official comments + meta-review + decision) for papers in our topic area, to use as
unbiased calibration anchors for a reviewer agent.

Target: adversarial robustness / shift- and group-invariance / certified (Lipschitz,
smoothing) robustness / anti-aliasing, at NeurIPS 2020-2025 (main + workshops) and,
for outcome diversity that NeurIPS does not expose publicly (rejected submissions are
hidden), ICLR 2020-2025 on the same topics. We want a spread of outcomes: oral/
spotlight (strong accept), poster (weak/borderline accept), and reject/withdrawn.

Anonymous, no login. api2.openreview.net (2023+) with fallback to api.openreview.net
(older venues). Backoff on HTTP 429.

Two modes:
  discover  -- run topic queries, collect candidate forums + venue/year, write
               candidates.json (does NOT pull threads).
  pull      -- given forum ids (from candidates.json or --ids), fetch the full
               thread, render reviews/<label>.md, and record per-reviewer
               ratings + decision in records.json.

Usage:
  python fetch_calibration_reviews.py discover
  python fetch_calibration_reviews.py pull --ids forumid1 forumid2 ...
  python fetch_calibration_reviews.py pull --from-candidates --max 60
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REV_DIR = os.path.join(HERE, "reviews")
RAW_DIR = os.path.join(REV_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

API2 = "https://api2.openreview.net"
API1 = "https://api.openreview.net"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-calibration/1.0"}

TOPIC_QUERIES = [
    "adversarial robustness shift invariance",
    "anti-aliasing adversarial robustness convolutional",
    "certified robustness Lipschitz margin",
    "randomized smoothing certified robustness",
    "translation invariance robustness neural network",
    "group equivariance adversarial robustness",
    "adversarial training robustness generalization",
    "robustness accuracy trade-off neural network",
    "spatial transformation robustness adversarial",
    "margin Lipschitz neural network robustness",
]


# ----------------------------- HTTP -----------------------------
def get(url, params=None, max_attempts=6):
    last = None
    for attempt in range(max_attempts):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=40)
        except Exception as e:  # noqa
            last = e
            time.sleep(3 * (attempt + 1))
            continue
        if r.status_code == 429:
            time.sleep(6 * (attempt + 1))
            continue
        if r.status_code != 200:
            last = f"HTTP {r.status_code}: {r.text[:160]}"
            time.sleep(2 * (attempt + 1))
            continue
        try:
            return r.json()
        except Exception as e:  # noqa
            last = e
            time.sleep(2)
    print(f"  [warn] giving up on {url} params={params}: {last}", file=sys.stderr)
    return None


def search(term, limit=40):
    for base in (API2, API1):
        j = get(base + "/notes/search", {"term": term, "limit": limit})
        if j and j.get("notes"):
            for n in j["notes"]:
                n["_api"] = base
            return j["notes"]
        time.sleep(2)
    return []


def forum_with_replies(forum_id):
    for base in (API2, API1):
        j = get(base + "/notes", {"forum": forum_id, "details": "replies", "limit": 1000})
        if j and j.get("notes"):
            return base, j["notes"]
        time.sleep(2)
    return None, []


# ----------------------------- content helpers -----------------------------
def cv(field):
    if isinstance(field, dict) and "value" in field:
        return field["value"]
    return field


def get_content(note):
    raw = note.get("content", {}) or {}
    return {k: cv(v) for k, v in raw.items()}


def invitations_of(note):
    if "invitations" in note and isinstance(note["invitations"], list):
        return note["invitations"]
    if "invitation" in note:
        return [note["invitation"]]
    return []


def primary_invitation(note):
    """The type-bearing invitation. OpenReview notes list several invitations
    (the real type + a generic '/-/Edit'); pick the first non-Edit one."""
    invs = invitations_of(note)
    for i in invs:
        if i and not i.lower().endswith("/-/edit"):
            return i
    return invs[0] if invs else ""


def note_kind(note):
    # The paper note itself is the only note whose id == forum. Decide this FIRST
    # so its many revision invitations (Rebuttal_Revision, Camera_Ready_Revision...)
    # can't get it misclassified as a rebuttal.
    if note.get("id") == note.get("forum"):
        return "submission"
    # Classify by the suffix after the last '/-/' of the primary invitation, so
    # e.g. '.../Official_Review1/-/Rebuttal' is a rebuttal, not a review.
    inv = primary_invitation(note).lower()
    tail = inv.rsplit("/-/", 1)[-1]
    if "meta_review" in tail or "metareview" in tail:
        return "meta_review"
    if "decision" in tail:
        return "decision"
    if "rebuttal" in tail or "author_response" in tail or "author_rebuttal" in tail:
        return "rebuttal"
    if "official_review" in tail or tail.endswith("review") or tail == "review":
        return "official_review"
    if "comment" in tail:
        return "official_comment"
    if "submission" in tail:
        return "submission"
    return "unknown"


def venue_year(submission):
    c = get_content(submission)
    venue = c.get("venue") or c.get("venueid") or ""
    inv = " ".join(invitations_of(submission))
    blob = f"{venue} {inv}"
    m = re.search(r"(20\d\d)", blob)
    year = m.group(1) if m else ""
    vlow = blob.lower()
    if "neurips" in vlow or "nips" in vlow:
        conf = "NeurIPS"
    elif "iclr" in vlow:
        conf = "ICLR"
    elif "icml" in vlow:
        conf = "ICML"
    else:
        conf = venue or inv
    return conf, year, str(venue)


RATING_KEYS = ["rating", "recommendation", "overall_rating", "score",
               "final_rating", "review_rating"]
CONF_KEYS = ["confidence", "reviewer_confidence"]
DECISION_KEYS = ["decision", "recommendation", "final_decision", "verdict"]


def first_num(s):
    if s is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", str(s))
    return float(m.group(0)) if m else None


def extract_scores(notes):
    """Per-reviewer numeric rating + the decision string, for bucketing.
    Prefer the real Decision note; fall back to a meta-review recommendation."""
    ratings, decision, meta_dec = [], None, None
    for n in notes:
        c = get_content(n)
        k = note_kind(n)
        if k == "official_review":
            for rk in RATING_KEYS:
                if rk in c:
                    num = first_num(c[rk])
                    if num is not None:
                        ratings.append(num)
                        break
        elif k == "decision":
            for dk in DECISION_KEYS:
                if dk in c and cv(c[dk]):
                    decision = str(cv(c[dk]))
                    break
        elif k == "meta_review" and meta_dec is None:
            for dk in ("recommendation", "decision", "final_decision"):
                if dk in c and cv(c[dk]):
                    meta_dec = str(cv(c[dk]))
                    break
    return ratings, (decision or meta_dec)


# ----------------------------- markdown rendering -----------------------------
PRIORITIZED = ["title", "summary", "summary_of_contributions", "summary_and_contributions",
               "strengths", "weaknesses", "strengths_and_weaknesses",
               "opportunities_for_improvement", "requested_changes", "questions",
               "review", "main_review", "limitations", "soundness", "presentation",
               "contribution", "rating", "confidence", "comment", "decision",
               "metareview", "justification"]
SKIP = {"venue", "venueid", "_bibtex", "pdf", "supplementary_material", "html",
        "code", "tldr", "TLDR", "keywords", "primary_area", "authors", "authorids"}


def render_content(c):
    lines, seen = [], set()
    for fld in PRIORITIZED + [k for k in c if k not in PRIORITIZED]:
        if fld in seen or fld in SKIP or fld not in c:
            continue
        seen.add(fld)
        val = c[fld]
        if val in (None, "", [], {}):
            continue
        if isinstance(val, list):
            val = "\n".join(f"- {x}" for x in val)
        lines += [f"**{fld}:**", "", str(val), ""]
    return lines


def render_thread(label, forum_id, notes):
    submission = next((n for n in notes if note_kind(n) == "submission"), None)
    title = "(unknown title)"
    conf = year = venue = ""
    if submission:
        c = get_content(submission)
        title = c.get("title", title)
        conf, year, venue = venue_year(submission)
    md = [f"# {title}", "",
          f"- **Label:** `{label}`",
          f"- **Venue:** {conf} {year}  ({venue})",
          f"- **Forum:** https://openreview.net/forum?id={forum_id}",
          f"> _Fetched {datetime.now(timezone.utc).isoformat()}_", ""]
    by_kind = {}
    for n in notes:
        if n is submission:
            continue
        by_kind.setdefault(note_kind(n), []).append(n)
    md.append("## Thread summary")
    for k in sorted(by_kind):
        md.append(f"- {k}: {len(by_kind[k])}")
    md.append("")
    order = [("official_review", "Official Reviews"),
             ("rebuttal", "Author Rebuttals / Responses"),
             ("official_comment", "Official Comments (multi-round discussion)"),
             ("meta_review", "Meta Review"),
             ("decision", "Decision"),
             ("unknown", "Other replies")]
    for key, heading in order:
        if key not in by_kind:
            continue
        md += [f"## {heading}", ""]
        for n in sorted(by_kind[key], key=lambda x: x.get("cdate") or x.get("tcdate") or 0):
            sig = ", ".join(n.get("signatures", []) or []) or "anonymous"
            ts = n.get("cdate") or n.get("tcdate")
            ts_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else "?"
            md += [f"### {sig} — {ts_str}", ""] + render_content(get_content(n)) + ["---", ""]
    return "\n".join(md), {"title": str(title), "conf": conf, "year": year, "venue": venue}


# ----------------------------- modes -----------------------------
def do_discover(args):
    cands = {}
    for q in TOPIC_QUERIES:
        print(f"[search] {q}")
        notes = search(q, limit=args.limit)
        print(f"   -> {len(notes)} hits")
        for n in notes:
            fid = n.get("forum") or n.get("id")
            if not fid:
                continue
            conf, year, venue = venue_year(n)
            if conf not in ("NeurIPS", "ICLR", "ICML"):
                continue
            if year and not ("2020" <= year <= "2025"):
                continue
            if fid not in cands:
                c = get_content(n)
                cands[fid] = {"forum": fid, "title": str(c.get("title", "?"))[:140],
                              "conf": conf, "year": year, "venue": venue, "query": q}
        time.sleep(2)
    out = os.path.join(REV_DIR, "candidates.json")
    json.dump(list(cands.values()), open(out, "w"), indent=1)
    print(f"\n[done] {len(cands)} candidate forums -> {out}")
    for c in sorted(cands.values(), key=lambda x: (x["conf"], x["year"])):
        print(f"  {c['conf']:8s} {c['year']:4s}  {c['forum']:14s}  {c['title'][:80]}")


TOPIC_KEYWORDS = ["robust", "adversarial", "invarian", "equivarian", "certif",
                  "lipschitz", "smoothing", "alias", "translation", "perturbation",
                  "margin", "shift", "rotation", "spatial transform"]


def list_venue_submissions(venueid):
    """List ALL submissions for an older venue (e.g. ICLR.cc/2021/Conference),
    paging through the venue's submission invitation. Tries Blind_Submission
    then Submission, on api v1 then v2."""
    inv_patterns = [f"{venueid}/-/Blind_Submission", f"{venueid}/-/Submission"]
    for base in (API1, API2):
        for inv in inv_patterns:
            notes, offset = [], 0
            while True:
                j = get(base + "/notes", {"invitation": inv, "limit": 1000,
                                          "offset": offset})
                batch = (j or {}).get("notes") or []
                notes += batch
                if len(batch) < 1000:
                    break
                offset += 1000
                time.sleep(1)
            if notes:
                return base, inv, notes
            time.sleep(1)
    return None, None, []


def do_venue(args):
    """Discover on-topic submissions for a specific (usually older) venue by
    listing its submissions and keyword-filtering titles/abstracts. Appends to
    candidates.json so they can then be pulled."""
    cand_path = os.path.join(REV_DIR, "candidates.json")
    cands = {c["forum"]: c for c in json.load(open(cand_path))} if os.path.exists(cand_path) else {}
    added = 0
    for venueid in args.venueids:
        print(f"[venue] listing {venueid}")
        base, inv, notes = list_venue_submissions(venueid)
        print(f"   -> {len(notes)} submissions via {inv} ({base})")
        for n in notes:
            c = get_content(n)
            title = str(c.get("title", "") or "")
            abstract = str(c.get("abstract", "") or "")
            blob = (title + " " + abstract).lower()
            if not any(k in blob for k in TOPIC_KEYWORDS):
                continue
            fid = n.get("forum") or n.get("id")
            conf, year, venue = venue_year(n)
            if fid and fid not in cands:
                cands[fid] = {"forum": fid, "title": title[:140], "conf": conf,
                              "year": year, "venue": venue, "query": f"venue:{venueid}"}
                added += 1
                print(f"     + {conf} {year} {fid}  {title[:70]}")
    json.dump(list(cands.values()), open(cand_path, "w"), indent=1)
    print(f"\n[done] +{added} on-topic candidates -> {cand_path}")


def do_pull(args):
    if args.ids:
        ids = [(fid, fid) for fid in args.ids]
    else:
        cand = json.load(open(os.path.join(REV_DIR, "candidates.json")))
        ids = [(c["forum"], f"{c['conf']}_{c['year']}_{c['forum']}") for c in cand][:args.max]
    records = []
    for forum_id, label in ids:
        label = re.sub(r"[^A-Za-z0-9_.-]", "_", label)
        print(f"[pull] {label} ({forum_id})")
        base, notes = forum_with_replies(forum_id)
        if not notes:
            print("   [skip] no notes")
            continue
        json.dump({"api": base, "notes": notes},
                  open(os.path.join(RAW_DIR, f"{forum_id}.json"), "w"))
        md, meta = render_thread(label, forum_id, notes)
        ratings, decision = extract_scores(notes)
        n_rev = sum(1 for n in notes if note_kind(n) == "official_review")
        open(os.path.join(REV_DIR, f"{label}.md"), "w").write(md)
        records.append({"label": label, "forum": forum_id, **meta,
                        "n_reviews": n_rev, "ratings": ratings, "decision": decision})
        print(f"   [ok] {meta['conf']} {meta['year']}  reviews={n_rev} "
              f"ratings={ratings} decision={decision}")
        time.sleep(2)
    json.dump(records, open(os.path.join(REV_DIR, "records.json"), "w"), indent=1)
    print(f"\n[done] {len(records)} threads -> {REV_DIR}/records.json")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    d = sub.add_parser("discover")
    d.add_argument("--limit", type=int, default=40)
    v = sub.add_parser("venue")
    v.add_argument("--venueids", nargs="+", required=True,
                   help="e.g. ICLR.cc/2021/Conference NeurIPS.cc/2022/Conference")
    p = sub.add_parser("pull")
    p.add_argument("--ids", nargs="*", default=None)
    p.add_argument("--from-candidates", action="store_true")
    p.add_argument("--max", type=int, default=60)
    args = ap.parse_args()
    if args.mode == "discover":
        do_discover(args)
    elif args.mode == "venue":
        do_venue(args)
    else:
        do_pull(args)


if __name__ == "__main__":
    main()
