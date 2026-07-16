"""Fetch RobustBench OFFICIAL leaderboard clean_acc + autoattack_acc for the
candidate models (from the model_info JSONs on GitHub). Cached to official.json.
Used as a validity check that our APGD-CE ranking matches full AutoAttack.
"""
import os, json, urllib.request
from download_models import CANDIDATES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "official.json")
BASE = "https://raw.githubusercontent.com/RobustBench/robustbench/master/model_info/cifar10/Linf/"


def main():
    data = {}
    if os.path.exists(OUT):
        data = json.load(open(OUT))
    for name in CANDIDATES:
        if name in data:
            continue
        url = BASE + name + ".json"
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                j = json.load(r)
            data[name] = {
                "clean_acc": float(j.get("clean_acc", "nan")),
                "autoattack_acc": float(j.get("autoattack_acc", "nan")),
                "architecture": j.get("architecture", ""),
            }
            print(f"{name:38s} clean={data[name]['clean_acc']:.2f} "
                  f"AA={data[name]['autoattack_acc']:.2f}")
        except Exception as e:
            print(f"{name:38s} FAIL {repr(e)[:80]}")
        json.dump(data, open(OUT, "w"), indent=2)
    print(f"cached {len(data)} official entries -> {OUT}")


if __name__ == "__main__":
    main()
