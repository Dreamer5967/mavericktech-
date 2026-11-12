# AEGIS starter reference kit
This is a documentation and development scaffold, not the finished AEGIS system.
No trained MAPPO checkpoint, CARLA server, YOLO weights, hosted credentials, or benchmark results are included.

## Zero-cloud-cost start
From this folder, use Python 3.10 or 3.11 (or another tested compatible interpreter):
```
python -m unittest discover -s tests -v
python -m aegis_helpers.mock_server
```
Open http://127.0.0.1:8000. The MOCK banner is deliberate. Operator token: `local-demo-only` for this local development tool, or set `AEGIS_OPERATOR_TOKEN`.

## Updated cloud setup
Use [CLEAN_COMMANDS.md](CLEAN_COMMANDS.md) as the copy-paste source. It preserves ordinary ASCII hyphens and provides explicit interpreter paths, so you do not need to remember which `tmux` pane activated which environment.

Only two cloud environments are the default:

| Environment | Workload |
| --- | --- |
| `venv-sim` / Python 3.10 | CARLA 0.9.15 client, SUMO tools, YOLOv10, FastAPI/uvicorn; compatible controller inference |
| `venv-vqa` / Python 3.10 | PyTorch, ViLT/Transformers, Langfuse and VQA evaluation |

The CARLA server binary and SUMO executable are installed separately. Two environments do not mean one blocking process: coordinator, YOLO inference, frame delivery and API remain independent workers. Only the live coordinator advances CARLA; recovery workers have separate SUMO processes. P3 retains training ownership and can reuse a compatible environment. Split an additional environment only if a measured dependency conflict requires it.

Python 3.10 is a compatibility choice for this bounded hackathon setup. Keep the API on loopback behind SSH. Package installation and GPU rendering must be verified on the chosen host; this kit does not certify them.

## Offline budget estimate
```
python -m aegis_helpers.budget --compute 0.30 --storage 0.02 --transfer 0.50 --reserve 1
```
Rates are examples, not live offers. This program never rents, stops or destroys anything.

## Optional Docker test
```
docker compose -f compose.mock.yaml up --build
```
The Compose file demonstrates the mock only, not PS3 completion. The team must implement and package the real app.

## Included vs to build
Included: fixture API, mock UI, observation validation, toy phase-request validation, cost estimator, unit tests, read-only preflight, two-environment creator, dependency/import checks, CARLA frame probe, SUMO signal inventory, Langfuse trace probe, local ViLT smoke probe, evidence export script, manifests and configuration examples.
To build: real CARLA/SUMO coordinator, camera lane calibration, YOLO adapter, MAPPO training and checkpoint, uncertainty estimator, recovery workers, real model router, adversarial benchmark, real operator UI and measured evaluations.
The CARLA/SUMO/ViLT/Langfuse probes require their separate dependencies and have not been executed on your cloud instance.
Read the handbook before running cloud setup commands. Never put keys or downloaded third-party weights in Git.

The original P1-P4 assignments remain unchanged. P1 keeps the lighter MacBook coding role and owns the PPT; P4 owns the speech. This setup revision does not assign P1 training jobs, backend hosting or shared compute responsibilities.
