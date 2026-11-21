from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.badge_service import BadgeService, PUBLIC_KEY_HEX
from app.services.collaboration_engine import CollaborationEngine
from app.services.speech_service import SpeechService


def test_speech_service_fluency_analysis():
    transcript = (
        "I used a hashmap to store the complement of the target minus current number. "
        "The time complexity is O(n) linear time, and the space complexity is O(n) in the worst case. "
        "Um, this cleanly handles edge cases with empty arrays or negative integers."
    )
    fluency = SpeechService.analyze_verbal_fluency(transcript, duration_seconds=12.0)
    assert fluency["word_count"] > 20
    assert fluency["words_per_minute"] > 80
    assert "hashmap" in fluency["detected_keywords"] or "time complexity" in fluency["detected_keywords"]
    assert 0.0 <= fluency["fluency_score"] <= 1.0


@pytest.mark.asyncio
async def test_speech_service_transcribe_fallback():
    dummy_audio = b"\x00" * 32000
    res = await SpeechService.transcribe_audio(dummy_audio, filename="voice.webm", language="hi")
    assert "transcript" in res
    assert res["language"] == "hi"
    assert "fluency_telemetry" in res
    assert res["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_collaboration_engine_room_lifecycle():
    room = await CollaborationEngine.get_or_create_room(problem_id="prob-pair-1", language="javascript")
    assert room.room_code.startswith("TF-")
    assert room.language == "javascript"

    # Test divergence metrics initial state
    metrics = room.get_divergence_metrics()
    assert metrics["is_divergent"] is False

    # Retrieve room
    fetched = CollaborationEngine.get_room(room.room_code)
    assert fetched is not None
    assert fetched.room_code == room.room_code


def test_openbadges_v3_export():
    payload = BadgeService.create_badge_payload(
        student_id="student-test-99",
        kind="gold",
        title="Independent Algorithmic Thinker",
        institution_name="BITS Pilani",
        its_score=88.5,
        adr_score=0.15,
        self_solves_count=18
    )
    signature = BadgeService.sign_payload(payload)
    ob_v3 = BadgeService.to_openbadges_v3(
        badge_id="badge-uuid-1234",
        payload=payload,
        signature_str=signature
    )

    assert "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json" in ob_v3["@context"]
    assert "OpenBadgeCredential" in ob_v3["type"]
    assert ob_v3["proof"]["type"] == "Ed25519Signature2020"
    assert ob_v3["proof"]["proofValue"] == signature
    assert ob_v3["credentialSubject"]["achievement"]["name"] == "Independent Algorithmic Thinker"


@pytest.mark.asyncio
async def test_api_public_key_and_openbadge_endpoints(client: AsyncClient, sample_problem):
    # Verify public key endpoint
    pk_resp = await client.get("/api/v1/institutional/badges/public-key")
    assert pk_resp.status_code == 200
    data = pk_resp.json()
    assert data["algorithm"] == "Ed25519"
    assert data["public_key_hex"] == PUBLIC_KEY_HEX
