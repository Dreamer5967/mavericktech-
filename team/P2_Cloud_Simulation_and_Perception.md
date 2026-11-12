# 21. Person 2 handoff: cloud, simulation, perception, and runtime

You own the expensive and fragile part of the system. Your priority is a repeatable real pipeline, not a large city. Keep P3 and P4 unblocked by publishing observations in the agreed schema as early as possible.

## Implementation tickets in order

| Ticket | Build action | Files / interface | Done when |
|---|---|---|---|
| P2-01 | Compare offer, configure SSH, run graphics preflight | Runtime manifest and logs | Actual RGB frame saved on the chosen host |
| P2-02 | Run supplied co-simulation and inventory signal IDs | Map manifest + junction config | Four connected signal systems reviewed |
| P2-03 | Add fixed roadside cameras and a selected overview | Camera configs + frame store | All declared approaches have visible coverage or explicit gaps |
| P2-04 | Run YOLOv10n and lane assignment | Perception worker | Timestamped count/queue proxy messages published |
| P2-05 | Own the extended synchronization coordinator | Coordinator action/incident hooks | One clock owner; valid actions mirror into CARLA |
| P2-06 | Add dropout/stale/occlusion mechanisms | Fault injector + seeded schedule | Controller sees only allowed observations |
| P2-07 | Compress and publish selected frames | Frame API / broker | Browser receives live frames at measured cost/rate |
| P2-08 | Execute scheduled local-model attack jobs | Evaluation artifacts | Real attack metrics, not detector-only screenshots |
| P2-09 | Reset, backup, and shut down responsibly | Runtime runbook | Repeatable restart and local evidence copies |

## Coordinator integration detail

Start from the version-matched co-simulation example. Add a pre-tick action inbox and a post-tick event publication point. Never create a second unsynchronized `simulationStep()` loop in a separate API process. A sequence is: receive latest eligible proposal, queue approved transition, advance SUMO, synchronize actors/lights, advance CARLA once, collect bounded sensor observations, publish a revision. Match the exact bridge implementation's ordering rather than rewriting it blindly.

Queues are bounded. Long-running model calls happen outside the tick loop. If inference is late, use the latest eligible estimate with its age; do not block forever waiting for a single camera. Expose coordinator exceptions to the readiness panel and write logs with run ID and simulation time.

## Perception interface with P3

Before hour 2, give P3 the lane ordering and camera availability schema, even if only fixtures exist. By the first live integration, replace fixture values with actual detector outputs, retaining missing/null fields. A newly added hidden evaluator field must never appear in P3's online actor input.

Calibrate camera regions with screenshots. Save transforms and polygons as versioned data. Each capture has frame ID, timestamp, and camera ID. When the fault injector drops an image, preserve the last valid timestamp rather than retimestamping old data as new.

## Cloud execution checklist

Record who owns the current tmux sessions and model jobs. Start a GPU-heavy adversarial evaluation only after agreeing with P3 that training/rendering can pause. Profile memory before loading an extra model. Keep raw frames bounded, for example one selected frame per second plus incident windows, rather than retaining every rendered image indefinitely.

Before a reset, tell P4 that LIVE will become RESETTING. Stop the coordinator, remove only owned actors/processes, restore/reload the scenario, and create a fresh run ID. Do not kill every Python process on a shared machine.

## Acceptance tests

A judge-selected camera fails while the other cameras continue. The failed lane's raw count becomes null rather than zero. Signal actions remain synchronized. The dashboard shows current timestamps. Repeated start/reset cycles do not accumulate duplicate vehicles or cameras. A disconnected browser does not stop the simulation. A restarted simulation does not reuse stale proposals from the previous run.

Your ownership is complete only when another teammate can follow the runbook to reproduce the smoke test and export the evidence. Document unresolved issues instead of hiding them behind a cached video.


# Shared handoff rules

Develop against the versioned observation/proposal/execution contract in handbook section 18. P2 alone owns live simulation ticks and restarts. Do not present mock values as metrics. All benchmark tables remain empty until measured. P1 has protected PPT time; P4 has protected speech time. Keep credentials out of Git, screenshots and recordings.

Use the complete handbook for setup, requirements and source references. This task sheet is an ownership guide, not a complete stand-alone simulator installer.
