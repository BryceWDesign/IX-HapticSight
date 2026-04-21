"""
IX-HapticSight interface abstractions package.

This package is reserved for backend-agnostic interface contracts that normalize
external inputs and outputs before they reach runtime coordination logic.

Planned responsibilities:
- force/torque signal interfaces
- tactile signal interfaces
- proximity signal interfaces
- thermal signal interfaces
- execution adapter contracts
- signal health and freshness metadata

Design rules:
- keep device-specific transport details out of the protocol core
- keep ROS 2 specifics out of these base interfaces
- prefer normalized typed payloads over raw vendor-specific dictionaries
- make freshness and signal health explicit
"""

from __future__ import annotations

__all__ = [
    "__version__",
]

__version__ = "0.1.0"
