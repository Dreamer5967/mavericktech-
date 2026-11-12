# AEGIS Master Submission Checklist
**Smart Technologies PS1 (Intelligent Traffic Control) & PS3 (VQA & Security Boundary)**

> [!IMPORTANT]
> Every item must have a named owner, a verified output artifact, and explicit test status. Do not mark items complete until actual runs produce evidence files.

---

## 1. Core Deliverables Matrix

| ID | Requirement / Objective | Problem Statement | Owner | Artifact / File Path | Target Status | Verified By | Notes / Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | Co-simulation environment setup (CARLA 0.9.15 + SUMO in Town05) | PS1 | P2 | `starter/templates/junctions.example.json`<br>`docs/Cloud_Setup_Detailed.md` | In Progress | P1 | Single clock owner (`run_synchronization.py`). 4+ connected signal systems identified. |
| **REQ-02** | Roadside perception pipeline (YOLOv10n vehicle detection & lane counting) | PS1 | P2 | `starter/scripts/camera_smoke.py`<br>`evaluation/perception_results.csv` | Pending Live Frame | P1 | Fixed camera viewpoints at 4 junctions; outputs timestamped count & queue proxy. |
| **REQ-03** | Cooperative MARL traffic controller (MAPPO across 4+ intersections) | PS1 | P3 | `starter/templates/model_manifest.example.json`<br>`team/P3_MAPPO_Planner_and_Evaluation.md` | Pending Training | P1 | Multi-agent coordination with shared state/rewards; frozen checkpoint hash recorded. |
| **REQ-04** | Perception fault injection & missing-state uncertainty recovery | PS1 | P2, P3 | `starter/aegis_helpers/contracts.py`<br>`starter/aegis_helpers/mock_server.py` | Verified (Mock) | P1 | Camera dropout emits `null` count + uncertainty intervals `[lower, upper]` (never fake zero). |
| **REQ-05** | Safety phase manager & transition guard | PS1 | P3 | `starter/aegis_helpers/phase_guard.py`<br>`tests/phase_cases.md` | Scaffold Done | P1 | Enforces minimum green, yellow/all-red clearance, and rejects stale/out-of-order state revisions. |
| **REQ-06** | Traffic performance evaluation (Waiting time, queue, fuel consumption) | PS1 | P3 | `evaluation/traffic_results.csv`<br>`evaluation/README.md` | Ready for Data | P1 | Matched seeds & scenarios: Fixed-time vs. MAPPO vs. Recovery. Units explicitly declared. |
| **REQ-07** | Multimodal Visual Question Answering (VQA) with dynamic multi-model routing | PS3 | P4 | `starter/scripts/vqa_smoke.py`<br>`evaluation/vqa_routes.csv` | Scaffold Done | P1 | Route between fast edge model and deep reasoning model based on query complexity. |
| **REQ-08** | Adversarial robustness evaluation (FGSM/PGD perturbations on vision) | PS3 | P2, P4 | `evaluation/adversarial_vqa.csv` | Ready for Data | P1 | Perturbed camera frames evaluated against clean frames; detection flags recorded. |
| **REQ-09** | Security privilege boundary & prompt injection defense | PS3 | P4 | `evaluation/prompt_injection.csv` | Scaffold Done | P1 | VQA/operator tokens cannot call actuation endpoints. Injected prompts in images fail to actuate signals. |
| **REQ-10** | System deployment & containerization (Docker Compose) | General | P2, P4 | `starter/compose.mock.yaml`<br>`starter/Dockerfile.mock` | Scaffold Done | P1 | Reproducible stack deployment across environments. |
| **REQ-11** | Final Presentation Slide Deck (6 Core Slides + Appendix) | Pitch | P1 | `presentation/slides.md`<br>`presentation/slides.pptx` | Skeleton Ready | P1, P4 | 6 core slides aligned with 5-minute pitch choreography and verified evidence. |
| **REQ-12** | Cloud Budget & Spend Tracking ($5.00 limit) | Operations | P1 | `manifests/cost_log.csv` | Active | P1 | Maintains $1.00 reserve; hourly tracking of compute, storage, and transfer rates. |

---

## 2. Review Gates & Timeline

```
Hour 0-2  [GATE 1]: Local verification passed, repo shared, cost log initialized, checklist signed.
Hour 2-5  [GATE 2]: Cloud GPU preflight passed, first real CARLA frame saved, MAPPO training starts.
Hour 5-8  [GATE 3]: First closed loop (Camera -> YOLO -> Coordinator -> SUMO), UI shows live data.
Hour 8-10 [GATE 4]: Code freeze; run matched evaluation benchmarks (Traffic, VQA, Adversarial).
Hour 10-12[GATE 5]: Final deck finalized with real numbers, rehearsal with P4, submission package built.
```

---

## 3. Pre-Submission Verification Sign-Off

- [ ] All benchmark CSV files contain genuine measured data with no fabricated placeholder numbers.
- [ ] No API keys, credentials, or private SSH keys exist in Git history, configs, or slides.
- [ ] Model weights / checkpoints have documented SHA256 hashes and training manifests.
- [ ] Backup demonstration recording is stored locally on the presentation laptop.
- [ ] Live demo reset procedure tested twice consecutively without crashing.
