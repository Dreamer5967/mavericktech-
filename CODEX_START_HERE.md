# AEGIS - Codex start here (P2 live cloud handoff)

Updated: 12 November 2026. This addendum supplements the original AEGIS Team Build Kit. It does not alter any P1-P4 duties, previous team handoff PDFs, or the implementation plan.

## Read in this order

1. `START_HERE.md` (original build kit overview)
2. `docs/P2_Live_Cloud_Status.md` (confirmed cloud progress and commands)
3. `docs/GitHub_Workflow.md` (safe repository and branch setup)
4. `team/P2_Cloud_Simulation_and_Perception.md` (P2 scope)
5. `docs/API_and_Data_Contracts.md` (team data interface)
6. `starter/CLEAN_COMMANDS.md` (clean ASCII setup commands)

## Your job as Codex

You are continuing **Person 2's** CARLA/SUMO/perception work, not rebuilding the project from scratch.

- **Do not change any team roles.** P1 = light coding/PPT/evidence; P2 = cloud+CARLA/SUMO+YOLO+live coordinator; P3 = MAPPO/estimator/recovery/evaluation; P4 = app/dashboard/VQA/security/speech.
- There is already a running CARLA server on the rented GPU (verify runtime health before assuming it is still alive).
- Do **not** download/reinstall CARLA, reinstall NVIDIA drivers, recreate `venv-sim`, or start a second server before verifying what is present.
- Do **not** call `world.tick()` or `traci.simulationStep()` in standalone smoke tests. P2's eventual synchronized coordinator must be the sole live clock owner; P3 recovery SUMO processes are independent.
- Do not expose simulator ports publicly. Keep the app API on loopback, use authorized SSH tunnels.
- Do not put cloud SSH keys, GitHub credentials, `.env`, model checkpoints, or downloaded binaries in the repo.
- Keep evaluation CSVs blank until actual measured runs. A smoke-test detection is **not** proof of 4-intersection co-simulation or lane occupancy estimation.

## First Codex actions

1. Inspect `git status`, the existing branch, and the kit. Do not overwrite teammates' work.
2. Verify the instance with `bash scripts/p2_check_instance.sh` **on the Vast server**, if the project is present there.
3. Review the existing P2 smoke-test image artifacts and YOLO console result. Extract reusable source files from the *verified commands* in `docs/P2_Live_Cloud_Status.md`; do not assume scripts were saved to disk when they were only executed through a heredoc.
4. Check whether `/workspace/aegis/camera_four_smoke.py` exists, and run/review it carefully. **Its success has not yet been confirmed by the user.**
5. Coordinate an observation schema with P3/P4 before implementing continuous camera feeds, faults, or signal control.
6. Add scripts to Git incrementally with tests and clear commits. Make a PR into `main`, rather than direct experimental commits to the shared integration branch.

## Verified milestone

CARLA 0.9.15 server + Python client connected on Town10HD_Opt; CARLA RGB camera produced a 960x540 frame; YOLOv10n detected one car and one person on the saved frame. Details and evidence paths are in `docs/P2_Live_Cloud_Status.md`.
