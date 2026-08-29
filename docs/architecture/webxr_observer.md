# WebXR Safety Observer

The WebXR observer is an observability surface, not the safety authority itself.

It displays:

- safety-authority disposition;
- force and speed caps;
- consent state;
- controller state;
- veto or derating reason;
- colored hazard markers.

The included browser client requests an `immersive-ar` WebXR session when a compatible browser and device are available. The same page falls back to a 2D safety visualization when WebXR is unavailable.

XR visualization latency and spatial registration are not assumed safe enough to close a physical control loop. Those require device-specific measured validation.
