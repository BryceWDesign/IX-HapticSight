"""
IX-HapticSight runtime package.

This package is the first step in separating the stable OHIP protocol core
from runtime orchestration concerns.

Design intent
-------------
The existing ``src/ohip`` package remains the protocol and deterministic logic
core. This package is reserved for runtime/session ownership concerns such as:

- interaction session lifecycle
- runtime state ownership
- timeout handling
- transition coordination
- latched fault handling
- coordination between consent, safety, planning, and execution layers

At this stage, the package is intentionally small. The goal is to establish a
clean boundary before additional runtime code is introduced.

Rules
-----
- Do not put backend-specific transport code here.
- Do not put ROS 2 node code here.
- Do not move stable protocol schemas out of ``src/ohip``.
- Keep runtime state explicit and auditable.
- Preserve the authority of consent and safety logic over convenience behavior.

Versioning
----------
This package tracks the repository buildout version, not a separate protocol
version. The protocol schema version remains owned by ``ohip.schemas``.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.1.0"
