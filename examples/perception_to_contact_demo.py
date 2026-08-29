"""End-to-end software demonstration for IX-HapticSight v0.2.

The demo intentionally uses synthetic RGB-D calibration data and a simulated
contact plant. It proves software integration, not physical robot validation.
"""
from __future__ import annotations

from pathlib import Path

from ohip.schemas import SafetyLevel
from ohip_control import ActionProposal, BoundedRealtimeController, ControllerInput, IndependentSafetyAuthority
from ohip_evidence import EvidenceChain
from ohip_perception import PerceptionFrame, ReferenceSegmenter, VisionPipeline
from ohip_sim import ContactWorld

ROOT = Path(__file__).resolve().parents[1]
primary = ReferenceSegmenter.from_file(ROOT / "models/reference_segmenter_primary.json")
secondary = ReferenceSegmenter.from_file(ROOT / "models/reference_segmenter_secondary.json")
pipeline = VisionPipeline(primary, secondary=secondary)

# Person-colored target plus ordinary object. Synthetic input is explicit.
frame = PerceptionFrame(
    rgb=[[(178, 122, 94), (107, 117, 110)]],
    depth_m=[[0.40, 1.20]],
    timestamp_s=1.0,
)
perception = pipeline.process(frame)

proposal = ActionProposal(
    action_id="demo-contact",
    requested_force_N=5.0,
    requested_speed_mps=0.20,
    base_force_cap_N=3.0,
    base_speed_cap_mps=0.10,
    safety_level=SafetyLevel.YELLOW,
    perception_uncertainty=0.10,
    perception_quorum_ok=bool(perception.agreement is None or perception.agreement.passed),
    consent_required=True,
    consent_active=True,
    human_present=True,
    proximity_m=0.40,
)
authority = IndependentSafetyAuthority().decide(proposal)

chain = EvidenceChain()
chain.append("perception", {
    "safe_for_autonomy": perception.safe_for_autonomy,
    "reason": perception.reason,
    "hazard_count": len(perception.hazards),
}, timestamp_s=1.0)
chain.append("authority", {
    "disposition": authority.disposition.value,
    "force_N": authority.granted_force_N,
    "speed_mps": authority.granted_speed_mps,
    "reason": authority.reason,
}, timestamp_s=2.0)

controller = BoundedRealtimeController(target_period_ms=50.0)
world = ContactWorld(surface_position_m=0.02)
last = None
for _ in range(120):
    measured = 0.0 if last is None else last.measured_force_N
    control = controller.step(ControllerInput(
        requested_speed_mps=authority.granted_speed_mps,
        requested_force_N=authority.granted_force_N,
        measured_force_N=measured,
        force_cap_N=authority.granted_force_N,
        speed_cap_mps=authority.granted_speed_mps,
        sensor_age_ms=1.0,
        consent_active=True,
        contact_requested=True,
        perception_quorum_ok=True,
        contact_detected=measured > 0.25,
    ))
    last = world.step(
        command_velocity_mps=control.command_speed_mps,
        force_cap_N=max(0.0, authority.granted_force_N),
        dt_s=0.005,
    )
    if control.stop or control.latched:
        break

chain.append("control", {
    "state": controller.state.value,
    "measured_force_N": 0.0 if last is None else last.measured_force_N,
    "latched": controller.latched,
}, timestamp_s=3.0)

print("PERCEPTION:", perception.reason)
print("AUTHORITY:", authority.disposition.value, authority.reason)
print("GRANTED:", round(authority.granted_force_N, 3), "N", round(authority.granted_speed_mps, 3), "m/s")
print("CONTROLLER:", controller.state.value, "latched=", controller.latched)
print("EVIDENCE_CHAIN:", chain.verify())
