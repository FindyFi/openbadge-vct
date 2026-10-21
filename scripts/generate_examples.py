#!/usr/bin/env python3
"""Generate the signed SD-JWT VC example files in examples/sd-jwt-vc/.

For each example <name> (openbadge, student-status), reads
examples/sd-jwt-vc/<name>-claims.json (the credential as flat claims),
makes the top-level claims selectively disclosable, signs the result with
a fresh ES256 issuer key and writes:

    <name>.sd-jwt            the issued SD-JWT (JWT~disclosure~...~)
    <name>-header.json       decoded JWT header
    <name>-payload.json      decoded JWT payload (with _sd digests)
    <name>-disclosures.json  decoded disclosures
    ../jwt-vc-issuer.json    issuer metadata with the public key

Claims that the type metadata marks "sd": "never" stay visible. The
Open Badge VCT doesn't mark any, so every Open Badge claim is disclosable.

Run:  python3 scripts/generate_examples.py
Requires: pip install cryptography
"""

import base64
import hashlib
import json
import secrets
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "sd-jwt-vc"
ISSUER = "https://badges.example.com"
KID = "badge-signing-key-1"
IAT = 1792108800  # 2026-10-16T00:00:00Z
# Claims that stay visible: needed to validate or process the credential.
ALWAYS_VISIBLE = {"iss", "iat", "nbf", "exp", "vct", "vct#integrity", "cnf", "status"}
SITE = "https://openbadge.digicredential.eu/"
EXAMPLES = ["openbadge", "student-status"]


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_json(obj) -> str:
    return b64url(json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode())


def public_jwk(key: ec.EllipticCurvePrivateKey, **extra) -> dict:
    nums = key.public_key().public_numbers()
    return {
        "kty": "EC",
        "crv": "P-256",
        "x": b64url(nums.x.to_bytes(32, "big")),
        "y": b64url(nums.y.to_bytes(32, "big")),
        **extra,
    }


def sign_es256(key: ec.EllipticCurvePrivateKey, data: bytes) -> bytes:
    r, s = decode_dss_signature(key.sign(data, ec.ECDSA(hashes.SHA256())))
    return r.to_bytes(32, "big") + s.to_bytes(32, "big")


def write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {path.relative_to(ROOT)}")


def never_disclosable(vct: str) -> set:
    """Top-level claims that the type metadata at vct marks "sd": "never"."""
    metadata = json.loads((ROOT / (vct[len(SITE):] + ".json")).read_text())
    return {
        c["path"][0] for c in metadata.get("claims", [])
        if c.get("sd") == "never" and len(c["path"]) == 1
    }


def issue(name: str, issuer_key: ec.EllipticCurvePrivateKey) -> None:
    claims = json.loads((OUT / f"{name}-claims.json").read_text())
    holder_key = ec.generate_private_key(ec.SECP256R1())
    visible = ALWAYS_VISIBLE | never_disclosable(claims["vct"])

    payload = {"iss": ISSUER, "iat": IAT}
    payload.update({k: v for k, v in claims.items() if k in visible})
    payload["cnf"] = {"jwk": public_jwk(holder_key)}

    disclosures, decoded = [], []
    for claim, value in claims.items():
        if claim in visible:
            continue
        disclosure = [b64url(secrets.token_bytes(16)), claim, value]
        encoded = b64url_json(disclosure)
        disclosures.append(encoded)
        decoded.append({
            "digest": b64url(hashlib.sha256(encoded.encode("ascii")).digest()),
            "disclosure": encoded,
            "contents": disclosure,
        })
    payload["_sd"] = sorted(d["digest"] for d in decoded)
    payload["_sd_alg"] = "sha-256"

    header = {"alg": "ES256", "typ": "dc+sd-jwt", "kid": KID}
    signing_input = f"{b64url_json(header)}.{b64url_json(payload)}"
    jwt = f"{signing_input}.{b64url(sign_es256(issuer_key, signing_input.encode()))}"
    # No Key Binding JWT: SD-JWT ends with "~" after the last disclosure.
    sd_jwt = jwt + "".join(f"~{d}" for d in disclosures) + "~"

    (OUT / f"{name}.sd-jwt").write_text(sd_jwt + "\n")
    print(f"wrote {(OUT / f'{name}.sd-jwt').relative_to(ROOT)}")
    write_json(OUT / f"{name}-header.json", header)
    write_json(OUT / f"{name}-payload.json", payload)
    write_json(OUT / f"{name}-disclosures.json", decoded)


def main():
    issuer_key = ec.generate_private_key(ec.SECP256R1())
    for name in EXAMPLES:
        issue(name, issuer_key)
    write_json(ROOT / "examples" / "jwt-vc-issuer.json", {
        "issuer": ISSUER,
        "jwks": {"keys": [public_jwk(issuer_key, kid=KID, use="sig", alg="ES256")]},
    })


if __name__ == "__main__":
    main()
