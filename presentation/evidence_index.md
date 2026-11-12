# AEGIS Evidence Index & Media Asset Standard
**Owner: P1 (Amal) | Contributors: P2, P3, P4**
*Verified against Town10HD_Opt co-simulation, PR #3 merge, and 12 November 2026 audit*

> [!IMPORTANT]
> All raw simulation videos, heavyweight image frames, and weights are kept outside Git per maintainer guidelines. Below is the indexed registry of verified artifacts, test results, and offline recorded-run backups.

---

## 1. Verified Evidence Registry

| Asset ID | File / Directory Path | Mode | Description | Key Metric / Verification Point | Owner | Slide Ref |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EV-01** | `evidence/cosim-smoke/test-20261112T081204Z-6199.jsonl` | REPLAY | 30s CARLA-SUMO Co-Simulation Bridge Run | SUMO reached 29.95s; 57 observer samples; up to 14 mirrored CARLA vehicles. Zero signal mismatches. | P2 | Slide 4 |
| **EV-02** | `evidence/multicam/p2-smoke-20261112T070404Z-86ad7e08` | REPLAY | Four-Camera YOLOv10n Perception Smoke | 4 angled roadside cameras (cam_g1, g3, g4, g5). Ages 0.13–0.25s, skew 0.094s, 960x540 JPEGs. | P2 | Slide 4 |
| **EV-03** | `evidence/pipeline-validation/p2-combined-2961dcd55cbc46f6ac0a933ee5f86e72` | REPLAY | Combined Fixed-Time Perception & Traffic Bridge | 63 sampled snapshots, 58 fresh observations, 0 sensor leaks. Map: Town10HD_Opt. | P2 | Slide 4 |
| **EV-04** | `configs/runtime_mapping.json` & `configs/lane_regions.json` | STATIC | 24 Physical Lane Inventory & Signal Mapping | Maps CARLA stop lanes to SUMO incoming lanes; actual green indices (0, 3, 6). | P2 | Slide 2, 4 |
| **EV-05** | `evaluation/prompt_injection.csv` | BENCHMARK | Adversarial Prompt Injection Test Suite (PS3) | 11 fixtures: 100% attack defense rate (6/6 blocked), 0% false alarms (0/5 benign). | P1 | Slide 5 |
| **EV-06** | `tests/test_firewall.py` & `tests/test_p1_phase_guard_cases.py` | UNIT/REGRESSION | Security Firewall & Phase Guard Test Suites | 28/28 tests passed. Validates min green (10s), max green (60s), and clearance sequences [Y+AR]. | P1 | Slide 2, 5 |
| **EV-07** | `manifests/cost_log.csv` | AUDIT | Vast.ai Cloud Expenditure Audit | Total spent: $1.66 ($1.35 GPU + $0.18 disk + $0.13 transfer). Balance $3.34 intact. Zero overrun. | P1 | Slide 6 |
| **EV-08** | `presentation/AEGIS_Pitch_Deck.pptx` & `presentation/AEGIS_Pitch_Deck.pdf` | DECK | 6-Slide Master Presentation Deck | Editable PPTX and compiled widescreen PDF calibrated with actual runtime numbers and declared limitations. | P1 | All |
| **EV-09** | `AEGIS_Emergency_Green_Corridor_System.pdf` & `starter/sim_output/` | SPEC/SIM | Emergency Green Corridor Architecture & Sim | 6-page technical whitepaper + 200-frame animated simulation of zero-stop preemption wave. | P1 | Slide 1, 3 |
| **EV-10** | `starter/web/index.html` & `starter/aegis_helpers/mock_server.py` | LOCAL RUNTIME | Mission Control & Offline Recorded Backup | Interactive local dashboard running corridor simulation, camera dropout toggles, and telemetry. | P1, P4 | Slide 3 |

---

## 2. Offline Recorded-Run Backup (Cloud-Independent Demo)

For judging evaluation when cloud GPU connectivity is restricted or during live stage presentation:

### Quickstart Offline Demo
```powershell
# In terminal:
$env:PYTHONPATH = "starter"
python -m aegis_helpers.mock_server --port 8000
```
Open in browser: `http://127.0.0.1:8000`

### Offline Capabilities Verified:
1. **Interactive Arterial Visualizer**: Real-time canvas animation of Town10 arterial corridor (J1 to J4).
2. **Emergency Dispatch Simulation**: One-click dispatch of Priority 1 Ambulance, Fire Engine, or Organ Courier.
3. **Queue Pre-Flushing Animation**: Visualizes traffic clearing into cross-streets ahead of emergency vehicle arrival.
4. **Camera Fault Injection**: Toggle any junction camera between `AVAILABLE` and `MISSING` to test uncertainty interval fallback.
5. **Phase Guard Invariant Monitor**: Displays live transition checking, clearance stages, and prompt injection defense.
6. **Zero Cloud Dependency**: Runs entirely locally using Python standard library HTTP server and embedded HTML5 canvas.
