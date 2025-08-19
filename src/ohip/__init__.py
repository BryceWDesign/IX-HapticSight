"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)

Package initializer: exposes the stable public API used across docs, sims,
and tests. Keeps versioning centralized.

Versioning
----------
__version__        : project/package version (v0.1.0 for the v0.1 spec drop)
__schema_version__ : canonical schema version from ohip.schemas

Do not import heavy dependencies here. Keep imports shallow.
"""

from .schemas import (
    # enums
    SafetyLevel, HazardClass, ConsentMode, ConsentSource, NudgeLevel,
    # primitives
    Vector3, RPY, Pose,
    # core messages
    ConsentRecord, SafetyMapCell, Nudge,
    ImpedanceProfile, ContactPlan, ContactExecutionLog,
    RestTargets,
    # utils
    now_utc_iso, clamp, validate_priority,
    # schema version
    OHIP_SCHEMAS_VERSION as __schema_version__,
)

from .nudge_scheduler import EngagementScheduler, PolicyProfile
from .safety_gate import SafetyGate, HardwareInterface, HardwareStatusSnapshot
from .contact_planner import ContactPlanner, PlannerHints
from .rest_pose import RestPoseGenerator, RestConfig
from .consent_manager import ConsentManager, ProfileRules

# Project/package version for this release of the reference implementation.
__version__ = "0.1.0"

__all__ = [
    # versions
    "__version__", "__schema_version__",
    # enums & primitives
    "SafetyLevel", "HazardClass", "ConsentMode", "ConsentSource", "NudgeLevel",
    "Vector3", "RPY", "Pose",
    # core messages
    "ConsentRecord", "SafetyMapCell", "Nudge",
    "ImpedanceProfile", "ContactPlan", "ContactExecutionLog",
    "RestTargets",
    # utils
    "now_utc_iso", "clamp", "validate_priority",
    # scheduler
    "EngagementScheduler", "PolicyProfile",
    # safety
    "SafetyGate", "HardwareInterface", "HardwareStatusSnapshot",
    # planner
    "ContactPlanner", "PlannerHints",
    # rest pose
    "RestPoseGenerator", "RestConfig",
    # consent
    "ConsentManager", "ProfileRules",
]
