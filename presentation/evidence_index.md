# AEGIS Evidence Index & Media Asset Standard
**Owner: P1 | Contributors: P2, P3, P4**

> [!TIP]
> Use this standardized structure to log, name, and archive all screenshots, video clips, and benchmark files. This prevents confusion during presentation preparation and judging.

---

## 1. Naming Conventions

### Screen Captures & Visual Artifacts
- **Format**: `run_<RUN_ID>_j<JUNCTION_ID>_<CONDITION>_<TIMESTAMP>.<ext>`
- **Examples**:
  - `run_001_j2_cam_dropout_t120s.png` (Camera dropout at Junction 2)
  - `run_002_j1_normal_traffic_t060s.png` (Normal baseline traffic at Junction 1)
  - `run_003_dashboard_recovery_t300s.png` (Operator console displaying recovery plan)

### Video Recordings (Contingency Demo)
- **Format**: `demo_<MODE>_<SCENARIO>_v<VERSION>.mp4`
- **Examples**:
  - `demo_live_recovery_town05_v1.mp4`
  - `demo_vqa_injection_rejection_v1.mp4`

---

## 2. Evidence Registry

| Asset ID | File Name / Path | Mode (MOCK/REPLAY/LIVE) | Description | Key Metric / Verification Point | Owner | Slide Ref |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EV-01** | `assets/architecture.png` | STATIC | Full 3-Plane System Architecture | Shows clean isolation between control and VQA | P1 | Slide 2 |
| **EV-02** | `assets/dashboard.png` | MOCK/LIVE | Operator Dashboard & Incident Trigger | 4 junction cards, camera status, incident toggle | P4 | Slide 3 |
| **EV-03** | `evaluation/traffic_results.csv` | LIVE | Simulation Benchmark Metrics | Mean waiting time, stopped delay, fuel consumption | P3 | Slide 4 |
| **EV-04** | `evaluation/vqa_routes.csv` | LIVE | Multi-Model Routing Latency & Scores | Compares edge router vs deep model response time | P4 | Slide 5 |
| **EV-05** | `evaluation/adversarial_vqa.csv`| LIVE | FGSM Attack Robustness Scores | Clean vs attacked accuracy and detector flags | P2, P4 | Slide 5 |
| **EV-06** | `evaluation/prompt_injection.csv`| LIVE | Prompt Injection Test Suite | 100% rejection rate for unauthorized actions | P4 | Slide 5 |
| **EV-07** | `manifests/cost_log.csv` | LIVE | Vast.ai Cloud Expenditure Audit | Proves complete execution within $5.00 limit | P1 | Appendix |

---

## 3. Storage Rules
1. Never commit multi-gigabyte raw video files directly to the root Git repository; store them in an `/evidence_media/` folder or cloud storage bucket.
2. Every screenshot included in the final slide deck must indicate whether it was taken during **MOCK**, **REPLAY**, or **LIVE** mode. Never disguise a mock or replay as a live run.
