# AEGIS - GitHub and Codex workflow (4 people, unchanged roles)

## Recommended branch ownership

- `main`: protected, runnable team integration branch. Person 2 can act as maintainer/merge coordinator as agreed.
- `p1-ppt-evidence`: Person 1 light coding, validation/evidence and presentation.
- `p2-cloud-sim`: Person 2 cloud/CARLA/SUMO/YOLO and live coordinator.
- `p3-marl-recovery`: Person 3 controller/MAPPO/estimation/recovery/evaluation.
- `p4-app-vqa`: Person 4 UI/backend/VQA/security/speech.

**Keep the team's existing actual branch names if they have already created branches.** Names above are examples, not instructions to rename them. Do not change assignments. Everyone develops and pushes on their own branch; tested work is merged to `main` by PR/review. If P2 must make changes directly on main by a team agreement, make small reviewed commits and avoid force pushes.

## Keep large simulator assets out of Git

On the rented Vast instance:

```text
/workspace/aegis/
  carla/                    # 0.9.15 server binaries: DO NOT COMMIT
  downloads/                # ~8GB CARLA archive and logs: DO NOT COMMIT
  venv-sim/                 # Python packages: DO NOT COMMIT
  venv-vqa/                 # future env: DO NOT COMMIT
  evidence/                 # raw frames: do not blindly commit
  repo/                     # THIS is your GitHub checkout
```

The original kit already contains `starter/`, `team/`, `docs/`, `evaluation/`, `presentation/`, and `assets/`. Keep those names. Put new P2 source under a dedicated `p2/` directory inside the repo, and place any shared schemas in `docs/` or `contracts/` after agreeing with P3/P4.

## Clone the EXISTING GitHub repo on the server (when ready)

Do **not** run `git init` inside `/workspace/aegis` or clone into `/workspace/aegis/carla`.

```bash
mkdir -p /workspace/aegis
# Replace with your real GitHub repo URL from its green Code button.
git clone https://github.com/YOUR_TEAM/YOUR_REPO.git /workspace/aegis/repo
cd /workspace/aegis/repo
git status -sb
git branch -a
```

If the target directory exists, inspect it rather than deleting it or cloning again. If the repo is private, authenticate interactively using GitHub's supported method. Do not embed a token in the remote URL, shell history, or the repository. GitHub SSH authentication is distinct from SSH access to Vast.

## Switch to your EXISTING P2 branch, if your team has one

```bash
cd /workspace/aegis/repo
git fetch --all --prune
git branch -a
# Example ONLY; substitute your team's real branch name.
git switch p2-cloud-sim
```

If that branch only exists on GitHub and isn't tracked locally, use `git switch --track origin/p2-cloud-sim`. If you're the integration maintainer and intentionally staying on main, use `git switch main`; discuss this with the team before applying experimental changes.

## Initial commit: import docs and starter SAFELY

- Unzip the **updated AEGIS Codex Handoff Kit** on your own laptop, next to the GitHub clone; copy the files into your checkout **only after reviewing existing teammate changes**.
- Do not commit the ZIP itself, cloud binaries, Python environments, generated models, raw frame dumps, credentials, or private keys.
- Commit the original kit's small source/docs/assets as needed; `team/*.pdf` and the manual PDFs are reference artifacts, not source code. Keep Git history manageable.
- On the server, first inspect `git status` and `.gitignore`. Never run `git add -A` at `/workspace/aegis`.

Suggested minimal commands from a Git checkout:

```bash
git status -sb
git add .gitignore CODEX_START_HERE.md docs/P2_Live_Cloud_Status.md docs/GitHub_Workflow.md scripts/p2_check_instance.sh
git diff --cached --stat
git commit -m "docs: hand off verified P2 CARLA and YOLO setup"
git push -u origin YOUR_BRANCH_NAME
```

The `git push` line needs your actual branch name and authenticated GitHub access. Nothing here automatically pushes to GitHub or changes the rented instance.

## Code collaboration contracts

- P2 publishes timestamped observations with camera IDs, frame source/time, measured detector counts, missing/stale status, and explicit `null` for unavailable measurements.
- P3 consumes observation-only messages and owns training/recovery. P3 must not run a second live CARLA or SUMO tick loop.
- P4 consumes P2 observations through a stable API and owns application/VQA/security/UI and the stage speech.
- P1 validates/evidences the demo and makes the presentation.
- `docs/API_and_Data_Contracts.md` defines suggested routes; don't silently rename them without a joint agreement.
- Keep metrics labeled mock vs. live; benchmark CSV values only from reproducible trials.

## Codex setup

Best workflow: open `/workspace/aegis/repo` from VS Code using **Remote - SSH** (user authenticates with the key on their Windows machine), then use Codex in that remote project if supported. Alternatively, use Codex against a local clone, commit and push, and pull on the GPU instance. You **do not** give Codex your private key or Vast password.
