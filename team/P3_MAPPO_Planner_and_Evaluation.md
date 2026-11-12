# 22. Person 3 handoff: cooperative policy, estimator, and planner

You own the decision-making system and its traffic evaluation. You can work locally in SUMO while P2 prepares graphics. Match the final map/schema before interpreting a training result as transferable to the live pipeline.

## Implementation tickets in order

| Ticket | Action | Output | Acceptance |
|---|---|---|---|
| P3-01 | Load selected network and fixed-time baseline | Environment adapter + demand seeds | Episode completes; queues/trips logged |
| P3-02 | Freeze observations, masks, actions, reward | Schema/configuration | Four junctions have correct action mappings |
| P3-03 | Connect a verified MAPPO implementation | Training runner | Gradient updates and checkpoint reload work |
| P3-04 | Train/evaluate incremental checkpoints | Manifest + learning/evaluation curves | Held-out performance is measured, not assumed |
| P3-05 | Implement missing-state estimator | Observation-to-belief function | Missing camera does not erase queues |
| P3-06 | Implement reviewed phase manager | Request validator + phase transitions | Minimum green/clearance/revision tests pass |
| P3-07 | Add isolated recovery workers | Candidate inputs/results | Candidates affect the executed first action |
| P3-08 | Run matched controller/fault comparisons | CSV/JSON metrics | Same scenarios, explicit units and failures |

## Start from a small observable training loop

Run a single environment and fixed seed. Inspect one observation/action/reward transition manually. Check that the environment honors phase-clearance states and counts simulated time correctly. Then connect multiple agents. A policy that requests a phase change every step can appear active while the phase manager suppresses almost every request; log requested versus executed actions.

Use CPU development first if the local machine can step the selected network. A GPU does not accelerate every SUMO operation. Request cloud training only after showing which part is slow. Keep training independent from the renderer so the cloud can run the first camera demo while you improve the policy elsewhere.

## Evidence discipline

Do not select a checkpoint using the same episodes later presented as the test set. Save optimizer state only when needed to resume; save a lightweight inference bundle for the demo. The model card states synthetic-noise training conditions, the actual YOLO evaluation conditions, and any mismatch.

When evaluating, compare a reviewed fixed-time baseline, learned policy without recovery, and learned policy with recovery. Optionally include a pressure heuristic. Every comparison retains demand, map, seeds, fault schedule, warm-up, and horizon. Record incomplete trips and teleports so congestion cannot disappear from the metric denominator.

## Planner implementation boundary

Online planning receives an observation-derived belief, not the exact live SUMO state. Create estimated queues and demand assumptions in independent workers. Give all candidates the same belief samples. Enforce deadline/expiry and return `unavailable` on worker failure. The coordinator applies only the first validated action.

Begin with one belief sample and three genuine candidate policies. Add lower/upper uncertainty samples only after the first comparison is functioning. Do not promise three parallel real-time rollouts until timing is measured. If the deadline cannot be met, reduce horizon or scenario count and display that configuration honestly.

## Map-specific safety review with P2

Review controlled links, conflict movements, phase indexes, min-green timing, yellow duration, and clearance behavior. Convert policy green-action indices through this reviewed mapping. Test all legal phase pairs. Run an independent event-log checker for conflicting greens and skipped transition states.

## Final handoff

Provide P2 an inference entrypoint with no training side effects, checkpoint/normalization files, action mappings, and an example input/output. Provide P4 candidate result fields and reason codes. Provide P1 measured result tables plus sample count, seeds, units, and limitations. An unfavorable result is still a result; fabricated improvement is not.


# Shared handoff rules

Develop against the versioned observation/proposal/execution contract in handbook section 18. P2 alone owns live simulation ticks and restarts. Do not present mock values as metrics. All benchmark tables remain empty until measured. P1 has protected PPT time; P4 has protected speech time. Keep credentials out of Git, screenshots and recordings.

Use the complete handbook for setup, requirements and source references. This task sheet is an ownership guide, not a complete stand-alone simulator installer.
