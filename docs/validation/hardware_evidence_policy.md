# Hardware Evidence Policy

IX-HapticSight does not treat a mock, simulator, generated signal, or replay as hardware evidence.

The HIL harness can report `PASSED` only when all required hardware capabilities are positively declared and the configured executor returns measured samples.

A physical-robot evidence package should retain at minimum:

- robot and controller identity;
- sensor identity and calibration state;
- software revision;
- configuration hashes;
- synchronized force/torque and motion timestamps;
- commanded versus measured trajectories;
- limit and watchdog events;
- fault-injection cases;
- recovery outcome;
- evidence-chain manifest;
- operator/test witness metadata where appropriate.

The repository can prepare and verify that structure. It cannot manufacture the measurements.
