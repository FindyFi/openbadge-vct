# Open Badges as SD-JWT VCs

This repository publishes SD-JWT VC Type Metadata for issuing [Open Badges 3.0](https://www.imsglobal.org/spec/ob/v3p0) credentials as [IETF SD-JWT VCs](https://datatracker.ietf.org/doc/draft-ietf-oauth-sd-jwt-vc/) (`dc+sd-jwt`). With it you can issue a badge to EUDI and other OpenID4VC wallets that don't process JSON-LD. Any issuer can use this `vct`:

```text
https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT
```

Wallets fetch the type metadata from that URL. It gives the credential's name and colours, labels for the claims in English, Finnish, German, Spanish, French, Dutch and Swedish, and an [SVG card template](#card-template).

## Issuing a badge

1. Turn your `OpenBadgeCredential` into flat JSON claims ([mapping](#claims)).
2. Sign them as an SD-JWT with `"typ": "dc+sd-jwt"` and `"vct"` set to the URL above ([example](#example-credential)).
3. Publish your signing key at `https://<your issuer>/.well-known/jwt-vc-issuer` ([example](#issuer-key)).
4. Offer the credential over [OpenID4VCI](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html) with a `dc+sd-jwt` credential configuration ([example](#openid4vci-issuer-metadata)).

## Claims

The claims are the `OpenBadgeCredential` as plain JSON. Property names and value formats are the ones Open Badges 3.0 uses, so you can convert the credential mechanically:

| Open Badges 3.0 | SD-JWT VC claim |
| --- | --- |
| `@context`, `type` (everywhere, also in nested objects), `proof` | left out |
| `id` | `jti` (optional) |
| `issuer` | `iss`: the URL of the signing issuer. Its keys are published at `<iss origin>/.well-known/jwt-vc-issuer` |
| `validFrom`, `validUntil` | `nbf`, `exp` (optional) |
| `credentialStatus` | `status` (optional), for example an [IETF Token Status List](https://datatracker.ietf.org/doc/draft-ietf-oauth-status-list/) entry |
| `credentialSubject.id` | `sub` (optional) |
| other `credentialSubject` properties: `achievement`, `result`, `creditsEarned`, `activityStartDate`, `activityEndDate`, `term`, `identifier`, `role`, … | top-level claims of the same name |
| other credential properties: `name`, `description`, `image`, `awardedDate`, `evidence`, … | top-level claims of the same name |

`achievement` is the only required claim.

The organisation that awarded the achievement is `achievement.creator`, an Open Badges `Profile` without `type`. `iss` names the service that signed the credential, which can be a different party, such as a badge platform signing on behalf of a university.

Holder binding (`cnf`) is up to you. Use it if verifiers should be able to check that the person presenting the badge is the one it was issued to.

You decide which claims are selectively disclosable. The example makes every top-level claim disclosable, so the holder can, for example, show the `achievement` without their `sub` or `creditsEarned`.

## Card template

Wallets that support SVG templates show the badge as a card drawn from [`templates/svg/OpenBadge_v1.svg`](templates/svg/OpenBadge_v1.svg). The template has no fixed text, so one file serves every language. The wallet fills in these claims:

| Placeholder | Claim |
| --- | --- |
| `{{achievement_name}}` | `achievement.name` |
| `{{field_of_study}}` | `achievement.fieldOfStudy` |
| `{{creator_name}}` | `achievement.creator.name` |
| `{{awarded_date}}` | `awardedDate` (only the date part is shown) |
| `{{achievement_image}}` | `achievement.image.id`, shown in the medal |

Long names wrap onto several lines in wallets that render HTML inside SVG (`foreignObject`). Other wallets show each name on one line, cut off at the edge of the card.

The badge image is loaded from its URL, and some wallets don't load external images. A `data:` URL works everywhere. If no image loads, the medal shows a star.

## Example credential

All of the example files are in [`examples/`](examples/). The badge, written as claims before signing, is [`openbadge-claims.json`](examples/sd-jwt-vc/openbadge-claims.json):

```json
{
  "vct": "https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT",
  "jti": "urn:uuid:7c1d4e2a-9f3b-4a6c-8e5d-2b7f0a913c48",
  "status": {
    "status_list": { "idx": 4182, "uri": "https://badges.example.com/status/1" }
  },
  "sub": "urn:uuid:3f9a2c7e-5b1d-4e8f-a6c4-0d2e7b9f1a35",
  "name": "Bachelor of Science in Computer Science",
  "awardedDate": "2026-06-12T00:00:00Z",
  "achievement": {
    "id": "urn:uuid:a4e6c2b8-1d3f-4b5a-9c7e-6f8d0a2b4c19",
    "achievementType": "BachelorDegree",
    "name": "Bachelor of Science",
    "description": "First-cycle degree in computer science (180 ECTS credits).",
    "fieldOfStudy": "Computer Science",
    "creditsAvailable": 180,
    "criteria": {
      "narrative": "Complete 180 ECTS credits of studies, including a bachelor's thesis."
    },
    "image": {
      "id": "https://badges.example.com/images/bsc-computer-science.png",
      "caption": "Bachelor of Science badge"
    },
    "creator": {
      "id": "urn:uuid:5e7b9d1f-3a2c-4e6b-8d0f-1c3a5e7b9d24",
      "name": "Example University",
      "url": "https://university.example.com"
    }
  },
  "creditsEarned": 180,
  "activityStartDate": "2023-09-01T00:00:00Z",
  "activityEndDate": "2026-05-31T00:00:00Z"
}
```

The issuer signs it as an SD-JWT. The JWT header ([`openbadge-header.json`](examples/sd-jwt-vc/openbadge-header.json)) names the key from the issuer's `jwt-vc-issuer` metadata:

```json
{
  "alg": "ES256",
  "typ": "dc+sd-jwt",
  "kid": "badge-signing-key-1"
}
```

The JWT payload ([`openbadge-payload.json`](examples/sd-jwt-vc/openbadge-payload.json)) keeps `iss`, `iat`, `vct`, `status` and `cnf` visible. The other claims are replaced with digests in `_sd`:

```json
{
  "iss": "https://badges.example.com",
  "iat": 1792108800,
  "vct": "https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT",
  "status": {
    "status_list": { "idx": 4182, "uri": "https://badges.example.com/status/1" }
  },
  "cnf": {
    "jwk": { "kty": "EC", "crv": "P-256", "x": "…", "y": "…" }
  },
  "_sd": ["-N5Z0Wjl9oQ-…", "7AJpGy1akaA5…", "…"],
  "_sd_alg": "sha-256"
}
```

Each disclosure ([`openbadge-disclosures.json`](examples/sd-jwt-vc/openbadge-disclosures.json)) is a base64url-encoded `[salt, name, value]` array:

```json
["VgojrMyuF50OpEPEi7WhJA", "achievement", { "id": "urn:uuid:a4e6c2b8-…", "achievementType": "BachelorDegree", … }]
```

The issued credential, [`openbadge.sd-jwt`](examples/sd-jwt-vc/openbadge.sd-jwt), is the signed JWT followed by the disclosures, each one after a `~`:

```text
eyJhbGciOiJFUzI1NiIsInR5cCI6ImRjK3NkLWp3dCIsImtpZCI6ImJhZGdlLXNpZ25pbmcta2V5LTEifQ.eyJpc3Mi…~WyItalRnN1pE…~…~
```

You can paste it into [sdjwt.info](https://www.sdjwt.info/) to decode it.

### Issuer key

Wallets and verifiers find the key that signed the credential at `https://badges.example.com/.well-known/jwt-vc-issuer` ([`jwt-vc-issuer.json`](examples/jwt-vc-issuer.json)):

```json
{
  "issuer": "https://badges.example.com",
  "jwks": {
    "keys": [
      { "kty": "EC", "crv": "P-256", "x": "…", "y": "…", "kid": "badge-signing-key-1", "use": "sig", "alg": "ES256" }
    ]
  }
}
```

You can sign with an X.509 certificate chain (`x5c` in the header) instead.

## OpenID4VCI issuer metadata

Advertise the credential in `/.well-known/openid-credential-issuer` with a `dc+sd-jwt` configuration that names the `vct` ([`openid-credential-issuer.json`](examples/openid-credential-issuer.json)):

```json
"credential_configurations_supported": {
  "OpenBadge_dc+sd-jwt": {
    "format": "dc+sd-jwt",
    "vct": "https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT",
    "scope": "OpenBadge",
    "cryptographic_binding_methods_supported": ["jwk"],
    "credential_signing_alg_values_supported": ["ES256"],
    "proof_types_supported": {
      "jwt": { "proof_signing_alg_values_supported": ["ES256"] }
    },
    "credential_metadata": {
      "display": [{ "locale": "en", "name": "Open Badge", "background_color": "#1f3a5f", "text_color": "#ffffff" }],
      "claims": [
        { "path": ["achievement", "name"], "mandatory": true, "display": [{ "locale": "en", "name": "Achievement name" }] },
        …
      ]
    }
  }
}
```

The type metadata already carries display information in seven languages. In `credential_metadata`, add only what your wallets need, or what's specific to your badges, such as your own colours or logo.

## Requesting a badge

Verifiers can ask for a badge over [OpenID4VP](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html) with a [DCQL](https://openid.net/specs/openid-4-verifiable-presentations-1_0.html#name-digital-credentials-query-l) query ([`dcql-query.json`](examples/dcql-query.json)). This one asks for any bachelor's degree badge:

```json
{
  "credentials": [
    {
      "id": "badge",
      "format": "dc+sd-jwt",
      "meta": {
        "vct_values": ["https://openbadge.digicredential.eu/credentials/v1/OpenBadgeVCT"]
      },
      "claims": [
        { "path": ["achievement", "name"] },
        { "path": ["achievement", "achievementType"], "values": ["BachelorDegree"] },
        { "path": ["achievement", "creator", "name"] },
        { "path": ["awardedDate"] }
      ]
    }
  ]
}
```

## Regenerating the examples

`scripts/generate_examples.py` signs `openbadge-claims.json` with a new ES256 key and rewrites the other files in `examples/`. It needs `pip install cryptography`.

```sh
python3 scripts/generate_examples.py
```

## Versions

The `v1` type won't change in a way that breaks existing credentials. Incompatible changes will be published under a new URL (`credentials/v2/…`).
