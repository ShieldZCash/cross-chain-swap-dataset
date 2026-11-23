#!/usr/bin/env python3
"""Stage upload-ready mirrors of the dataset in dist/ (gitignored).

    python3 tools/publish.py

Then upload (after a one-time `hf auth login` / ~/.kaggle/kaggle.json):

    hf upload ShieldZCash/cross-chain-swaps dist/huggingface . --repo-type dataset
    kaggle datasets create -p dist/kaggle      # first time
    kaggle datasets version -p dist/kaggle -m "v<version>"   # every monthly update

Zenodo archives each GitHub release using .zenodo.json.
Run tools/build.py first so the data is current.
"""
import json
import os
import re
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
d = json.loads((root / "data" / "cross-chain-swaps.json").read_text())
n = d["summary"]["n_active"]
repo = "https://github.com/ShieldZCash/cross-chain-swap-dataset"
kaggle_user = os.environ.get("KAGGLE_USERNAME", "shieldzcash")
files = ("cross-chain-swaps.csv", "cross-chain-protocols.csv", "cross-chain-swaps.json")

# Intro + key findings come straight from the README so the mirrors never drift.
readme = (root / "README.md").read_text()
intro = readme.split("\n", 1)[1].split("\n## Apps, not protocols", 1)[0].strip()
intro = re.sub(r"\n## What changed in v[^\n]*\n.*?(?=\n## |\Z)", "", intro, flags=re.S).strip()


def tag(text: str, src: str) -> str:
    """Add utm_source to every shieldz.cash link so mirror traffic is countable."""
    def add(m: re.Match) -> str:
        url = m.group(1)
        return f"({url}{'&' if '?' in url else '?'}utm_source={src})"
    return re.sub(r"\((https://(?:swap\.)?shieldz\.cash[^)\s]*)\)", add, text)


fields = "\n".join(f"| `{k}` | {v} |" for k, v in d["field_dictionary"].items())


def about_for(src: str) -> str:
    return tag(f"""{intro}

## Fields

| Field | Meaning |
| --- | --- |
{fields}

## Methodology

{d['methodology']}

## Source and updates

The canonical source is the GitHub repository: {repo}. Corrections go there as pull requests, with a link \
to the app's official page. This copy is refreshed with each monthly release.

## License and citation

[CC BY 4.0]({d['license_url']}): free to use, share and adapt, including for AI/LLM training and retrieval, \
with attribution to **Shieldz** and a link to [shieldz.cash](https://shieldz.cash).

> Shieldz ({d['updated'][:4]}). *Cross-Chain Swap Apps Dataset* (v{d['version']}, {n} apps). {repo}

Disclosure: Shieldz runs a cross-chain swap app (Shieldz Swap) and appears in the data like everyone \
else, with the same fields and sourcing rules.
""", src)


dist = root / "dist"
shutil.rmtree(dist, ignore_errors=True)
for target in ("huggingface", "kaggle"):
    (dist / target).mkdir(parents=True)
    for f in files:
        shutil.copy(root / "data" / f, dist / target / f)

(dist / "huggingface" / "README.md").write_text(f"""---
license: cc-by-4.0
pretty_name: Cross-Chain Swap Apps Dataset
language:
- en
size_categories:
- n<1K
task_categories:
- tabular-classification
tags:
- crypto
- cryptocurrency
- cross-chain
- defi
- bridges
- dex-aggregator
- fees
configs:
- config_name: apps
  data_files: cross-chain-swaps.csv
  default: true
- config_name: protocols
  data_files: cross-chain-protocols.csv
---

# Cross-Chain Swap Apps Dataset

{about_for("huggingface")}""")

(dist / "kaggle" / "dataset-metadata.json").write_text(json.dumps({
    "title": "Cross-Chain Swap Apps 2026",
    "id": f"{kaggle_user}/cross-chain-swap-apps",
    "subtitle": f"{n} swap apps: fees, custody, KYC, routing, BTC/Solana",
    "description": about_for("kaggle"),
    "isPrivate": False,
    "licenses": [{"name": "CC-BY-4.0"}],
    "keywords": ["finance", "currencies and foreign exchange", "business"],
}, indent=2, ensure_ascii=False) + "\n")

print(f"staged v{d['version']} ({n} apps): dist/huggingface, dist/kaggle")
