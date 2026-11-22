#!/usr/bin/env python3
"""Render the GitHub Pages site from data/cross-chain-swaps.json.

Writes site/index.html (single file, no external assets). The Pages workflow
runs this on every push to main, so the page always matches the dataset.
Ranking uses only dataset fields; the formula is printed on the page.
"""
import json
import sys
from html import escape
from pathlib import Path

root = Path(__file__).resolve().parent.parent
d = json.loads((root / "data" / "cross-chain-swaps.json").read_text())
out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "site"
out_dir.mkdir(parents=True, exist_ok=True)

REPO = "https://github.com/ShieldZCash/cross-chain-swap-dataset"
RAW = "https://raw.githubusercontent.com/ShieldZCash/cross-chain-swap-dataset/main/data"
PAGES = "https://shieldzcash.github.io/cross-chain-swap-dataset/"

CAT_LABEL = {
    "aggregator": "Aggregator",
    "frontend": "Protocol front-end",
    "wallet": "Wallet",
    "instant-exchange": "Instant exchange",
    "exchange-aggregator": "Exchange aggregator",
}


def score(a):
    parts = []
    kyc = {"none": 3, "risk-based": 1}.get(a["kyc"], 0)
    parts.append(("No KYC", kyc, 3))
    cus = {"non-custodial": 3, "hybrid": 2}.get(a["custody"], 0)
    parts.append(("Custody", cus, 3))
    parts.append(("Native BTC", 1 if a["native_btc"] is True else 0, 1))
    parts.append(("Solana", 1 if a["solana"] is True else 0, 1))
    if a["fee_type"] == "stated" and isinstance(a["fee_pct"], (int, float)):
        fee = round(max(0.0, 2 - a["fee_pct"] * 2), 2)
    elif a["fee_type"] == "route-only":
        fee = 1
    else:
        fee = 0
    parts.append(("Published fee", fee, 2))
    parts.append(("Chains 30+", 1 if (a["chains"] or 0) >= 30 else 0, 1))
    parts.append(("Verified", 1 if a["verified"] else 0, 1))
    return round(sum(p[1] for p in parts), 2), parts


MAX = 12
active = [a for a in d["apps"] if a["status"] == "active"]
inactive = [a for a in d["apps"] if a["status"] != "active"]
for a in active:
    a["_score"], a["_parts"] = score(a)
active.sort(key=lambda a: (-a["_score"], -(a["chains"] or 0), a["name"].lower()))

c = d["counts"]
updated = d["updated"]
version = d["version"]
n = len(active)
nc = sum(1 for a in active if a["custody"] == "non-custodial")
nokyc = sum(1 for a in active if a["kyc"] == "none")
fullyes = sum(1 for a in active if a["kyc"] == "none" and a["custody"] == "non-custodial"
              and a["native_btc"] is True and a["solana"] is True)

e = lambda s: escape(str(s if s is not None else ""), quote=True)


def yesno(v, yes="yes", no="no"):
    if v is True:
        return f'<span class="b ok" title="{yes}">✓</span>'
    if v is False:
        return f'<span class="b no" title="{no}">✕</span>'
    return '<span class="b un" title="not yet verified">?</span>'


def kyc_cell(k):
    if k == "none":
        return '<span class="b ok" title="No KYC">✓</span>'
    return '<span class="b mid" title="Risk-based: flagged swaps can be held for KYC">~</span>'


def custody_cell(cu):
    cls = {"non-custodial": "ok", "hybrid": "mid"}.get(cu, "no")
    sym = {"non-custodial": "✓", "hybrid": "~"}.get(cu, "✕")
    return f'<span class="b {cls}" title="{e(cu)}">{sym}</span>'


def fee_text(a):
    if a["fee_type"] == "stated" and isinstance(a["fee_pct"], (int, float)):
        f = a["fee_pct"]
        return f"{f:g}%" + ("" if a["verified"] else "*")
    if a["fee_type"] == "route-only":
        return "route only"
    return "unpublished"


def fee_sort(a):
    if a["fee_type"] == "stated" and isinstance(a["fee_pct"], (int, float)):
        return a["fee_pct"]
    return 50 if a["fee_type"] == "route-only" else 99


