# AEGIS

Traffic simulation and camera observations using CARLA 0.9.15, YOLOv10n and
CARLA–SUMO co-simulation on the existing cloud instance.

- [P2 tools and commands](p2/README.md)
- [Current runtime and verified results](docs/runtime.md)
- [Camera API and timestamps](docs/api.md)

`main` is the integration branch. Responsibilities remain unchanged: P1 owns
presentation and evidence, P2 simulation and perception, P3 policy and planning,
and P4 the application, security and speech. Teammate branches merge separately.

Run local P2 checks from the repository root:

```powershell
py -3.14 -B -m unittest discover -s p2/tests -v
```

Cloud code uses the existing Python 3.10 `venv-sim`. Live execution requires
appropriate approval. Do not restart CARLA, change maps or advance the clock as
part of setup. Keep keys, credentials, weights, environments, simulator binaries
and generated evidence outside Git.
