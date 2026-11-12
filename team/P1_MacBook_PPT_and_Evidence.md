# 20. Person 1 handoff: MacBook, evidence, and PPT

Your job is to make the system understandable, testable, and presentable without becoming its main implementation owner. You are not responsible for installing CARLA, training MAPPO, maintaining the router, or implementing the whole dashboard.

## First 2-3 hours: a bounded technical contribution

| Ticket | Exact action | Output | Acceptance |
|---|---|---|---|
| P1-01 | Read PS1/PS3 and mark each requested deliverable | Compliance checklist | Every item has a named owner and evidence path |
| P1-02 | Record $5 starting credit, offer details, and budget checkpoints | Cost log | Storage/transfer are not omitted |
| P1-03 | Run the starter tests and review the phase-guard edge cases | Test log + additional cases | Stale state, unknown phase, missing observation covered |
| P1-04 | Create empty result tables and slide placeholders | CSV/table templates | All results explicitly blank until measured |
| P1-05 | Agree on screenshot/video naming and safe export paths | Evidence checklist | Run IDs and data mode are visible |

Use the supplied phase-request helper to understand the intended tests. P3 owns the real map-specific phase manager. Hand P3 your cases by hour 2-3; do not let this task turn into responsibility for the controller.

## Main deliverable: the slide deck

Prepare six core slides: problem and PS mapping; architecture/authority boundary; live-demo handoff; traffic evidence; VQA/security evidence; limitations and next step. Use actual screenshots after the pipeline works. The report's architecture figures can be reused, but simplify labels for projection. Retain a readable hidden appendix for configuration hashes, metrics definitions, and failure cases.

The live-demo slide is a transition, not a screenshot claiming to be live. Results slides contain the actual sample count, seeds/fault definition, baseline, and units. A failed or inconclusive experiment can be summarized honestly. Do not fill missing values with illustrative improvements.

## Time reservation

Hours 0-2: checklist/tests/cost log and slide skeleton. Hours 2-5: architecture slides and demo outline. Hours 5-8: collect working screenshots, curate the source list, and help organize experiments without writing new major services. Hours 8-10: insert actual results and export a first deck. Hours 10-12: rehearse, export PDF and editable format, verify the presentation laptop, and package evidence.

## Files you own

`presentation/slides.*`, `presentation/architecture_simple.*`, `presentation/evidence_index.md`, `evaluation/result_tables/`, `manifests/cost_log.csv`, `submission_checklist.md`, and `tests/phase_cases.md`. No credentials belong in slides, speaker notes, screenshots, or the backup recording.

## Handoff to the speaker and operators

Give P4 the current deck and an evidence-backed narration outline. Give P2 the exact moment the presentation switches to the live console. Keep a labeled recorded-run backup and exported metrics available locally. Test that the backup opens without the cloud. The recording is contingency evidence, not a substitute to advertise as a live run.

Your final check: every highlighted claim on a slide points to a working feature, a measured result file, or an explicitly labeled future direction.


# Shared handoff rules

Develop against the versioned observation/proposal/execution contract in handbook section 18. P2 alone owns live simulation ticks and restarts. Do not present mock values as metrics. All benchmark tables remain empty until measured. P1 has protected PPT time; P4 has protected speech time. Keep credentials out of Git, screenshots and recordings.

Use the complete handbook for setup, requirements and source references. This task sheet is an ownership guide, not a complete stand-alone simulator installer.
