"""Deterministic 1-D contact world for safety/controller regression tests.

This is not claimed as physical validation. It provides a small executable
closed-loop plant so force caps, contact detection, overshoot, sensor dropouts,
and recovery can be regression-tested without replacing future HIL work.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ContactWorldState:
    position_m: float = 0.0
    velocity_mps: float = 0.0
    measured_force_N: float = 0.0
    sim_time_s: float = 0.0


class ContactWorld:
    def __init__(
        self,
        *,
        surface_position_m: float = 0.10,
        stiffness_N_per_m: float = 800.0,
        damping_Ns_per_m: float = 12.0,
        mass_kg: float = 1.0,
    ) -> None:
        self.surface_position_m = float(surface_position_m)
        self.stiffness_N_per_m = float(stiffness_N_per_m)
        self.damping_Ns_per_m = float(damping_Ns_per_m)
        self.mass_kg = float(mass_kg)
        self.state = ContactWorldState()

    def reset(self) -> ContactWorldState:
        self.state = ContactWorldState()
        return self.state

    def step(self, *, command_velocity_mps: float, force_cap_N: float, dt_s: float = 0.005) -> ContactWorldState:
        dt = float(dt_s)
        desired_velocity = float(command_velocity_mps)
        accel = (desired_velocity - self.state.velocity_mps) * 25.0
        self.state.velocity_mps += accel * dt
        self.state.position_m += self.state.velocity_mps * dt
        penetration = max(0.0, self.state.position_m - self.surface_position_m)
        raw_force = self.stiffness_N_per_m * penetration + self.damping_Ns_per_m * max(0.0, self.state.velocity_mps)
        self.state.measured_force_N = max(0.0, raw_force)
        if self.state.measured_force_N > max(0.0, force_cap_N):
            # Simulate local low-level limiter dissipating forward motion.
            self.state.velocity_mps = min(0.0, self.state.velocity_mps)
        self.state.sim_time_s += dt
        return ContactWorldState(**self.state.__dict__)
