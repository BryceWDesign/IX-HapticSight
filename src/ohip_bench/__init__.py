"""
IX-HapticSight benchmark package.

This package is reserved for:
- deterministic benchmark scenario definitions
- benchmark execution harnesses
- metrics aggregation
- result packaging
- replay-backed regression checks

Design goals:
- keep benchmark logic separate from runtime execution code
- preserve repeatability and traceability
- make scenario inputs and outputs explicit
- support local tests before any hardware-in-the-loop evidence exists
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.1.0"
