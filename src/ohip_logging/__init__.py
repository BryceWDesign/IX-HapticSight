"""
IX-HapticSight structured logging package.

This package is reserved for:
- structured event models
- event serialization
- replay-safe log writing
- evidence bundle helpers

It is intentionally separate from:
- the stable OHIP protocol core in ``src/ohip``
- runtime orchestration in ``src/ohip_runtime``
- future ROS 2 integration layers

The design goal is simple:
important runtime behavior should be inspectable after the fact without relying
on ad hoc console output or scattered backend logs.
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.1.0"
