# Person 1 (P1) Task Sheet: Quality, Compliance, Evidence & Presentation

**Project**: AEGIS — Fault-Tolerant Traffic Control & Secure Multimodal Assistance  
**Competition**: Code Spark 2026 (Smart Technologies PS1 & PS3)  
**Role Owner**: Person 1 (P1)  
**Operating Environment**: Windows (PowerShell, Python 3.13, Git, Microsoft PowerPoint)  

---

## 1. Executive Summary & Core Mandate

As **P1**, you are the **System Quality, Compliance, Budget, and Presentation Lead**. 

Your objective is to make AEGIS understandable, testable, and presentation-ready without owning heavy simulation or model training code. You do not train MAPPO or run CARLA locally; instead, you ensure the team hits every requirement in the brief, safeguards the $5.00 cloud budget, verifies data contracts, and authors the winning 6-slide pitch deck for judging.

> [!NOTE]
> **No MacBook Required**: All P1 tasks run natively on Windows using Python, standard markdown/CSV tools, and Microsoft PowerPoint.

---

## 2. P1 Owned Files & Artifacts

All files listed below are owned and maintained by P1:

| Artifact / File Path | Purpose | Ticket | Status |
| :--- | :--- | :---: | :---: |
| [`P1_TASKS.md`](file:///c:/Users/amalh/Downloads/code%20spark/P1_TASKS.md) | Master P1 Task Specification & Roadmap | All | Active |
| [`submission_checklist.md`](file:///c:/Users/amalh/Downloads/code%20spark/submission_checklist.md) | PS1 & PS3 Master Deliverable & Compliance Matrix | P1-01 | Complete |
| [`manifests/cost_log.csv`](file:///c:/Users/amalh/Downloads/code%20spark/manifests/cost_log.csv) | $5.00 Cloud Budget Audit & Spending Checkpoints | P1-02 | Complete |
| [`tests/phase_cases.md`](file:///c:/Users/amalh/Downloads/code%20spark/tests/phase_cases.md) | 12 Safety Phase Guard Edge Cases (Handoff to P3) | P1-03 | Complete |
| [`presentation/evidence_index.md`](file:///c:/Users/amalh/Downloads/code%20spark/presentation/evidence_index.md) | Standardized Evidence Registry & Screenshot Protocols | P1-05 | Complete |
| [`presentation/slides.md`](file:///c:/Users/amalh/Downloads/code%20spark/presentation/slides.md) | The 6-Slide Master Pitch Deck with Speaker Cues | Core | Complete |
| [`evaluation/`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/) | Blank Benchmark Result Tables (Traffic, VQA, Attacks) | P1-04 | Audited |

---

## 3. Detailed P1 Tickets & Implementation Breakdown

### Ticket P1-01: PS1/PS3 Compliance Matrix
- **File**: [`submission_checklist.md`](file:///c:/Users/amalh/Downloads/code%20spark/submission_checklist.md)
- **Objective**: Track every single requirement of Smart Technologies PS1 and PS3 across teammates:
  - `REQ-01`: CARLA 0.9.15 + SUMO in Town05 (Owner: P2)
  - `REQ-02`: YOLOv10 roadside cameras & vehicle counting (Owner: P2)
  - `REQ-03`: Cooperative MAPPO across 4+ intersections (Owner: P3)
  - `REQ-04`: Camera fault injection & uncertainty interval recovery (Owner: P2 + P3)
  - `REQ-05`: Safety Phase Guard (Owner: P3, based on P1's `tests/phase_cases.md`)
  - `REQ-06`: Quantitative traffic evaluation (waiting time, queue, fuel) (Owner: P3)
  - `REQ-07`: Multi-model VQA dynamic routing (Owner: P4)
  - `REQ-08`: Adversarial FGSM vision testing (Owner: P2 + P4)
  - `REQ-09`: Prompt injection defense & privilege boundary (Owner: P4)
  - `REQ-10`: Docker Compose reproducible packaging (Owner: P2 + P4)
  - `REQ-11`: 6-Slide Master Presentation Deck (Owner: P1)
  - `REQ-12`: Cloud budget tracking under $5.00 (Owner: P1)
- **Rule**: Never mark an item "Verified" unless an actual artifact file exists.

---

### Ticket P1-02: Cloud Budget & Cost Tracking
- **File**: [`manifests/cost_log.csv`](file:///c:/Users/amalh/Downloads/code%20spark/manifests/cost_log.csv)
- **Objective**: Prevent the team from getting disqualified due to account suspension or mid-demo shutdown.
- **Budget Envelopes**:
  - Total credit: **$5.00**
  - Emergency reserve: **$1.00** (strictly untouched)
  - Transfer/storage allowance: **$0.50**
  - Available compute: **$3.50** (max ~11.6 hours at $0.30/hr)
- **Verification Command** (Run from `starter/`):
  ```powershell
  python -m aegis_helpers.budget --credit 5.0 --compute 0.30 --storage 0.02 --transfer 0.50 --reserve 1.0
  ```
- **Action**: Check Vast.ai balance with P2 hourly and log entries in `cost_log.csv`.

---

### Ticket P1-03: Safety Phase Guard Edge Cases (Technical Contribution)
- **File**: [`tests/phase_cases.md`](file:///c:/Users/amalh/Downloads/code%20spark/tests/phase_cases.md)
- **Objective**: Author test boundary conditions for P3's phase manager before signals can change in the live simulator.
- **Key Edge Cases Defined**:
  1. *Minimum Green*: Rejects transitions if elapsed green < 10.0s (`minimum_green`).
  2. *Stale Revision*: Rejects proposals based on outdated world ticks (`stale_revision`).
  3. *Stale Observation*: Rejects proposals when camera age > 2.0s (`stale_state`).
  4. *Missing Sensor Fallback*: Emits `observed_count: null` and enforces `[lower_queue, upper_queue]`. Never treats missing raw data as 0.
  5. *Clearance Sequence*: Enforces `YELLOW` and `ALL_RED` transition stages between conflicting movements.

---

### Ticket P1-04: Blank Benchmark Result Audit
- **Directory**: [`evaluation/`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/)
- **Objective**: Ensure all result tables remain completely blank until measured:
  - [`traffic_results.csv`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/traffic_results.csv): Waiting time, stopped delay, fuel.
  - [`vqa_routes.csv`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/vqa_routes.csv): Routing latency and accuracy.
  - [`adversarial_vqa.csv`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/adversarial_vqa.csv): Clean vs. FGSM scores.
  - [`prompt_injection.csv`](file:///c:/Users/amalh/Downloads/code%20spark/evaluation/prompt_injection.csv): Unauthorized actuation rejection rate.
- **Rule**: If a model fails to beat the baseline, report the honest numbers. Transparent engineering scores higher than fake perfection.

---

### Ticket P1-05: Evidence Standards & Media Registry
- **File**: [`presentation/evidence_index.md`](file:///c:/Users/amalh/Downloads/code%20spark/presentation/evidence_index.md)
- **Naming Rule**: `run_<RUN_ID>_j<JUNCTION_ID>_<CONDITION>_<TIMESTAMP>.png`
- **Labeling Rule**: Tag every visual asset as **MOCK**, **REPLAY**, or **LIVE**.
- **Contingency**: Save one full backup screen recording of the recovery demo locally on your laptop in case cloud networking lags during judging.

---

## 4. Main Deliverable: 6-Slide Pitch Structure (5-Minute Presentation)

Detailed in [`presentation/slides.md`](file:///c:/Users/amalh/Downloads/code%20spark/presentation/slides.md) and synchronized with P4's speech script in [`presentation/Stage_Script_and_Storyboard.md`](file:///c:/Users/amalh/Downloads/code%20spark/presentation/Stage_Script_and_Storyboard.md):

```
+-----------------------------------------------------------------------------------------+
| SLIDE 1: THE PROBLEM                                                                    |
| "A camera going dark should never make a controller believe the road is empty."         |
| Focus: Real-world perception failure & PS1 + PS3 fusion.                                |
+-----------------------------------------------------------------------------------------+
| SLIDE 2: ARCHITECTURE & AUTHORITY BOUNDARIES                                            |
| "Three isolated planes. Single live clock coordinator. Zero actuation rights for VQA."   |
| Visual: assets/architecture.png                                                         |
+-----------------------------------------------------------------------------------------+
| SLIDE 3: INTERACTIVE LIVE DEMO TRANSITION                                               |
| "Judge, please choose any intersection camera to drop."                                 |
| Visual: assets/dashboard.png (J2 count turns null, uncertainty interval activates)      |
+-----------------------------------------------------------------------------------------+
| SLIDE 4: TRAFFIC EVIDENCE & MARL BENCHMARKS                                             |
| "Under sensor blackout, unrecovered policies cascade into gridlock. AEGIS saves delay." |
| Visual: Matched waiting time & fuel consumption curves from evaluation/traffic_results  |
+-----------------------------------------------------------------------------------------+
| SLIDE 5: PS3 VQA ROUTING & PROMPT INJECTION DEFENSE                                     |
| "Dynamic model routing slashes latency; visual prompt injections 100% defended."       |
| Visual: Routing latency table & prompt injection rejection audit                        |
+-----------------------------------------------------------------------------------------+
| SLIDE 6: SCOPE, LIMITATIONS & ROAD AHEAD                                                |
| "Transparent engineering: what ran live, what was simulated, and what remains future."  |
| Focus: Honest research boundaries within 12 hours and $5 budget.                        |
+-----------------------------------------------------------------------------------------+
```

---

## 5. Timeline & Milestones for P1

- **Hours 0–2 (Gate 1)**: Initialize checklist, cost log, phase edge cases, and slide skeleton.
- **Hours 2–5 (Gate 2)**: Build architecture slides, align with P4 on speech cues, verify P2's first CARLA frame.
- **Hours 5–8 (Gate 3)**: Collect live UI screenshots, verify naming convention, audit cloud spending checkpoints.
- **Hours 8–10 (Gate 4)**: Receive real benchmark numbers from P3 and P4; insert into slides.
- **Hours 10–12 (Gate 5)**: Full rehearsal with P4, export final `.pptx` and `.pdf`, verify local backup recording.

---

## 6. How to Push This Task File to GitHub

From your terminal, run:

```powershell
cd "c:\Users\amalh\Downloads\code spark"
git add P1_TASKS.md
git commit -m "docs(p1): add master P1 task sheet and deliverables roadmap"
git push -u origin main
```
