"""SMOKE TEST for the ONE new mechanism of the hardened Crown-Jewel design:
TEXT-ADVERSARIAL robustness = worst-case-over-paraphrases (the bottom-right 2x2 cell).

The average-case textual invariance (paraphrase-consistency PC, v0) asks: over a set of K
meaning-preserving prompt templates, how OFTEN does the top-1 stay put? The worst-case sibling
asks: does the WORST template in that SAME set flip the top-1 (away from the true label)?

Given a fixed image and its true class y, and K meaning-preserving templates
T = {t_1..t_K} (the SAME curated set used for average-case PC), define per template t a
single-template zero-shot head h_t and prediction pred_t(x) = argmax_c <emb(x), proto_t(c)>.

  clean/reference acc            a_ref  = mean_x 1[pred_ref(x) == y]           (reference template)
  average-case (per-template)    a_avg  = mean_x mean_t 1[pred_t(x) == y]      (== textual "acc under PC")
  ADVERSARIAL-PARAPHRASE acc     S_text = mean_x min_t 1[pred_t(x) == y]
                                        = mean_x 1[ pred_t(x) == y for ALL t ]  (worst template can't flip)

This is a DISCRETE worst-case over a semantically-null perturbation family -- the exact textual
analog of the image cell's average-shift-consistency (SC) vs worst-case-eps-ball (AutoAttack S).
No text-encoder attack machinery, no meaning drift: the perturbation set is fixed and human-curated.

WHAT THIS SMOKE CONFIRMS (design-gate, ONE non-robust encoder, a handful of images):
  (1) the ordering    S_text <= a_avg <= a_ref <= 1                  (worst <= average <= clean)
  (2) SIGNAL: some images ARE flipped by SOME meaning-preserving reword (S_text strictly < a_ref),
      i.e. the worst-case textual axis is non-degenerate on a non-robust CLIP tower.
  (3) it runs on GPU 1 with one tower, small batches, no attack code needed.

Reuses run_crownjewel_v0.load_tower_with_reference_head / build_single_template_features and the
SAME PARAPHRASE_TEMPLATES / REFERENCE_TEMPLATE -- no new model or head machinery is invented.

GPU 1 ONLY.  Example:
  CUDA_VISIBLE_DEVICES=1 python -u smoke_text_adv.py --tower clip --n 64
"""
import argparse
import time

import torch
import torch.nn.functional as F

import data
import run_crownjewel_v0 as CJ  # reuse loader, head builder, and the curated template set


@torch.no_grad()
def per_template_predictions(tower, clip_model, tokenizer, class_names, images, device,
                             templates, bs=128):
    """For each template t, classify every image with the single-template head h_t.
    Returns pred[t] : LongTensor[N] of top-1 class ids (t indexes the template list)."""
    logit_scale = tower.logit_scale
    # embed images once; all single-template heads reuse the same image embeddings
    embs = []
    for i in range(0, len(images), bs):
        embs.append(tower.encode(images[i:i + bs].to(device)))
    emb = torch.cat(embs)  # [N,d]
    preds = []
    for t in templates:
        tf = CJ.build_single_template_features(clip_model, tokenizer, class_names, t, device)  # [C,d]
        logits = logit_scale * emb @ tf.t()
        preds.append(logits.argmax(1).cpu())
    return torch.stack(preds, 0)  # [K, N]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tower", default="clip", help="ONE (non-robust) tower for the smoke")
    ap.add_argument("--n", type=int, default=64, help="images to smoke (correct-under-reference)")
    ap.add_argument("--bs", type=int, default=128)
    args = ap.parse_args()
    device = "cuda"

    t0 = time.time()
    class_names = data.get_class_names()
    imgs, labels = data.load_val(n=400, seed=0, cache_path=CJ.CACHE)  # small pool; subset below
    tower, clip_model, tokenizer = CJ.load_tower_with_reference_head(args.tower, class_names, device)
    print(f"[smoke] tower={args.tower} loaded ({time.time()-t0:.0f}s); "
          f"{len(CJ.PARAPHRASE_TEMPLATES)} meaning-preserving templates "
          f"(ref={CJ.REFERENCE_TEMPLATE!r})", flush=True)

    # reference prediction and the correct-under-reference subset (the PC / attack population)
    ref_pred = CJ.D.predict(tower, imgs, bs=args.bs, device=device)
    correct = (ref_pred == labels)
    ci = torch.where(correct)[0][:args.n]
    x, y = imgs[ci], labels[ci]
    print(f"[smoke] using {len(ci)} correct-under-reference images", flush=True)

    # per-template top-1 over the SAME curated meaning-preserving set
    templates = CJ.PARAPHRASE_TEMPLATES
    K = len(templates)
    preds = per_template_predictions(tower, clip_model, tokenizer, class_names, x, device,
                                     templates, bs=args.bs)  # [K, n]
    y_row = y.view(1, -1)
    correct_kt = (preds == y_row)  # [K, n] : template t classifies image i correctly?

    # reference-template accuracy (== 1.0 by construction on this subset; sanity)
    ref_idx = templates.index(CJ.REFERENCE_TEMPLATE)
    a_ref = correct_kt[ref_idx].float().mean().item()

    # AVERAGE-case textual accuracy (per-template mean) -- the "acc implied by paraphrase-consistency"
    a_avg = correct_kt.float().mean().item()

    # WORST-case textual accuracy (adversarial-paraphrase): correct under ALL K templates
    survives_all = correct_kt.all(dim=0)            # [n] : no meaning-preserving reword flips it
    S_text = survives_all.float().mean().item()

    # how many images does SOME meaning-preserving reword flip? (signal check)
    n_flipped = int((~survives_all).sum().item())
    # per-template accuracy (which rewordings bite hardest)
    per_template_acc = {t: correct_kt[k].float().mean().item() for k, t in enumerate(templates)}
    worst_t = min(per_template_acc, key=per_template_acc.get)

    print("\n[smoke] === text-adversarial (worst-case-over-paraphrases) ===")
    print(f"  a_ref  (reference-template acc, sanity=1.0)   : {a_ref:.4f}")
    print(f"  a_avg  (average per-template acc = PC-implied): {a_avg:.4f}")
    print(f"  S_text (worst-case / adversarial-paraphrase)  : {S_text:.4f}")
    print(f"  ordering  S_text <= a_avg <= a_ref <= 1       : "
          f"{S_text:.4f} <= {a_avg:.4f} <= {a_ref:.4f} <= 1  -> "
          f"{S_text <= a_avg + 1e-9 <= 1 and a_avg <= a_ref + 1e-9}")
    print(f"  images flipped by SOME meaning-preserving reword: {n_flipped}/{len(ci)} "
          f"(axis has signal: {n_flipped > 0})")
    print(f"  worst template: {worst_t!r}  (acc {per_template_acc[worst_t]:.4f})")
    print("  per-template acc:")
    for t, a in sorted(per_template_acc.items(), key=lambda kv: kv[1]):
        print(f"    {a:.4f}  {t}")

    # explicit design-gate assertions
    assert a_ref >= a_avg - 1e-9, "reference acc should be >= average per-template acc"
    assert a_avg >= S_text - 1e-9, "average acc should be >= worst-case acc (S_text)"
    assert 0.0 <= S_text <= 1.0
    print(f"\n[smoke] PASS: ordering holds; axis {'HAS' if n_flipped>0 else 'has NO'} signal "
          f"on {args.tower}. ({time.time()-t0:.0f}s)")

    del tower, clip_model
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
