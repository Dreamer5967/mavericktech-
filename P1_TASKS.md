# P1 Task Sheet: My Working Files & Deliverables

**Role**: P1 (Quality, Compliance, Evidence & Presentation)  
**Environment**: Windows (PowerShell, Python, PowerPoint)  

---

## 1. My Working Files (What I Own)

I am responsible only for the following files in this project:

```
├── P1_TASKS.md                        <-- This task guide
├── submission_checklist.md            <-- Deliverables & compliance tracker
├── manifests/
│   └── cost_log.csv                   <-- $5.00 cloud spending log
├── tests/
│   └── phase_cases.md                 <-- 12 safety edge cases for the traffic light manager
├── presentation/
│   ├── slides.md                      <-- 6-slide pitch deck & script cues
│   └── evidence_index.md              <-- Registry for screenshots, videos & benchmark logs
└── evaluation/                        <-- Empty result tables to audit
    ├── traffic_results.csv
    ├── vqa_routes.csv
    ├── adversarial_vqa.csv
    └── prompt_injection.csv
```

---

## 2. File-by-File Breakdown & Actions

### 1. `submission_checklist.md` (Compliance Matrix)
* **What it is**: Tracks the 12 required competition deliverables across the team.
* **My Action**:
  - Keep each requirement mapped to its owner (P2 for CARLA/SUMO/YOLO, P3 for MAPPO/Estimator, P4 for Dashboard/VQA, P1 for PPT/Budget).
  - Verify that no deliverable is marked done until an actual code or result file is produced.

---

### 2. `manifests/cost_log.csv` (Budget Tracker)
* **What it is**: Audits the $5.00 cloud spend on Vast.ai.
* **My Action**:
  - Log hourly checkpoints of compute rate, storage, and balance with P2.
  - Enforce our strict rule: Keep an untouched **$1.00 reserve** so the system doesn't shut down before judging.
* **Local Check Command**:
  ```powershell
  python -m aegis_helpers.budget --credit 5.0 --compute 0.30 --storage 0.02 --transfer 0.50 --reserve 1.0
  ```

---

### 3. `tests/phase_cases.md` (Safety Phase Guard Edge Cases)
* **What it is**: 12 critical test edge cases for the traffic signal controller.
* **My Action**:
  - Hand this specification off to P3 to implement in the phase manager.
  - Ensures lights cannot change before 10s of green, cannot skip yellow/all-red clearance, and cannot treat dropped cameras as zero cars.

---

### 4. `presentation/slides.md` (6-Slide Master Presentation Deck)
* **What it is**: The exact content for our 5-minute pitch deck.
* **My Action**:
  - **Slide 1**: The Problem (camera failures causing traffic gridlock).
  - **Slide 2**: System Architecture & Privilege Boundary (VQA cannot change lights).
  - **Slide 3**: Live Demo Handoff (judge drops a camera, system recovers).
  - **Slide 4**: Traffic Results (waiting time & fuel improvements).
  - **Slide 5**: VQA & Security Evidence (dynamic model routing & prompt injection defense).
  - **Slide 6**: Scope & Limitations (honest engineering boundaries).
  - Convert this outline into our final PowerPoint presentation (`.pptx`).

---

### 5. `presentation/evidence_index.md` (Evidence & Media Registry)
* **What it is**: Naming and storage rules for all presentation visuals.
* **My Action**:
  - Enforce naming format: `run_<ID>_j<JUNCTION>_<CONDITION>_<TIMESTAMP>.png`.
  - Mark every visual on slides as **MOCK**, **REPLAY**, or **LIVE**.
  - Keep a local backup recording of the recovery demo on my laptop for judging.

---

### 6. `evaluation/*.csv` (Audit Result Tables)
* **What it is**: Benchmark tables for traffic, routing, and attack tests.
* **My Action**:
  - Keep tables clean and blank until real test runs finish.
  - Prevent any fake or placeholder numbers from reaching the slides.

---

## 3. How to Push My Files to GitHub

From the project root (`c:\Users\amalh\Downloads\code spark`):

```powershell
# 1. Stage only my working files
git add P1_TASKS.md submission_checklist.md manifests/ tests/ presentation/ evaluation/

# 2. Commit my files
git commit -m "docs(p1): update P1 working files and deliverables"

# 3. Push to GitHub
git push -u origin main
```
