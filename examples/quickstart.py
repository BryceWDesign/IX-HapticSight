"""
IX-HapticSight — Quickstart Demo (1 minute)

Loads the basic sim scene, runs:
  Scene JSON → EngagementScheduler (nudge)
              → ContactPlanner (ContactPlan)
              → SafetyGate (dual-channel OK?)

Output: a short, factual log proving the stack is wired correctly.

Usage:
  python examples/quickstart.py
  python examples/quickstart.py --scene sim/scenes/basic_room.json --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    print("Missing dependency: pyyaml. Install with `pip install pyyaml`.", file=sys.stderr)
    raise

# Make 'ohip' importable from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ohip import (  # noqa: E402
    # data + utils
    Pose, Vector3, RPY, SafetyLevel,
    ConsentRecord, ConsentMode, ConsentSource,
    # engine
    EngagementScheduler, PolicyProfile,
    ContactPlanner, PlannerHints,
    SafetyGate,
)

SCENE_DEFAULT = ROOT / "sim" / "scenes" / "basic_room.json"
FORCE_LIMITS = ROOT / "configs" / "force_limits.yaml"


def load_scene(path: Path) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text())
    return data


def load_envelopes(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def aabb_contains(aabb_min: List[float], aabb_max: List[float], p: Tuple[float, float, float]) -> bool:
    return all(aabb_min[i] <= p[i] <= aabb_max[i] for i in range(3))


def risk_query_from_scene(scene: Dict[str, Any]):
    """Return a callable pose->SafetyLevel derived from scene.safety_regions."""
    regions = scene.get("safety_regions", []) or []

    def risk(pose: Pose) -> SafetyLevel:
        x, y, z = pose.xyz.x, pose.xyz.y, pose.xyz.z
        point = (x, y, z)
        level = SafetyLevel.GREEN
        # Prefer the most severe label among matches
        for r in regions:
            mn = r.get("aabb_min_W")
            mx = r.get("aabb_max_W")
            if not (mn and mx):
                continue
            if aabb_contains(mn, mx, point):
                lv = r.get("level", "GREEN").upper()
                if lv == "RED":
                    return SafetyLevel.RED
                if lv == "YELLOW":
                    level = SafetyLevel.YELLOW
        return level

    return risk


def make_consent_from_scene(scene: Dict[str, Any]) -> ConsentRecord:
    h = scene.get("human", {})
    c = h.get("consent", {}) or {}
    mode = str(c.get("mode", "none")).lower()
    if mode == "explicit":
        cmode = ConsentMode.EXPLICIT
        csource = ConsentSource(str(c.get("source", "ui")))
    elif mode == "policy":
        cmode = ConsentMode.POLICY
        csource = ConsentSource.PROFILE
    else:
        cmode = ConsentMode.NONE
        csource = ConsentSource.UI
    scope = [s.lower() for s in c.get("scope", [])]
    ttl = int(c.get("ttl_s", 60))
    return ConsentRecord(subject_id=h.get("id", "anon"), mode=cmode, source=csource, scope=scope, ttl_s=ttl)


def make_affordances_from_scene(scene: Dict[str, Any]) -> List[Dict[str, Any]]:
    aff = scene.get("affordances", []) or []
    # Ensure pose dict matches schemas.Pose.to_dict() expectations
    for a in aff:
        pose = a.get("pose")
        if pose and isinstance(pose.get("xyz"), list) and isinstance(pose.get("rpy"), list):
            # OK
            pass
    return aff


def to_pose(d: Dict[str, Any]) -> Pose:
    return Pose(
        frame=str(d.get("frame", "W")),
        xyz=Vector3(*[float(v) for v in d["xyz"]]),
        rpy=RPY(*[float(v) for v in d["rpy"]]),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=Path, default=SCENE_DEFAULT, help="Path to scene JSON")
    ap.add_argument("--envelopes", type=Path, default=FORCE_LIMITS, help="Path to force_limits.yaml")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    scene = load_scene(args.scene)
    envelopes = load_envelopes(args.envelopes)
    risk_query = risk_query_from_scene(scene)

    # Human state & consent
    human = scene.get("human", {})
    human_state = {
        "present": bool(human.get("present", True)),
        "distress": float(human.get("affect", {}).get("distress", 0.0)),
    }
    consent = make_consent_from_scene(scene)

    # Affordances (targets)
    affordances = make_affordances_from_scene(scene)

    # Run scheduler
    policy = PolicyProfile()
    sched = EngagementScheduler(policy=policy)
    nudge = sched.decide(human_state, consent, affordances, risk_query)

    if args.verbose:
        print("Scene:", args.scene)
        print("Human state:", human_state)
        print("Consent:", consent.to_dict())

    if nudge is None:
        print("No nudge emitted (nothing safe/appropriate).")
        return 0

    print("NUDGE:", nudge.to_dict())

    # Plan contact
    planner = ContactPlanner(envelopes)
    plan = planner.plan(nudge, consent, profile_name=envelopes.get("defaults", {}).get("social_touch_profile"))
    if plan is None:
        print("Planner returned no plan.")
        return 0

    print("PLAN:", plan.to_dict())

    # Safety gate (dual-channel OK?)
    gate = SafetyGate(envelopes)
    ok = gate.dual_channel_ok(plan, risk_query, start_pose=None)
    print("SAFETY_OK:", ok)
    if not ok:
        print("Reason (if latched):", gate.last_reason())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