def breakdown(a):
    return "; ".join(f"{k} {v:g}/{m}" for k, v, m in a["_parts"])


rows = []
for i, a in enumerate(active, 1):
    rows.append(
        f'<tr data-cat="{e(a["category"])}" data-kyc="{e(a["kyc"])}" data-cus="{e(a["custody"])}" '
        f'data-btc="{1 if a["native_btc"] is True else 0}" data-sol="{1 if a["solana"] is True else 0}" '
        f'data-ver="{1 if a["verified"] else 0}">'
        f'<td class="rk" data-v="{i}">{i}</td>'
        f'<td class="nm" data-v="{e(a["name"].lower())}"><a href="{e(a["url"])}" rel="noopener nofollow" target="_blank">{e(a["name"])}</a>'
        f'<small>{e(CAT_LABEL.get(a["category"], a["category"]))}</small></td>'
        f'<td class="sc" data-v="{a["_score"]}" title="{e(breakdown(a))}"><b>{a["_score"]:g}</b><i style="--w:{a["_score"] / MAX * 100:.0f}%"></i></td>'
        f'<td data-v="{2 if a["kyc"] == "none" else 1}">{kyc_cell(a["kyc"])}</td>'
        f'<td data-v="{ {"non-custodial": 2, "hybrid": 1}.get(a["custody"], 0) }">{custody_cell(a["custody"])}</td>'
        f'<td data-v="{1 if a["native_btc"] is True else 0}">{yesno(a["native_btc"])}</td>'
        f'<td data-v="{1 if a["solana"] is True else 0}">{yesno(a["solana"])}</td>'
        f'<td class="fee" data-v="{fee_sort(a)}" title="{e(a["fee_note"])}">{e(fee_text(a))}</td>'
        f'<td class="num" data-v="{a["chains"] or 0}">{e(a["chains"] if a["chains"] else "?")}</td>'
        f'<td class="nt">{e(a["notable"])}</td>'
        "</tr>"
    )

cards = []
for i, a in enumerate(active[:20], 1):
    facts = [
        ("Type", CAT_LABEL.get(a["category"], a["category"])),
        ("Custody", a["custody"]),
        ("KYC", "none" if a["kyc"] == "none" else "risk-based (flagged swaps can be held)"),
        ("Own fee", fee_text(a)),
        ("Routes via", a["routes_via"]),
        ("Chains", a["chains"] or "not yet verified"),
    ]
    if a["founded"]:
        facts.append(("Founded", a["founded"]))
    dl = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in facts)
    src = (f'<a href="{e(a["source_url"])}" rel="noopener nofollow" target="_blank">source</a>'
           if a["source_url"] else "no source yet")
    ver = '<span class="pill ok">verified</span>' if a["verified"] else '<span class="pill un">unverified</span>'
    cards.append(
        f'<article class="card"><header><span class="cn">{i}</span><h3>'
        f'<a href="{e(a["url"])}" rel="noopener nofollow" target="_blank">{e(a["name"])}</a></h3>'
        f'<span class="cs">{a["_score"]:g}<small>/{MAX}</small></span></header>'
        f'<p>{e(a["notable"])}</p><dl>{dl}</dl>'
        f'<p class="fn">{e(a["fee_note"])}</p>'
        f'<footer>{ver}<span>checked {e(a["checked"])} · {src}</span></footer></article>'
    )

inactive_li = "".join(
    f'<li><b>{e(a["name"])}</b> <span>{e(a["status_note"] or a["status"])}</span></li>' for a in inactive
)
proto_li = "".join(
    f'<li><a href="{e(p.get("url", ""))}" rel="noopener nofollow" target="_blank">{e(p["name"])}</a>'
    f'<span>{e(p.get("category", ""))}</span></li>'
    for p in d.get("protocols", [])
)

cats = sorted({a["category"] for a in active})
cat_opts = "".join(f'<option value="{e(k)}">{e(CAT_LABEL.get(k, k))}</option>' for k in cats)

