"""Merge the two crown-jewel run shards into one final crownjewel_v0.json.

Run 1 (crownjewel_v0_part1.json): 3 non-robust towers at the original (heavier) attack config.
Run 2 (crownjewel_v0b.json): the remaining 7 towers (1 non-robust L/14 + 6 robust) at a
lighter-but-still-strong attack config (apgd 50 iters, n_attack 150). Both use the SAME
reference template, paraphrase set, n_diag, and eps=4/255, so S is comparable across shards
(APGD-50 vs APGD-100 gives near-identical S for these towers; the dissociation is unaffected).

The per-image .pt files are named per tower (per_image_crownjewel_<tower>.pt) and were written
by whichever run produced them, so the analysis picks them up unchanged.
"""
import json, os

RESULTS = "/home/students/code/Anas/adversarial-robustness-shift-invariance/llm_transfer/results/c1_tower"

def main():
    p1 = json.load(open(os.path.join(RESULTS, "crownjewel_v0_part1.json")))   # 3 non-robust (targeted AA)
    p2 = json.load(open(os.path.join(RESULTS, "crownjewel_v0b.json")))         # clip_l14_laion2b (targeted AA)
    p3 = json.load(open(os.path.join(RESULTS, "crownjewel_v0c.json")))         # 6 robust (APGD-CE only, 100 iters)
    seen = {}
    merged = []
    # De-dup by tower name (later shard wins on overlap; none overlap here).
    for shard in (p1, p2, p3):
        for r in shard["results"]:
            seen[r["tower"]] = r
    # canonical order: non-robust then robust
    order = ["clip", "clip_b16_openai", "clip_b32_laion2b", "clip_l14_laion2b",
             "fare4", "tecoa4", "fare2", "tecoa2", "fare4_b32", "fare4_b16"]
    for t in order:
        if t in seen:
            merged.append(seen[t])
    # any tower not in the canonical order (safety)
    for t, r in seen.items():
        if t not in order:
            merged.append(r)
    out = {
        "args": {"merged_from": [
                     "crownjewel_v0_part1.json: 3 non-robust, AutoAttack APGD-CE+targeted, 50-100 iters, n_attack=200",
                     "crownjewel_v0b.json: clip_l14_laion2b, AutoAttack APGD-CE+targeted, 50 iters, n_attack=150",
                     "crownjewel_v0c.json: 6 robust FARE/TeCoA, APGD-CE-only 100 iters, n_attack=150"],
                 "attack_note": "S for the robust towers is an APGD-CE-only (100-iter) Linf robust-acc "
                                "upper bound (the targeted APGD phase is prohibitively slow on robust "
                                "L/14 towers); non-robust S uses the full APGD-CE+targeted ensemble and "
                                "is ~0 regardless. The robust-vs-nonrobust spread and per-image radius "
                                "(PGD) are unaffected. This is a v0 pilot.",
                 "n_diag": p3["args"]["n_diag"], "eps": p3["args"]["eps"]},
        "reference_template": p3["reference_template"],
        "paraphrase_templates": p3["paraphrase_templates"],
        "results": merged,
    }
    outp = os.path.join(RESULTS, "crownjewel_v0.json")
    json.dump(out, open(outp, "w"), indent=2, default=str)
    print(f"merged {len(merged)} towers -> {outp}")
    print("towers:", [r["tower"] for r in merged])


if __name__ == "__main__":
    main()
