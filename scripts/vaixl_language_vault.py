#!/usr/bin/env python3
"""VAIXLNS private language vault binding.

Raw identity data, phone data, unlock codes, and vault keys are runtime secrets.
They are never written to the repository, manifests, evidence, or logs.

The repository stores only a sanitized lock contract and opaque cryptographic
references. Production secret material belongs in Vault/HSM/KMS.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

VAULT_ID = "VAIXLNS-PRIVATE-LANGUAGE-VAULT-001"
SCHEMA_VERSION = "vaixlns.private_language_vault.v1"
_LOCKED = "LOCKED"
_REVOKED = "REVOKED"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hmac_sha256(key: str, value: str) -> str:
    return hmac.new(
        key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def normalize_secret(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def subject_binding(identity_value: str, phone_value: str, binding_key: str) -> str:
    identity = normalize_secret(identity_value)
    phone = normalize_secret(phone_value)
    if not identity or not phone:
        raise ValueError("identity and phone values are required at runtime")
    if not binding_key:
        raise ValueError("binding_key is required")
    material = f"VAIXLNS-SUBJECT-V1|{identity}|{phone}"
    return hmac_sha256(binding_key, material)


def unlock_proof(binding_id: str, unlock_code: str, proof_key: str) -> str:
    code = normalize_secret(unlock_code)
    if not binding_id or not code or not proof_key:
        raise ValueError("binding_id, unlock_code, and proof_key are required")
    return hmac_sha256(proof_key, f"VAIXLNS-UNLOCK-V1|{binding_id}|{code}")


def build_lock_manifest(
    language_ids: list[str],
    vault_ref: str,
    binding_id: str,
    proof: str,
) -> dict[str, Any]:
    languages = sorted({str(v).strip() for v in language_ids if str(v).strip()})
    if not languages:
        raise ValueError("at least one language id is required")
    if not vault_ref or not binding_id or not proof:
        raise ValueError("vault_ref, binding_id, and proof are required")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "vault_id": VAULT_ID,
        "state": _LOCKED,
        "language_ids": languages,
        "storage": {
            "backend": "EXTERNAL_SECRET_VAULT",
            "vault_ref": vault_ref,
            "raw_source_persistence": False,
            "raw_identity_persistence": False,
            "raw_phone_persistence": False,
            "raw_unlock_code_persistence": False,
        },
        "binding": {
            "algorithm": "HMAC-SHA256",
            "binding_id": binding_id,
            "proof_id": hashlib.sha256(proof.encode("utf-8")).hexdigest(),
        },
        "authority": {
            "unlock_requires_external_secret": True,
            "self_unlock": False,
            "self_promotion": False,
        },
        "privacy": {
            "repository_contains_raw_identity": False,
            "repository_contains_raw_phone": False,
            "repository_contains_unlock_code": False,
        },
        "provenance": {
            "created_by": VAULT_ID,
            "created_at": "RUNTIME_ONLY",
        },
    }
    manifest["manifest_hash"] = hashlib.sha256(canonical(manifest).encode("utf-8")).hexdigest()
    return manifest


def verify_lock_manifest(manifest: Mapping[str, Any], binding_id: str, unlock_code: str, proof_key: str) -> bool:
    if manifest.get("state") != _LOCKED:
        return False
    stored_binding = manifest.get("binding", {}).get("binding_id")
    stored_proof_id = manifest.get("binding", {}).get("proof_id")
    if stored_binding != binding_id or not stored_proof_id:
        return False
    proof = unlock_proof(binding_id, unlock_code, proof_key)
    return hmac.compare_digest(stored_proof_id, hashlib.sha256(proof.encode("utf-8")).hexdigest())


def _runtime_secret(name: str, prompt: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    return getpass.getpass(prompt)


def main() -> int:
    parser = argparse.ArgumentParser(description="VAIXLNS private language vault binding")
    parser.add_argument("command", choices=["lock", "verify"])
    parser.add_argument("--manifest", default="")
    parser.add_argument("--language", action="append", default=[])
    parser.add_argument("--vault-ref", default="")
    parser.add_argument("--identity-env", default="VAIXLNS_SUBJECT_ID")
    parser.add_argument("--phone-env", default="VAIXLNS_SUBJECT_PHONE")
    parser.add_argument("--binding-key-env", default="VAIXLNS_BINDING_KEY")
    parser.add_argument("--unlock-code-env", default="VAIXLNS_UNLOCK_CODE")
    parser.add_argument("--proof-key-env", default="VAIXLNS_PROOF_KEY")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.command == "lock":
        identity = _runtime_secret(args.identity_env, "Identity value (runtime only): ")
        phone = _runtime_secret(args.phone_env, "Phone value (runtime only): ")
        binding_key = _runtime_secret(args.binding_key_env, "Binding key (runtime only): ")
        unlock_code = _runtime_secret(args.unlock_code_env, "Unlock code (runtime only): ")
        proof_key = _runtime_secret(args.proof_key_env, "Proof key (runtime only): ")

        binding_id = subject_binding(identity, phone, binding_key)
        proof = unlock_proof(binding_id, unlock_code, proof_key)
        manifest = build_lock_manifest(args.language, args.vault_ref, binding_id, proof)
        rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0

    if not args.manifest:
        raise ValueError("--manifest is required for verify")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    identity = _runtime_secret(args.identity_env, "Identity value (runtime only): ")
    phone = _runtime_secret(args.phone_env, "Phone value (runtime only): ")
    binding_key = _runtime_secret(args.binding_key_env, "Binding key (runtime only): ")
    unlock_code = _runtime_secret(args.unlock_code_env, "Unlock code (runtime only): ")
    proof_key = _runtime_secret(args.proof_key_env, "Proof key (runtime only): ")
    binding_id = subject_binding(identity, phone, binding_key)
    ok = verify_lock_manifest(manifest, binding_id, unlock_code, proof_key)
    print(json.dumps({"verified": ok, "raw_secrets_persisted": False}, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
