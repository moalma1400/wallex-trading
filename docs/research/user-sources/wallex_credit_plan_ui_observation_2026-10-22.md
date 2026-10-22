# Wallex credit-plan UI observation — 2026-10-22

**Evidence class:** user-provided screenshot; visual observation only. This is not an independently authenticated official terms page and does not establish contractual rights, final account state, or current platform behavior beyond what was displayed in the supplied image.

## Source identity

- Attachment name supplied by the chat runtime: `ksnip_20261022-185625.png`
- SHA-256 of the supplied screenshot bytes: `eafaed14af03fd7c7fa33f844220dd58ffb646aa0ec555fe6ed2412faee9b45d`
- Image dimensions: 676 × 882 pixels.
- The raw image is not archived in this repository; this note records its fingerprint and the observations below. Re-upload the original image if byte-level review is needed later.
- The user reports that the plan has become available/enabled for their account. The screenshot shows the plan setup/acceptance page and a `فعال کردن طرح` (“Activate plan”) button, so the image alone does **not** prove that activation has completed.

## Visible UI observations

The page is titled **«هکاتون استارکوچ | والکس»** and displays:

- Displayed trading credit: **5,000,000 TMN**.
- Displayed entry/user assets: **0 toman**.
- Displayed credit amount: **5,000,000 toman**.
- Displayed plan duration: **3 days**.
- A repayment indicator that reads **«بازپرداخت اعتبار ۳ روز رایگان!»** (“credit repayment: 3 days free!”). Treat this as wording shown in the UI, not a complete fee contract or proof that every charge is waived.
- The checkbox stating the user has read and accepts the plan terms is checked.
- The account description says that after the plan period ends or the user stops the plan, assets in the credit account are sold through Wallex Instant Sell and transferred to the main account according to the plan rules.

The displayed main-account versus credit-account capability table reads as follows:

| Capability | Main account | Credit account |
|---|---:|---:|
| Advanced trading | Available | Available |
| Instant buy and sell | Available | Available |
| Create/manage API | Available | Available |
| Margin trading | Available | Not available |
| Trading bots | Available | Not available |
| Deposit and withdrawal | Available | Not available |
| Transfer between accounts | Available | Not available |

Warning/liquidation threshold labels are present in the screenshot, but the small display does not support a reliable transcription of their exact values/units; they are intentionally not copied into configuration.

## What this does and does not resolve

This screenshot improves the evidence for the **displayed product configuration and permission table** compared with the earlier English summary, which had a malformed table and no screenshot. It supports recording the displayed three-day period and a “three days free” repayment indicator as user-supplied UI evidence.

It does **not** establish the exact eligible-market list, fee rules after the displayed free period, trading-fee rates, liquidation trigger/valuation/fees, debt or deficit liability, ownership/withdrawability of the displayed amount, final settlement, or whether the special challenge terms supersede Wallex’s general credit-plan terms. It also does not establish that plan activation has completed or that API functionality is enabled for a particular key/endpoint.

## Implementation consequence

Do not yet treat 5,000,000 toman as user-owned cash, infer that the plan is risk-free, invent warning/liquidation values, or enable margin/leverage/shorts. Before modeling the special financing, keep `credit_fee`, `liquidation`, principal/deficit liability, and final settlement explicitly `UNKNOWN` unless verified terms are supplied. For the first strategy smoke test, 5,000,000 can only be a clearly labelled **scenario input**; its reported return is not settlement-ready profit.
