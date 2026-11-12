# AEGIS starter reference kit
This is a documentation and development scaffold, not the finished AEGIS system.
No trained MAPPO checkpoint, CARLA server, YOLO weights, hosted credentials, or benchmark results are included.

## Zero-cloud-cost start
From this folder, use Python 3.11 (or another tested compatible interpreter):
```
python -m unittest discover -s tests -v
python -m aegis_helpers.mock_server
```
Open http://127.0.0.1:8000. The MOCK banner is deliberate. Operator token: `local-demo-only` for this local development tool, or set `AEGIS_OPERATOR_TOKEN`.

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
Included: fixture API, mock UI, observation validation, toy phase-request validation, cost estimator, unit tests, read-only preflight, CARLA frame probe, SUMO signal inventory, Langfuse trace probe, local ViLT smoke probe, evidence export script, manifests and configuration examples.
To build: real CARLA/SUMO coordinator, camera lane calibration, YOLO adapter, MAPPO training and checkpoint, uncertainty estimator, recovery workers, real model router, adversarial benchmark, real operator UI and measured evaluations.
The CARLA/SUMO/ViLT/Langfuse probes require their separate dependencies and have not been executed on your cloud instance.
Read the handbook before running cloud setup commands. Never put keys or downloaded third-party weights in Git.
