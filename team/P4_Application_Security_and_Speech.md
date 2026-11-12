# 23. Person 4 handoff: application, security, speech, and demo

You own one integrated operator experience. Keep the screen simple enough to build and explain. Use the mock immediately; do not wait for CARLA to begin UI work. Protect the speech preparation slot and stop adding optional UI features when that slot begins.

## Implementation tickets in order

| Ticket | Action | Output | Acceptance |
|---|---|---|---|
| P4-01 | Start local UI/API and fixtures | Health + mock snapshot screen | Four junctions visible without cloud |
| P4-02 | Add frame/state subscriptions and status | LIVE/MOCK/REPLAY modes | Source timestamps and lag are obvious |
| P4-03 | Add authenticated incident requests | Judge control panel | Allowlist, idempotency, validation, reset |
| P4-04 | Add image/question sessions and real routing | VQA API + evidence references | Two actual model backends are tested |
| P4-05 | Add authority boundary and injection tests | Read-only VQA worker + test suite | Image instructions cannot call control endpoints |
| P4-06 | Connect Langfuse + evaluation scores | Searchable traces | Actual route/model/latency visible |
| P4-07 | Package real frontend/backend | Compose and setup instructions | Fresh application deployment tested |
| P4-08 | Write and rehearse speech | 3-minute and 5-minute scripts | Every claim matches current evidence |

## UI development sequence

Build the readiness panel, the four intersection cards, one frame viewer, and one incident control first. Then add the candidate-plan drawer, the question panel, and the metrics view. Keep empty, loading, stale, failed, and reset states explicit. A disconnected backend should not leave the last values looking live.

Use server-side state as the authority. The UI sends an incident request and waits for an applied/rejected event. It never changes a label to "recovered" simply because a button was clicked. A live diagram should reflect actual state messages.

## Backend and security scope

Implement a small operator/session role boundary. Only operator requests can reset or inject allowlisted faults. The question worker has no simulator/admin token. Validate image type and dimensions; re-encode uploaded images; cap body sizes and question lengths. Do not log API keys or display environment variables in the telemetry panel.

Maintain deterministic numerical tools for comparisons. The router can use a simple transparent rule/classifier initially. Log its reason and compare against single-model baselines. If a route is unavailable or a key has no quota, return an explicit degraded response; never substitute a canned answer without labeling it.

## Split adversarial work with P2

You own test questions, prompt-injection cases, detector threshold selection, provider routing, and result interpretation. P2 owns scheduling/running the local ViLT gradient jobs on suitable hardware. Agree on sample manifests, epsilon scale, clean/attack/defense conditions, and output schema before the job starts. You both review false positives, not only successful attack blocks.

## Protected presentation time

By hour 8, freeze the narration outline. Reserve roughly hour 9-10 for writing and rehearsing with P1's deck. P2 handles live-runtime recovery while you rehearse. Prepare one concise explanation of each technical component and a clear answer to "What did you actually measure?"

During presentation, you speak and guide the judge. P1 advances slides, P2 handles any simulator restart, and P3 answers detailed control questions. Practice the same roles before judging. A rehearsed reset is more useful than another animation.


# Shared handoff rules

Develop against the versioned observation/proposal/execution contract in handbook section 18. P2 alone owns live simulation ticks and restarts. Do not present mock values as metrics. All benchmark tables remain empty until measured. P1 has protected PPT time; P4 has protected speech time. Keep credentials out of Git, screenshots and recordings.

Use the complete handbook for setup, requirements and source references. This task sheet is an ownership guide, not a complete stand-alone simulator installer.
