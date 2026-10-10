# Cross-Chain Swap Apps Dataset (2026, updated monthly)

An open, hand-verified dataset of **81 cross-chain swap apps**: every wallet, aggregator, front-end and instant exchange that swaps a coin on one chain for a coin on another, classified by **who holds your funds while the swap is in flight**, user KYC, the app's own fee, routing, native Bitcoin and Solana support. Every verified fee links to the official page it was read from.

Maintained by [Shieldz](https://shieldz.cash). Current version: **v1.0.1, October 2026**. Sister dataset to the [Crypto Payment Gateways Dataset](https://github.com/ShieldZCash/crypto-payment-gateways-dataset).

Write-up: [81 cross-chain swap apps compared: fees, custody and KYC (October 2026)](https://shieldz.cash/blog/81-cross-chain-swap-apps-compared)

## Key findings (n=81 active apps, 10 October 2026)

- **70% state no fee you can check in advance.** Only 24 of 81 state a fixed fee on a current official page. 15 claim "no fee of their own", which means the whole cost is set by the route or partner (often including a commission paid back to the app); these are recorded as `route-only`, not 0%, and are excluded from fee statistics.
- **Wallets are the most expensive place to swap:** median verified fee **0.875%**, against **0.25%** for aggregators.
- **The protocol underneath costs almost nothing** (NEAR Intents 0.0001%, deBridge 0.04%, Relay 0.06% on major pairs); the app sets the price. Five apps with a stated fee on the same NEAR Intents route charge from 0.15% to 1.5%.
- **30% are custodial during the swap** (24 of 81), 15% hybrid. **14 of 35 wallets** hand at least some cross-chain swaps to a custodial exchange.
- **30 of 81 can hold a flagged swap for KYC**, including all 15 instant exchanges.
- **11 apps and protocols are no longer working**, including Ctrl Wallet (shut down 19 August 2026) and Hop Protocol, whose domain now serves a gambling site.

## Apps, not protocols

The comparison contains only **apps**, the places a person presses "swap". The **protocols** those apps route through (THORChain, Maya, Chainflip, NEAR Intents, Relay, Across, deBridge, bridges) are a different layer: most apps sit on top of them, so ranking the two together would not be a fair comparison. A protocol's own first-party front-end counts as the protocol. Protocols are kept in a separate `protocols` array for reference.

## Files

| File | Contents |
| --- | --- |
| [`data/cross-chain-swaps.json`](data/cross-chain-swaps.json) | Source of truth: `apps`, `protocols`, field dictionary, methodology, computed counts and summary |
| [`data/cross-chain-swaps.csv`](data/cross-chain-swaps.csv) | Apps as CSV (generated) |
| [`data/cross-chain-protocols.csv`](data/cross-chain-protocols.csv) | Protocols as CSV (generated) |
| [`DATA.md`](DATA.md) | Full table by category, the protocols underneath, and inactive entries (generated) |

Live endpoints (same data): [shieldz.cash/blog/data/cross-chain-swaps-2026.json](https://shieldz.cash/blog/data/cross-chain-swaps-2026.json), [shieldz.cash/blog/data/cross-chain-swaps-2026.csv](https://shieldz.cash/blog/data/cross-chain-swaps-2026.csv)

## Fields

| Field | Meaning |
| --- | --- |
| `name`, `url` | App name and official website |
| `category` | Apps: `aggregator` · `frontend` (independent interface on THORChain/Maya/Chainflip) · `wallet` · `instant-exchange` (custodial, no account) · `exchange-aggregator` (compares instant exchanges). Protocols: `native-dex` · `intent-network` · `bridge` |
| `custody` | During the swap: `non-custodial` (contracts, vaults or your wallet throughout) · `custodial` (an operator's wallet receives first) · `hybrid` (depends on route) |
| `kyc` | `none` · `risk-based` (no account, but flagged swaps can be held for KYC) · `required` |
| `fee_type` | `stated` (the app adds a fixed %) · `route-only` (claims no fee of its own; cost set by the route or partner, not certain until quoted) · `unpublished` |
| `fee_pct` | The fixed percentage the app adds on a standard cross-chain swap when `fee_type=stated`, otherwise `null`. For a wallet that hands every swap to one custodial partner, the partner's stated commission |
| `fee_note` | What the fee page says, including tiers, discounts and contradictions |
| `routes_via` | Protocols and exchanges the app routes through |
| `native_btc`, `solana` | Native Bitcoin (not wrapped) and Solana support; `null` = not verified |
| `chains`, `founded` | Approximate chain count and launch year where stated |
| `status`, `status_note` | `active` · `inactive` · `unchecked`, and what was found |
| `verified` | `true` = fee stated on a current (within ~18 months), non-contradictory official page |
| `source_url`, `checked` | Page the fee was read from; date of the last pass |

## Methodology

Each app was loaded on the `checked` date by HTTP, then in a real browser where bot protection blocked plain requests, then scanned for shutdown notices. Fees, custody and coverage come only from the app's own pricing pages, help center, docs or terms. A fee counts as verified only when it is stated on a current official page and does not contradict the app's other pages; "starting from" figures without a schedule, stale pages and conflicting pages are recorded in `fee_note` with `verified=false`. Summary fee statistics use verified rows only, so an unverified row can never move a published number. Custody describes who holds the user's funds while the swap is in flight, not who holds the wallet keys.

## Editing

Edit only the `apps` and `protocols` arrays, bump `version`/`updated`, then:

```bash
python3 tools/build.py      # recompute counts/summary, regenerate CSVs and DATA.md
python3 tools/validate.py   # schema and consistency checks (also run in CI)
```

## Independence

Shieldz operates [Shieldz Swap](https://swap.shieldz.cash), which is one of the 81 apps and is held to the same rules as every other row. We do not accept paid placements or any exchange of money for how an app appears. If a row is wrong, open an issue or pull request with the official source and it will be fixed in the next monthly release.

## License

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: Shieldz (https://shieldz.cash).
