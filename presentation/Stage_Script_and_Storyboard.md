# 28. Presentation, speech, and the judge interaction

## The six-slide deck

| Slide | Purpose | Evidence / visual |
|---|---|---|
| 1 | State the problem and the PS1 + PS3 fusion | One failed-camera scene; no invented competition statistics |
| 2 | Explain the control and authority boundary | Simplified architecture; VQA has no actuation key |
| 3 | Hand control to the live demo | One sentence: choose the camera failure |
| 4 | Show traffic results | Matched baseline/recovery curves with units and seed count |
| 5 | Show PS3 evidence | Routing comparisons, FGSM results, injection false alarms/mutations |
| 6 | State scope and the contribution | What runs, what is simulated, what remains unvalidated |

## Five-minute choreography

0:00-0:35: state the problem and what is actually operating. 0:35-1:10: show the normal observation/action loop and identify the four controlled intersections. 1:10-2:10: let the judge select a camera failure; display missing raw data and estimated queue uncertainty. 2:10-3:00: show genuine candidate predictions, selected action, and actual resulting phase. 3:00-3:45: ask an image/decision question and demonstrate the actuation boundary with a visual instruction attempt. 3:45-4:40: show measured traffic and security results. 4:40-5:00: state limitations and close.

Camera dropout is the default reliable interaction. Add a lane closure or emergency route only when it is integrated and reset-tested. Do not present a perturbed image as universally defeated; show the specific tested model and outcome.

## Speech draft for P4

"A traffic camera going silent should not make a controller believe the road is empty. We built AEGIS to keep the difference between what is observed, what is estimated, and what is unknown visible throughout a traffic-control decision.

This is our running CARLA-SUMO environment. These four signal systems share a cooperative controller. The camera frames are processed into lane observations, and each signal action passes through a reviewed transition manager.

Please choose which camera to disable. Notice that its raw count becomes unavailable; we do not replace it with zero. The system continues from recent and neighboring evidence and shows the uncertainty in its estimate.

These are the recovery candidates evaluated in separate SUMO workers. The numbers are predictions, not measured alternative futures. This selected plan passed the configured constraints, and this is the action that the live coordinator actually executed.

Now we can ask about the relevant frame or decision. The visual assistant can inspect and explain evidence, but it cannot directly set a traffic-light phase. An instruction embedded in an image does not acquire the operator's authority.

Here are our measured comparisons, including the sample size, fault schedule, waiting time, fuel units, and remaining queues. Here are the separate VQA routing and adversarial results. We have not certified a real city or proved universal attack resistance. We have built and evaluated a transparent recovery loop within this simulation scope."

Insert actual outcomes only after measurement. If the learned policy does not beat the baseline, change the narration to state what did and did not improve. If the demonstration is replayed, announce that at the start of the replay.

## Questions to rehearse

Why MAPPO rather than fixed-time? Answer with the actual cooperative objective and comparison. Where is the checkpoint from? Show the manifest. What does a failed camera reveal? Show the observation schema and leakage test. Why not trust the language model to control signals? Explain the authority boundary. Is the fuel real? Explain the simulation model, version, and units. What did the $5 pay for? Show actual running/storage/transfer costs, not the original estimate.

