#!/usr/bin/env python3
"""Rebuild everything derived from data/cross-chain-swaps.json.

Edit ONLY the `apps` array (and bump `version`/`updated`), then run this.
It recomputes `counts` and `summary`, and regenerates the CSV and DATA.md.
Summary figures cover active rows only; fee statistics use verified rows only,
so an unverified row can never move a published number.
"""
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent.parent
json_path = root / "data" / "cross-chain-swaps.json"
d = json.loads(json_path.read_text())
apps = d["apps"]

FIELDS = ["name", "url", "category", "custody", "kyc", "fee_pct", "fee_note", "routes_via",
          "native_btc", "solana", "chains", "founded", "status", "status_note", "notable",
          "verified", "source_url", "checked"]

active = [a for a in apps if a["status"] == "active"]
verified = [a for a in active if a["verified"]]
n = len(active)
pct = lambda k: round(k / n * 100) if n else 0
custody = Counter(a["custody"] for a in active)
fees = [a["fee_pct"] for a in verified if isinstance(a["fee_pct"], (int, float))]

d["counts"] = {
    "total": len(apps),
    "active": n,
    "inactive": sum(1 for a in apps if a["status"] == "inactive"),
    "unchecked": sum(1 for a in apps if a["status"] == "unchecked"),
    "verified": len(verified),
}
d["summary"] = {
    "n_active": n,
    "by_category": dict(sorted(Counter(a["category"] for a in active).items())),
    "custodial": custody["custodial"],
    "non_custodial": custody["non-custodial"],
    "hybrid": custody["hybrid"],
    "pct_custodial": pct(custody["custodial"]),
    "pct_non_custodial": pct(custody["non-custodial"]),
    "kyc": dict(sorted(Counter(a["kyc"] for a in active).items())),
    # Only figures confirmed on an official page count towards fee statistics.
    "n_fee_verified": len(fees),
    "median_fee_pct": round(statistics.median(fees), 3) if fees else None,
    "zero_fee": sum(1 for f in fees if f == 0),
    "native_btc": sum(1 for a in active if a["native_btc"] is True),
}
json_path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

cell = lambda v: "" if v is None else (str(v).lower() if isinstance(v, bool) else v)
with (root / "data" / "cross-chain-swaps.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    for a in sorted(apps, key=lambda a: a["name"].lower()):
        w.writerow({k: cell(a[k]) for k in FIELDS})

CATEGORY_ORDER = ["native-dex", "intent-network", "bridge", "aggregator", "frontend", "wallet",
                  "instant-exchange", "exchange-aggregator"]
yn = lambda v: "?" if v is None else ("yes" if v else "no")
fee = lambda a: "?" if a["fee_pct"] is None else f"{a['fee_pct']}%" + ("" if a["verified"] else "\\*")
s = d["summary"]
lines = [
    f"# {d['dataset']}: full table",
    "",
    f"{n} active apps ({d['counts']['inactive']} inactive, {d['counts']['unchecked']} unchecked), "
    f"v{d['version']}, updated {d['updated']}. "
    f"License: [{d['license']}]({d['license_url']}), attribution: [Shieldz]({d['publisher_url']}).",
    "",
    f"Of the active apps, **{s['pct_non_custodial']}% are non-custodial**, {s['pct_custodial']}% custodial "
    f"and {s['hybrid']} hybrid. Verified so far (fee and coverage confirmed on an official page): "
    f"{d['counts']['verified']} of {len(apps)}. "
    "`?` means not yet checked and an asterisk marks an unverified figure.",
    "",
]
for cat in CATEGORY_ORDER:
    rows = sorted((a for a in active if a["category"] == cat), key=lambda a: a["name"].lower())
    if not rows:
        continue
    lines += [f"## {cat} ({len(rows)})", "",
              "| App | Custody | KYC | Fee | Native BTC | Solana | Chains | Routes via | Notable |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for a in rows:
        lines.append(
            f"| [{a['name']}]({a['url']}) | {a['custody']} | {a['kyc']} | {fee(a)} | {yn(a['native_btc'])} "
            f"| {yn(a['solana'])} | {a['chains'] or '?'} | {a['routes_via']} | {a['notable']} |")
    lines.append("")
gone = sorted((a for a in apps if a["status"] != "active"), key=lambda a: a["name"].lower())
if gone:
    lines += ["## Inactive or unconfirmed", "", "| App | Status | What we found |", "| --- | --- | --- |"]
    lines += [f"| {a['name']} | {a['status']} | {a['status_note']} |" for a in gone]
    lines.append("")
(root / "DATA.md").write_text("\n".join(lines))
print(f"built: {len(apps)} rows ({n} active, {len(verified)} verified) -> JSON summary, CSV, DATA.md")
