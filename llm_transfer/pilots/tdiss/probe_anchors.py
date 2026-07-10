#!/usr/bin/env python
"""Empirically fix refusal/affirmation anchor token sets from the model's OWN greedy behavior.

Loads Llama-3-8B-Instruct, generates greedy first tokens on a sample of harmful (should refuse)
and benign (should comply) prompts, and tallies the first-token distribution. This makes the
anchor choice data-driven, not hand-picked (audit round2 §0.3).
"""
import csv, json, os, collections, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

HERE = os.path.dirname(os.path.abspath(__file__))
MID = "meta-llama/Meta-Llama-3-8B-Instruct"

tok = AutoTokenizer.from_pretrained(MID)
model = AutoModelForCausalLM.from_pretrained(MID, torch_dtype=torch.bfloat16, device_map="cuda")
model.eval()

rows = list(csv.DictReader(open(os.path.join(HERE, "data", "prompts.csv"))))
harmful = [r for r in rows if r["category"] == "harmful" and r["source"] != "xstest"][:120]
benign = [r for r in rows if r["category"] == "benign"][:120]


def first_tokens(prompts, n_gen=6):
    firsts = collections.Counter()
    strs = collections.Counter()
    for r in prompts:
        msgs = [{"role": "user", "content": r["behavior"]}]
        ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").cuda()
        with torch.no_grad():
            out = model.generate(ids, max_new_tokens=n_gen, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
        gen = out[0, ids.shape[1]:]
        firsts[gen[0].item()] += 1
        strs[tok.decode(gen).strip()[:40]] += 1
    return firsts, strs


hf, hs = first_tokens(harmful)
bf, bs = first_tokens(benign)

print("=== HARMFUL first-token (expect refusals) ===")
for t, c in hf.most_common(12):
    print(f"  {t:6d} {tok.decode([t])!r:12} {c}")
print("--- harmful first-6tok strings ---")
for s, c in hs.most_common(8):
    print(f"  {c:3d}  {s!r}")

print("\n=== BENIGN first-token (expect compliance) ===")
for t, c in bf.most_common(12):
    print(f"  {t:6d} {tok.decode([t])!r:12} {c}")
print("--- benign first-6tok strings ---")
for s, c in bs.most_common(8):
    print(f"  {c:3d}  {s!r}")

out = {
    "harmful_first_tokens": {str(t): c for t, c in hf.most_common(20)},
    "benign_first_tokens": {str(t): c for t, c in bf.most_common(20)},
    "harmful_strings": {s: c for s, c in hs.most_common(20)},
    "benign_strings": {s: c for s, c in bs.most_common(20)},
    "token_decode": {str(t): tok.decode([t]) for t, _ in list(hf.most_common(20)) + list(bf.most_common(20))},
}
json.dump(out, open(os.path.join(HERE, "data", "anchor_probe.json"), "w"), indent=2)
print("\nwrote data/anchor_probe.json")
