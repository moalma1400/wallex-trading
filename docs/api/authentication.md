# Authentication and API-key provenance

## New developer guide

- Key creation guide directs users to select the intended account, distinguishes main account from credit subaccounts, describes Read/Trade/Withdrawal permissions, says withdrawal permission has an IP matching requirement, key is shown only once, and at most three keys can be created. It does not specify an API request authentication header on that page. [CREATE-KEY](https://developers.wallex.ir/docs/create-api-key)
- The API introduction says personal/account and transaction-capable APIs are protected by API keys/security mechanisms but gives no exact auth header in the introductory page. [MOD-INTRO](https://developers.wallex.ir/docs)
- Spot introduction says use the matching main or credit-account API key, plus `sub-account-client-id` for credit-account Spot. [SPOT-INTRO](https://developers.wallex.ir/docs/spot-intro)

## Legacy reference

The legacy guide specifies `X-API-Key: <api-key>` in HTTP headers; it also says keys could be configured up to 90 days and empty IP allowlists mean all IPs. These key rules need current confirmation; do not assume the old header applies to every current endpoint. [LEGACY-API](https://api-docs.wallex.ir/)

No API key has been created or used. See [security boundary](../fa/account-and-api-keys.md). Current signature schemes, endpoint-specific permissions, renewal/revocation, and current key limits remain open questions.