ld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Dataset",
            "name": d["dataset"],
            "description": "Comparison of cross-chain swap apps by custody, KYC, own fee, native BTC and Solana support.",
            "url": PAGES,
            "sameAs": [REPO, d["canonical"]],
            "version": version,
            "dateModified": updated,
            "datePublished": d["published"],
            "license": d["license_url"],
            "creator": {"@type": "Organization", "name": d["publisher"], "url": d["publisher_url"]},
            "distribution": [
                {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": f"{RAW}/cross-chain-swaps.json"},
                {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": f"{RAW}/cross-chain-swaps.csv"},
            ],
        },
        {
            "@type": "ItemList",
            "name": "Cross-chain swap apps ranked for fast no-account swaps",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": n,
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": a["name"], "url": a["url"]}
                for i, a in enumerate(active[:25], 1)
            ],
        },
    ],
}

title = f"Fastest Cross-Chain Swaps Without an Account ({updated[:4]}): {n} Apps Ranked"
desc = (f"{n} cross-chain swap apps ranked on custody, KYC, own fee, native BTC and Solana support. "
        f"Open dataset, CC BY 4.0, updated {updated}.")

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{PAGES}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{PAGES}">
<meta name="twitter:card" content="summary">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
:root{{--bg:#0b0d0c;--bg2:#121614;--bg3:#18201c;--line:#24302a;--tx:#e6ece8;--mut:#8e9b94;--ac:#2fd08a;--ac2:#7ef0bd;--warn:#e9b949;--bad:#ef5b5b;color-scheme:dark}}
@media (prefers-color-scheme:light){{:root{{--bg:#f6f8f7;--bg2:#fff;--bg3:#eef3f0;--line:#d7e0db;--tx:#101614;--mut:#55625b;--ac:#0e9f63;--ac2:#0b7d4e;--warn:#b07d0c;--bad:#c63434;color-scheme:light}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
a{{color:var(--ac2);text-decoration:none}}a:hover{{text-decoration:underline}}
.wrap{{max-width:1180px;margin:0 auto;padding-inline:20px}}
.hero{{padding:56px 0 34px;border-bottom:1px solid var(--line);background:radial-gradient(900px 300px at 15% 0%,color-mix(in srgb,var(--ac) 16%,transparent),transparent)}}
.kick{{font:600 12px/1 ui-monospace,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--ac)}}
h1{{font-size:clamp(28px,4.6vw,48px);line-height:1.1;margin:14px 0 12px;letter-spacing:-.02em;max-width:22ch}}
.sub{{color:var(--mut);max-width:70ch;font-size:16px;margin:0}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:28px}}
.stat{{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.stat b{{display:block;font-size:26px;font-variant-numeric:tabular-nums}}.stat span{{color:var(--mut);font-size:13px}}
nav.toc{{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}}
nav.toc .wrap{{display:flex;gap:18px;overflow-x:auto;padding-block:11px;white-space:nowrap;font-size:14px}}
nav.toc a{{color:var(--mut)}}nav.toc a:hover{{color:var(--tx)}}
section{{padding:44px 0;border-bottom:1px solid var(--line)}}
h2{{font-size:24px;margin:0 0 6px;letter-spacing:-.01em}}
.lead{{color:var(--mut);margin:0 0 20px;max-width:78ch}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}
.box{{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.box h3{{margin:0 0 6px;font-size:16px}}.box p{{margin:0;color:var(--mut);font-size:14px}}
.formula{{font:13px/1.7 ui-monospace,Menlo,monospace;background:var(--bg3);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow-x:auto}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px;align-items:center}}
.filters label{{display:inline-flex;align-items:center;gap:6px;background:var(--bg2);border:1px solid var(--line);border-radius:999px;padding:6px 12px;font-size:13px;cursor:pointer;user-select:none}}
.filters input[type=checkbox]{{accent-color:var(--ac)}}
.filters select,.filters input[type=search]{{background:var(--bg2);color:var(--tx);border:1px solid var(--line);border-radius:999px;padding:7px 12px;font:inherit;font-size:13px}}
.filters input[type=search]{{flex:1;min-width:160px}}
#cnt{{color:var(--mut);font-size:13px;margin-left:auto}}
.tw{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--bg2)}}
table{{border-collapse:collapse;width:100%;min-width:920px;font-size:14px}}
th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:center;vertical-align:middle}}
th{{position:sticky;top:0;background:var(--bg3);font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);cursor:pointer;white-space:nowrap}}
th[aria-sort=ascending]::after{{content:" ▲"}}th[aria-sort=descending]::after{{content:" ▼"}}
tbody tr:hover{{background:var(--bg3)}}tbody tr:last-child td{{border-bottom:0}}
td.nm{{text-align:left;font-weight:600;white-space:nowrap}}td.nm small{{display:block;font-weight:400;color:var(--mut);font-size:12px}}
td.nt{{text-align:left;color:var(--mut);font-size:13px;min-width:240px}}
td.rk{{color:var(--mut);font-variant-numeric:tabular-nums}}td.num,td.fee{{font-variant-numeric:tabular-nums;white-space:nowrap}}
td.sc{{min-width:90px}}td.sc b{{font-variant-numeric:tabular-nums}}td.sc i{{display:block;height:4px;border-radius:4px;margin-top:4px;background:linear-gradient(90deg,var(--ac) var(--w),var(--line) var(--w))}}
.b{{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:7px;font-weight:700;font-size:13px}}
.b.ok{{background:color-mix(in srgb,var(--ac) 18%,transparent);color:var(--ac)}}
.b.mid{{background:color-mix(in srgb,var(--warn) 18%,transparent);color:var(--warn)}}
.b.no{{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}}
.b.un{{background:var(--bg3);color:var(--mut)}}
.legend{{color:var(--mut);font-size:13px;margin-top:10px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}}
.card{{background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:16px 18px;display:flex;flex-direction:column}}
.card header{{display:flex;align-items:center;gap:10px}}.card h3{{margin:0;font-size:17px;flex:1}}
.cn{{font:600 12px ui-monospace,Menlo,monospace;color:var(--mut)}}
.cs{{font-weight:700;color:var(--ac);font-variant-numeric:tabular-nums}}.cs small{{color:var(--mut);font-weight:400}}
.card>p{{color:var(--mut);font-size:14px;margin:8px 0 10px}}
.card dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0;font-size:13px}}
.card dt{{color:var(--mut)}}.card dd{{margin:0}}
.card .fn{{font-size:12.5px;border-top:1px dashed var(--line);padding-top:8px;margin-top:10px}}
.card footer{{margin-top:auto;padding-top:10px;display:flex;gap:10px;align-items:center;font-size:12px;color:var(--mut);flex-wrap:wrap}}
.pill{{border-radius:999px;padding:2px 9px;font-size:11px;font-weight:600}}.pill.ok{{background:color-mix(in srgb,var(--ac) 18%,transparent);color:var(--ac)}}.pill.un{{background:var(--bg3);color:var(--mut)}}
ul.plain{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:8px}}
ul.plain li{{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:9px 12px;font-size:14px;display:flex;justify-content:space-between;gap:10px}}
ul.plain li span{{color:var(--mut);font-size:12.5px;text-align:right}}
.dl{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}
.btn{{display:inline-block;border:1px solid var(--line);background:var(--bg2);border-radius:10px;padding:9px 14px;font-weight:600;font-size:14px}}
.btn.pri{{background:var(--ac);color:#04120b;border-color:var(--ac)}}
footer.site{{padding:30px 0 50px;color:var(--mut);font-size:13px}}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
<div class="kick">Open dataset · v{e(version)} · updated {e(updated)}</div>
<h1>Fastest cross-chain swaps without an account</h1>
<p class="sub">Need to move BTC, ETH, SOL or stablecoins across chains right now? {n} live swap apps, ranked only on facts that matter when you are in a hurry: whether you must sign up or pass KYC, who holds your funds mid-swap, what the app itself charges, and whether it handles native Bitcoin and Solana.</p>
<div class="stats">
<div class="stat"><b>{n}</b><span>active apps compared</span></div>
<div class="stat"><b>{nokyc}</b><span>need no KYC at all</span></div>
<div class="stat"><b>{nc}</b><span>non-custodial</span></div>
<div class="stat"><b>{fullyes}</b><span>tick all four: no KYC, non-custodial, BTC, SOL</span></div>
<div class="stat"><b>{c["verified"]}</b><span>fees verified on an official page</span></div>
</div>
</div></header>
<nav class="toc"><div class="wrap"><a href="#ranking">Ranking</a><a href="#method">Method</a><a href="#types">Swap types</a><a href="#details">Top 20 in detail</a><a href="#protocols">Protocols</a><a href="#inactive">Inactive</a><a href="#data">Data</a></div></nav>
<main class="wrap">

<section id="ranking">
<h2>Ranking</h2>
<p class="lead">Rebuilt automatically from the dataset on every update. Click a column to sort, hover a score for its breakdown, hover a fee for the published fee note.</p>
<div class="filters" role="group" aria-label="Filters">
<input type="search" id="q" placeholder="Search apps or routes" aria-label="Search">
<select id="cat" aria-label="Type"><option value="">All types</option>{cat_opts}</select>
<label><input type="checkbox" id="fkyc"> No KYC</label>
<label><input type="checkbox" id="fnc"> Non-custodial</label>
<label><input type="checkbox" id="fbtc"> Native BTC</label>
<label><input type="checkbox" id="fsol"> Solana</label>
<label><input type="checkbox" id="fver"> Verified only</label>
<span id="cnt"></span>
</div>
<div class="tw"><table id="t">
<thead><tr><th data-k="n">#</th><th data-k="s">App</th><th data-k="n" aria-sort="descending">Score</th><th data-k="n">No KYC</th><th data-k="n">Non-custodial</th><th data-k="n">Native BTC</th><th data-k="n">Solana</th><th data-k="n">Own fee</th><th data-k="n">Chains</th><th>Notes</th></tr></thead>
<tbody>
{chr(10).join(rows)}
</tbody></table></div>
<p class="legend"><span class="b ok">✓</span> yes &nbsp; <span class="b mid">~</span> partial (risk-based KYC, or hybrid custody) &nbsp; <span class="b no">✕</span> no &nbsp; <span class="b un">?</span> not yet verified &nbsp;·&nbsp; * fee figure not yet verified on an official page. "route only" = the app adds no fee of its own; protocol fees, liquidity costs and gas apply on every app.</p>
</section>

<section id="method">
<h2>Method</h2>
<p class="lead">Every score is computed from public dataset fields, nothing else. No paid placements, no affiliate links. A field that is not yet verified scores zero, so missing data can only lower a rank.</p>
<div class="formula">score (max {MAX}) =
  KYC          none 3 · risk-based 1
+ custody      non-custodial 3 · hybrid 2 · custodial 0
+ native BTC   1 if verified yes
+ Solana       1 if verified yes
+ own fee      stated fee: max(0, 2 - 2 × fee%) · route-only 1 · unpublished 0
+ chains       1 if 30 or more
+ verified     1 if fee and coverage confirmed on an official page
ties: more chains first, then name</div>
<p class="legend">Methodology from the dataset: {e(d["methodology"])}</p>
</section>

<section id="types">
<h2>Swap types, and what they mean in a hurry</h2>
<p class="lead">The type of app decides more than its fee does: who can freeze your funds, whether a flagged swap gets stuck, and how many chains you reach.</p>
<div class="grid2">
<div class="box"><h3>Aggregators</h3><p>Race several bridges and protocols for each quote and route through the best one. Funds stay in contracts or your wallet, so nobody can hold them mid-swap.</p></div>
<div class="box"><h3>Protocol front-ends</h3><p>Independent interfaces on THORChain, Maya or Chainflip. Native BTC in and out without wrapping, non-custodial vaults, fixed front-end fee on top of the protocol fee.</p></div>
<div class="box"><h3>Wallets</h3><p>Cross-chain swap inside the wallet you already use. Convenient, but the fee is often not published and you are limited to the wallet's partners.</p></div>
<div class="box"><h3>Instant exchanges</h3><p>No account, send coins to an address, receive on the other chain. Fast and simple, but custodial: the operator holds your funds and risk-based checks can pause a flagged swap for KYC.</p></div>
<div class="box"><h3>Exchange aggregators</h3><p>Compare instant exchanges side by side. Same custody and KYC caveats as the exchange you end up using.</p></div>
</div>
</section>

<section id="details">
<h2>Top 20 in detail</h2>
<p class="lead">Facts as recorded in the dataset, with the official page each one was checked against.</p>
<div class="cards">
{chr(10).join(cards)}
</div>
</section>

<section id="protocols">
<h2>Protocols underneath</h2>
<p class="lead">Most apps route through these. They are listed for reference and are not ranked, since a protocol is not something you open in a hurry; its own first-party front-end counts as the protocol.</p>
<ul class="plain">{proto_li}</ul>
</section>

<section id="inactive">
<h2>Inactive or shut down</h2>
<p class="lead">Checked and excluded from the ranking. Do not send funds to these.</p>
<ul class="plain">{inactive_li}</ul>
</section>

<section id="data">
<h2>Data</h2>
<p class="lead">Free to reuse under {e(d["license"])} with attribution to <a href="{e(d["publisher_url"])}">{e(d["publisher"])}</a>. Corrections are welcome as GitHub issues or pull requests; every change goes through validation and this page rebuilds itself.</p>
<div class="dl">
<a class="btn pri" href="{RAW}/cross-chain-swaps.json">JSON</a>
<a class="btn" href="{RAW}/cross-chain-swaps.csv">CSV</a>
<a class="btn" href="{REPO}/blob/main/DATA.md">Full table (Markdown)</a>
<a class="btn" href="{REPO}">GitHub repo</a>
<a class="btn" href="{e(d["canonical"])}">Write-up</a>
</div>
</section>
</main>
<footer class="site"><div class="wrap">Dataset maintained by <a href="{e(d["publisher_url"])}">{e(d["publisher"])}</a>, which also runs one of the listed apps (Shieldz Swap); it is scored by the same formula as every other row. v{e(version)}, {c["total"]} apps tracked ({c["active"]} active, {c["inactive"]} inactive), updated {e(updated)}.</div></footer>
<script>
(()=>{{const t=document.getElementById('t'),tb=t.tBodies[0],rows=[...tb.rows],$=id=>document.getElementById(id);
const f=()=>{{const q=$('q').value.trim().toLowerCase(),cat=$('cat').value;let n=0;
for(const r of rows){{const d=r.dataset,ok=(!q||r.textContent.toLowerCase().includes(q))&&(!cat||d.cat===cat)&&(!$('fkyc').checked||d.kyc==='none')&&(!$('fnc').checked||d.cus==='non-custodial')&&(!$('fbtc').checked||d.btc==='1')&&(!$('fsol').checked||d.sol==='1')&&(!$('fver').checked||d.ver==='1');r.hidden=!ok;if(ok)n++}}
$('cnt').textContent=n+' of '+rows.length+' apps'}};
['q','cat','fkyc','fnc','fbtc','fsol','fver'].forEach(id=>$(id).addEventListener('input',f));f();
[...t.tHead.rows[0].cells].forEach((th,i)=>{{if(!th.dataset.k)return;th.addEventListener('click',()=>{{const asc=th.getAttribute('aria-sort')!=='ascending';
[...t.tHead.rows[0].cells].forEach(c=>c.removeAttribute('aria-sort'));th.setAttribute('aria-sort',asc?'ascending':'descending');
const v=r=>r.cells[i].dataset.v,num=th.dataset.k==='n';
rows.sort((a,b)=>{{const x=v(a),y=v(b),c=num?x-y:x.localeCompare(y);return asc?c:-c}});rows.forEach(r=>tb.appendChild(r))}})}})}})();
</script>
</body>
</html>
"""

(out_dir / "index.html").write_text(page)
(out_dir / ".nojekyll").write_text("")
print(f"wrote {out_dir / 'index.html'} ({n} ranked, {len(inactive)} inactive)")
