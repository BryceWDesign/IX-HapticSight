from pathlib import Path

from ohip.schemas import SafetyLevel
from ohip_xr import XRHazardMarker, XRState


def test_xr_payload_exposes_safety_authority_and_markers():
    state = XRState(
        session_id="s",
        consent_active=True,
        safety_authority="DENY",
        force_cap_N=0.0,
        speed_cap_mps=0.0,
        controller_state="SAFE_HOLD",
        reason="red_hazard",
        markers=(XRHazardMarker("h", (0,0,1), .1, SafetyLevel.RED, "hot", .9),),
    )
    doc = state.to_dict()
    assert doc["markers"][0]["level"] == "RED"
    assert doc["safety_authority"] == "DENY"


def test_webxr_client_is_shipped():
    root = Path(__file__).resolve().parents[1]
    text = (root / "examples/webxr/index.html").read_text(encoding="utf-8")
    assert "navigator.xr" in text
    assert "immersive-ar" in text
    assert "XRWebGLLayer" in text
    assert "session.requestAnimationFrame" in text
    assert "view.projectionMatrix" in text
    assert "/state.json" in text
