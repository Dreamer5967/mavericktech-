# Evaluation Evidence Directory

> [!IMPORTANT]
> **Data Mode Distinction**:
> - `traffic_results.csv` and `planner_results.csv` populated in this branch represent **SYNTHETIC_PRE_COSIM_EVALUATION** (using verified Poisson arrival dynamics and queue discharge functions on Town10HD_Opt topology).
> - They provide algorithmic baseline verification for MAPPO and the Recovery Planner before live CARLA–SUMO bridge connection.
> - They must **NOT** be represented as measured CARLA–SUMO gains until executed on P2's cloud instance with live TraCI and CARLA co-simulation.
> - Live co-simulation results will be recorded separately during Gate 2 cloud integration.
