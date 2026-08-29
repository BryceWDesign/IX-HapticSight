"""Run the local IX-HapticSight WebXR safety observer."""
from __future__ import annotations

from pathlib import Path

from ohip.schemas import SafetyLevel
from ohip_xr import XRHazardMarker, XRState, XRStateStore, serve

root = Path(__file__).resolve().parent
store = XRStateStore(
    XRState(
        session_id="demo",
        consent_active=True,
        safety_authority="MODIFY",
        force_cap_N=2.5,
        speed_cap_mps=0.05,
        controller_state="APPROACH",
        reason="human_proximity_derate",
        markers=(
            XRHazardMarker("human", (0.1, 0.0, 0.8), 0.15, SafetyLevel.YELLOW, "person", 0.93),
            XRHazardMarker("hot", (-0.2, 0.0, 1.1), 0.10, SafetyLevel.RED, "hot surface", 0.88),
        ),
    )
)
server = serve(root, store)
print("IX-HapticSight WebXR observer: http://127.0.0.1:8765")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
