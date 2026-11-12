# AEGIS

CARLA 0.9.15 camera perception and CARLA–SUMO simulation, with MAPPO policy and
recovery-planner source. `main` is the integration branch.

## Open acceptance work

Reviewed 12 November 2026. The P1 security and P3 policy/planner source PRs are
merged; their full ZIP deliverables remain incomplete. Passing unit tests does
not establish live-policy, application or presentation acceptance.

| Owner | Verified progress | Remaining work |
|---|---|---|
| P1 / Amal | Security contribution merged; presentation/checklist drafts reviewed | [#4: Final deck, compliance evidence, actual costs, backup and rehearsal](https://github.com/Dreamer5967/mavericktech-/issues/4) |
| P2 | Four cameras, YOLO, 22 ROI counts, dropout recovery, and fixed-time CARLA–SUMO validation passed | [#6: Queue semantics, long-run acceptance and remaining runtime work](https://github.com/Dreamer5967/mavericktech-/issues/6) |
| P3 / Shivanshu | Actual-SUMO MAPPO artifact, hash verification, isolated recovery evaluation and live read-only proposals passed | [#5: Camera-domain and guarded control acceptance remain blocked](https://github.com/Dreamer5967/mavericktech-/issues/5) |
| P4 | Dashboard foundation on its branch; security helpers available | [#7: Live frames, operator API, VQA, tracing, deployment and speech](https://github.com/Dreamer5967/mavericktech-/issues/7) |

Live learned-policy control and the complete end-to-end demo are not ready.
Use the linked issue checklists and evidence to determine completion; team role
ownership remains unchanged. Artifacts completed outside Git can be linked in
the relevant issue for verification.

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
- [Lane calibration and policy mapping status](docs/lane_mapping.md)

P3's geometry-aligned training contract is integrated. Physical lanes aggregate into four
model slots; unused slots remain masked. Model actions translate through the
actual SUMO green-phase table. Inference is read-only: `actions` is always empty,
and `proposed_sumo_phases` requires independent transition validation. Live policy
remains disabled pending camera-domain/clearance review. The isolated SUMO
environment trains and evaluates only against the hash-verified Town10 network.
Offline diagnostics and rollouts are not live traffic benchmarks.

Cloud code uses the existing Python 3.10 `venv-sim`. Do not run policy development
requirements against it as setup. Live execution needs appropriate approval;
never automatically restart CARLA, change maps or take over the simulation clock.
Keep credentials, weights, environments and simulator binaries outside Git.

Responsibilities remain unchanged: P1 presentation/evidence; P2 simulation and
perception; P3 policy/planning; P4 application, security and speech.
