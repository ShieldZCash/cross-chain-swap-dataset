#!/usr/bin/env python3
"""Validate data/cross-chain-swaps.json. Exits non-zero on any error."""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parent.parent
d = json.loads((root / "data" / "cross-chain-swaps.json").read_text())
errors = []

# field -> (allowed types, nullable)
SCHEMA = {
    "name": (str, False), "url": (str, False), "category": (str, False), "custody": (str, False),
    "kyc": (str, False), "fee_pct": ((int, float), True), "fee_note": (str, False),
    "routes_via": (str, False), "native_btc": (bool, True), "solana": (bool, True),
    "chains": (int, True), "founded": (int, True), "status": (str, False),
    "status_note": (str, False), "notable": (str, False), "verified": (bool, False),
    "source_url": (str, True), "checked": (str, True),
}
ENUMS = {
    "category": {"aggregator", "frontend", "wallet", "instant-exchange", "exchange-aggregator"},
    "custody": {"custodial", "non-custodial", "hybrid"},
    "kyc": {"none", "risk-based", "required"},
    "status": {"active", "inactive", "unchecked"},
}

def is_url(u):
    p = urlparse(u)
    return p.scheme in ("http", "https") and bool(p.netloc)

seen = set()
PROTOCOL_CATEGORIES = {"native-dex", "intent-network", "bridge"}
APP_CATEGORIES = ENUMS["category"]
ENUMS["category"] = APP_CATEGORIES | PROTOCOL_CATEGORIES
rows = [("apps", i, a) for i, a in enumerate(d["apps"])] + [("protocols", i, a) for i, a in enumerate(d.get("protocols", []))]
for table, i, a in rows:
    who = f"{table}[{i}] ({a.get('name', '?')})"
    if table == "apps" and a.get("category") not in APP_CATEGORIES:
        errors.append(f"{who}: a protocol category belongs in `protocols`, not `apps`")
    if table == "protocols" and a.get("category") not in PROTOCOL_CATEGORIES:
        errors.append(f"{who}: protocols use native-dex, intent-network or bridge")
    for k, (t, nullable) in SCHEMA.items():
        if k not in a:
            errors.append(f"{who}: missing field '{k}'")
            continue
        v = a[k]
        if v is None:
            if not nullable:
                errors.append(f"{who}: '{k}' may not be null")
            continue
        # bool is an int subclass: never accept it where a number is meant.
        if not isinstance(v, t) or (t is not bool and isinstance(v, bool)):
            errors.append(f"{who}: '{k}' has wrong type {type(v).__name__}")
    extra = set(a) - set(SCHEMA)
    if extra:
        errors.append(f"{who}: unknown fields {sorted(extra)}")
    for k, allowed in ENUMS.items():
        if a.get(k) not in allowed:
            errors.append(f"{who}: {k} must be one of {sorted(allowed)}")
    for k in ("url", "source_url"):
        if isinstance(a.get(k), str) and not is_url(a[k]):
            errors.append(f"{who}: {k} is not a valid http(s) URL")
    if a.get("verified") and not a.get("source_url"):
        errors.append(f"{who}: a verified row needs a source_url")
    if a.get("verified") and a.get("fee_pct") is None:
        errors.append(f"{who}: a verified row needs a fee_pct")
    if a.get("status") != "active" and not a.get("status_note"):
        errors.append(f"{who}: an inactive or unchecked row needs a status_note")
    if isinstance(a.get("fee_pct"), (int, float)) and not 0 <= a["fee_pct"] <= 10:
        errors.append(f"{who}: fee_pct {a['fee_pct']} out of range 0-10")
    if isinstance(a.get("founded"), int) and not 2008 <= a["founded"] <= 2027:
        errors.append(f"{who}: founded {a['founded']} looks wrong")
    key = a.get("name", "").strip().lower()
    if key in seen:
        errors.append(f"{who}: duplicate name")
    seen.add(key)

if d.get("counts", {}).get("total") != len(d["apps"]):
    errors.append("counts.total does not match apps length — run tools/build.py")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(d['apps'])} apps and {len(d.get('protocols', []))} protocols valid")
