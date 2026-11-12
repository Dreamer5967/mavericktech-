# Revision 2 setup changes

Updated 12 November 2026.

## Unchanged assignments

All twelve handoff source files (four PDFs, four DOCXs and four Markdown sheets) are byte-for-byte the original files. Handbook chapters 4, 20, 21, 22, 23 and 24 retain their original text. There is no optional MacBook compute role.

## Technical changes

- Two cloud Python 3.10 environments: venv-sim for CARLA client, matched SUMO tools, YOLOv10 and the API; venv-vqa for ViLT/Transformers and Langfuse.
- Explicit interpreter paths reduce activation mistakes between SSH/tmux terminals.
- Maintained Ultralytics YOLO("yolov10n.pt") example replaces the separate fork-install path.
- ASCII command options and CLEAN_COMMANDS.md provide a copyable source for -m, --create-home, --tls-manager and SSH forwarding.
- setup_two_envs.sh creates environments only. environment_smoke.py checks imports/device availability; rendering remains a separate real-frame test.
- Existing local app requirements remain available for P4; they do not create a third cloud environment.

The package is a candidate setup to verify on your chosen host, not a prevalidated cloud lockfile. No rental, model training or real benchmark was performed for this revision.
