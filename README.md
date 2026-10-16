# Open Badge SD-JWT VC type

SD-JWT VC Type Metadata for issuing [Open Badges 3.0](https://www.imsglobal.org/spec/ob/v3p0) credentials as [IETF SD-JWT VCs](https://datatracker.ietf.org/doc/draft-ietf-oauth-sd-jwt-vc/) (`dc+sd-jwt`), so that wallets that don't understand JSON-LD can still store and show them. Any Open Badge issuer can use this `vct`:

```text
https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT
```

The type metadata is served at that URL, from [`credentials/v1/OpenBadgeVCT`](credentials/v1/OpenBadgeVCT) in this repository (GitHub Pages, custom domain in `CNAME`).

## Claims

The SD-JWT payload is the `OpenBadgeCredential` turned into flat JSON claims. Property names and value formats are the ones Open Badges 3.0 uses, so the mapping is mechanical:

| Open Badges 3.0 | SD-JWT VC claim |
| --- | --- |
| `@context`, `type` (everywhere, also in nested objects), `proof` | left out |
| `id` | `jti` (optional) |
| `issuer` | `iss`: the URL of the signing issuer. Its keys are published at `<iss origin>/.well-known/jwt-vc-issuer` |
| `validFrom`, `validUntil` | `nbf`, `exp` (optional) |
| `credentialStatus` | `status` (optional) |
| `credentialSubject.id` | `sub` (optional) |
| other `credentialSubject` properties: `achievement`, `result`, `creditsEarned`, `activityStartDate`, `activityEndDate`, `term`, `identifier`, `role`, … | top-level claims of the same name |
| other credential properties: `name`, `description`, `image`, `awardedDate`, `evidence`, … | top-level claims of the same name |

The organisation that awarded the achievement is `achievement.creator` (an Open Badges `Profile`, without `type`). `iss` names the service that signed the credential, which may be a different party.

`achievement` is the only required claim. Holder binding (`cnf`) is up to the issuer.

Example payload (before the issuer adds `iss`, `iat` and `cnf`):

```json
{
  "vct": "https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT",
  "vct#integrity": "sha256-…",
  "sub": "urn:oid:1.2.246.562.24.00000000001",
  "awardedDate": "2021-06-01T00:00:00Z",
  "achievement": {
    "id": "urn:opintopolku2openbadge:11b07ca1a4c8a2ef",
    "achievementType": "BachelorDegree",
    "name": "Luonnontieteiden kandidaatti",
    "fieldOfStudy": "Tietojenkäsittelytiede",
    "criteria": { "narrative": "…" },
    "creator": { "id": "urn:oid:1.2.246.562.10.39218317368", "name": "Helsingin yliopisto" }
  }
}
```

## Integrity

Issuers can add `vct#integrity` (an [SRI](https://www.w3.org/TR/SRI/) hash of the exact bytes served at the `vct` URL) so wallets can detect a changed definition:

```sh
printf 'sha256-%s\n' "$(openssl dgst -sha256 -binary credentials/v1/OpenBadgeVCT | base64)"
```

Any change to the file changes the hash, which breaks `vct#integrity` in credentials already issued. So don't change `v1` once issuers use it: fix typos only before then, and publish incompatible changes as `credentials/v2/…`.

## Hosting notes

- GitHub Pages serves a file without an extension as `application/octet-stream`, not `application/json`. Check that wallets accept this before relying on it. If one doesn't, put a proxy that sets the header (for example Cloudflare) in front, or move the definition to a `.json` URL.
- `.nojekyll` makes Pages serve the files as they are.
