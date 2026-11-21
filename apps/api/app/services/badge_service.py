from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519
from pydantic import BaseModel

# Pre-generated deterministic demonstration keypair for dev & testing
# In production, private key is injected via secure environment variable
_DEV_SEED = b"ThinkFreeMasterKeyForEd25519BadgeSignatures12345"[:32]
_DEV_PRIVATE_KEY = ed25519.Ed25519PrivateKey.from_private_bytes(_DEV_SEED)
_DEV_PUBLIC_KEY = _DEV_PRIVATE_KEY.public_key()
PUBLIC_KEY_HEX = _DEV_PUBLIC_KEY.public_bytes_raw().hex()


class BadgeVerificationResult(BaseModel):
    is_valid: bool
    badge_id: str
    student_id: str
    kind: str
    title: str
    issuer: str
    issued_at: datetime
    metrics: Dict[str, Any]
    error: Optional[str] = None


class BadgeService:
    """
    Feature 11: Verified-Independent-Performance Badges.
    Signs and verifies tamper-evident badges using Ed25519 digital signatures.
    """

    @classmethod
    def create_badge_payload(
        cls,
        student_id: str,
        kind: str,
        title: str,
        institution_name: str,
        its_score: float,
        adr_score: float,
        self_solves_count: int,
        issued_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Builds the canonical JSON payload for a badge.
        """
        issue_time = issued_at or datetime.utcnow()
        return {
            "version": "1.0",
            "issuer": f"ThinkFree Verified ({institution_name})",
            "student_id": student_id,
            "kind": kind,
            "title": title,
            "criteria": {
                "min_its": 80.0,
                "achieved_its": round(its_score, 1),
                "max_adr": 0.25,
                "achieved_adr": round(adr_score, 3),
                "self_solves": self_solves_count
            },
            "issued_at": issue_time.isoformat()
        }

    @classmethod
    def sign_payload(cls, payload: Dict[str, Any], private_key: Optional[ed25519.Ed25519PrivateKey] = None) -> str:
        """
        Signs the canonical sorted JSON serialization using Ed25519.
        Returns URL-safe Base64 signature string.
        """
        key = private_key or _DEV_PRIVATE_KEY
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature_bytes = key.sign(canonical_bytes)
        return base64.urlsafe_b64encode(signature_bytes).decode("ascii")

    @classmethod
    def verify_badge(
        cls,
        badge_id: str,
        payload: Dict[str, Any],
        signature_str: str,
        public_key: Optional[ed25519.Ed25519PublicKey] = None
    ) -> BadgeVerificationResult:
        """
        Verifies the cryptographic signature of a badge payload.
        """
        pub_key = public_key or _DEV_PUBLIC_KEY
        canonical_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        try:
            signature_bytes = base64.urlsafe_b64decode(signature_str.encode("ascii"))
            pub_key.verify(signature_bytes, canonical_bytes)
            issued_at_dt = datetime.fromisoformat(payload.get("issued_at", datetime.utcnow().isoformat()))
            return BadgeVerificationResult(
                is_valid=True,
                badge_id=badge_id,
                student_id=payload.get("student_id", "unknown"),
                kind=payload.get("kind", "badge"),
                title=payload.get("title", "Verified Independent Badge"),
                issuer=payload.get("issuer", "ThinkFree"),
                issued_at=issued_at_dt,
                metrics=payload.get("criteria", {})
            )
        except (InvalidSignature, ValueError, Exception) as exc:
            return BadgeVerificationResult(
                is_valid=False,
                badge_id=badge_id,
                student_id=payload.get("student_id", "unknown"),
                kind=payload.get("kind", "badge"),
                title=payload.get("title", "Invalid Badge"),
                issuer=payload.get("issuer", "ThinkFree"),
                issued_at=datetime.utcnow(),
                metrics={},
                error=f"Signature verification failed: {str(exc)}"
            )
