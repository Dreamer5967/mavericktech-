# AEGIS

CARLA 0.9.15 camera perception and CARLA–SUMO simulation, with MAPPO policy and
recovery-planner source. `main` is the integration branch.

## Source layout

| Directory | Contents |
|---|---|
| `p2/` | Camera capture, YOLO, observation API, static map/demand tools and guarded bridge tests |
| `services/control/` | Estimation, fixed-time control, policy inference and phase-manager logic |
| `services/planner/` | Candidate generation, belief rollouts, planning and outcome logging |
| `services/security/` | Prompt-screening rules and explicit-token role authorization |
| `training/` | MAPPO actor/critic, training and standalone SUMO environment |
| `configs/` | Observation, reward, seed and draft action configurations |
| `contracts/` | Planner output schema |
| `manifests/` | Model provenance declarations and deployment verification status |
| `aegis_helpers/` | Shared lane-observation contract and phase-transition validation |
| `scripts/` | Read-only instance check and offline synthetic diagnostics |
| `tests/`, `p2/tests/` | Policy/planner and perception unit tests |
| `requirements/` | Policy development dependencies; not a cloud installation command |
| `docs/` | Current runtime and integration API documentation |

Generated experiments go into ignored `results/`; checkpoints and simulator
evidence stay outside Git. Handoff documents and presentation material are not
part of this source tree.

## Run checks

From the repository root, using a local interpreter with the policy dependencies:

```powershell
py -3.14 -B -m unittest discover -s p2/tests -v
py -3.14 -B -m unittest discover -s tests -v
```

The external trained-checkpoint test skips when its artifact is unavailable.
Set `AEGIS_P3_CHECKPOINT` to its path and `AEGIS_REQUIRE_P3_CHECKPOINT=1` to require
that test; inference checks the manifest SHA256 before loading tensor weights.
Random test fixtures do not count as trained-policy verification.

## Runtime and integration

- [P2 commands](p2/README.md)
- [Existing cloud runtime and validation status](docs/runtime.md)
- [Observation and policy integration boundaries](docs/api.md)
- [Security module scope](docs/security.md)

P3 source is integrated; live learned control remains blocked by external
checkpoint verification, lane calibration and actual map-specific phase mapping.
The four-phase action labels are draft model slots, not verified SUMO phase
indices. Inference returns proposals and internal phase-manager state; it does
not execute simulator signal changes. Synthetic diagnostics and rollouts are not
live traffic benchmarks.

Cloud code uses the existing Python 3.10 `venv-sim`. Do not run policy development
requirements against it as setup. Live execution needs appropriate approval;
never automatically restart CARLA, change maps or take over the simulation clock.
Keep credentials, weights, environments and simulator binaries outside Git.

Responsibilities remain unchanged: P1 presentation/evidence; P2 simulation and
perception; P3 policy/planning; P4 application, security and speech.
