# AEGIS / CodeSpark

AEGIS hackathon source and team handoff. Person 2 maintains `main` integration.
The original P1–P4 responsibilities are unchanged: see `team/`.

Start with `CODEX_START_HERE.md` and `docs/P2_Live_Cloud_Status.md`.

- `starter/`: the original mock, helpers, and setup references.
- `p2/`: real camera smoke capture, saved-image detector comparison, and a draft observation-only handoff.
- `team/`, `docs/`, `assets/`, `presentation/`: original project references and team assignments.
- `evaluation/`: unfilled benchmark templates; smoke results are not benchmark values.

Run the dependency-free checks from this checkout:

```powershell
py -3.14 -B -m unittest discover -s p2/tests -v
Push-Location starter
py -3.14 -B -m unittest discover -s tests -v
Pop-Location
```

The cloud interpreter remains Python 3.10 in the existing `venv-sim`.
Do not run the historical installation commands against the working environment
without reviewing their effect. The actual installed NumPy/OpenCV versions differ
from the starter's candidate dependency inputs.

Simulator binaries, virtual environments, keys, checkpoints, and raw evidence
belong outside this checkout. No code here automatically commits, pushes, rents,
restarts, loads a map, or advances the live simulation clock.
