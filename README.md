# Cross-Chain Swaps Dataset (2026) — working draft

An open dataset of every app, protocol, wallet and exchange that swaps an asset on one chain for an asset on another: native cross-chain DEXes, intent networks, bridges, aggregators, THORChain/Maya/Chainflip front-ends, wallet swaps and custodial instant exchanges. Each is classified by **who holds your funds while the swap is in flight**, user KYC, interface fee, routing, native Bitcoin and Solana support, and chain coverage.

Sister dataset to the [Crypto Payment Gateways Dataset](https://github.com/ShieldZCash/crypto-payment-gateways-dataset). Maintained by [Shieldz](https://shieldz.cash).

> **Status: v0.1.0, not yet published.** 93 rows, 83 confirmed live on 2026-10-10. Categories and custody are first-pass editorial classifications; fees, chain counts and most coverage flags are `null` until verified against each official page. Do not quote figures from this draft.

## Files

| File | Contents |
| --- | --- |
| `data/cross-chain-swaps.json` | Source of truth: rows, field dictionary, methodology, computed counts and summary |
| `data/cross-chain-swaps.csv` | Same rows as CSV (generated) |
| `DATA.md` | Full table grouped by category, plus inactive apps (generated) |

## Editing

Edit only the `apps` array in the JSON, then:

```bash
python3 tools/build.py      # recompute counts/summary, regenerate CSV and DATA.md
python3 tools/validate.py   # schema and consistency checks (also run in CI)
```

A row may only be `verified: true` with a `fee_pct` and the `source_url` it was read from. Fee statistics in the summary use verified rows only, so an unverified row can never move a published number. Inactive apps stay in the file with a `status_note` saying what was found.

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: Shieldz (https://shieldz.cash).
