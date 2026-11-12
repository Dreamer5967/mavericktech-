# AEGIS clean commands

Revision 2 - 12 November 2026. Copy commands from this text file. All option hyphens below are ordinary ASCII `-` characters. This is a setup reference, not an automatic cloud installer or a finished AEGIS application.

## 1 Local laptop before renting

Open a terminal in the extracted `starter` folder. These commands use only Python's standard library; no model files or cloud access are needed.

```bash
python3 -m unittest discover -s tests -v
python3 -m aegis_helpers.mock_server
```

On Windows use `py -3.11` instead of `python3` if that is your installed interpreter. Open <http://127.0.0.1:8000>. Keep the `MOCK` label; these are development fixtures. Stop with Ctrl+C. The mock is a small standard-library HTTP server, not FastAPI or React.

## 2 Cloud shell and directories

Choose a Linux x86_64 host with Python 3.10 and working NVIDIA graphics support. The official CARLA 0.9.15 distribution includes a CPython 3.10 Linux x86_64 wheel. Installing that wheel installs the Python client, not the CARLA server. Match server and client versions.

Run as the non-root simulator user in the uploaded/extracted `starter` folder:

```bash
export AEGIS_HOME=/workspace/aegis
export AEGIS_STARTER="$PWD"
test -f "$AEGIS_STARTER/aegis_helpers/mock_server.py"
bash "$AEGIS_STARTER/scripts/preflight.sh"
bash "$AEGIS_STARTER/scripts/setup_two_envs.sh" "$AEGIS_HOME"
```

The selected user must already own a writable `AEGIS_HOME`. If a non-root simulator account does not exist, an administrator can create one with the following exact command, then arrange ownership of the project directory and use that account:

```bash
sudo useradd --create-home --shell /bin/bash aegisrun
```

Do not repeat the account-creation command for an existing account. Do not run the CARLA server as root. On a rental container, do not assume `sudo` or nested Docker is available; follow the selected image's access model.

The environment script runs the equivalent of:

```bash
python3.10 -m venv "$AEGIS_HOME/venv-sim"
python3.10 -m venv "$AEGIS_HOME/venv-vqa"
```

Use the script when rerunning setup: it checks existing environments instead of silently recreating them.

## 3 Install the chosen PyTorch build

Use <https://pytorch.org/get-started/locally/> to choose a mutually compatible `torch` and `torchvision` build for the host's NVIDIA driver. This is a hardware-specific selection, not something `nvidia-smi` alone validates. Run the selected install command with each explicit interpreter below, replacing only the selector command's `pip`/`pip3` prefix:

```bash
"$AEGIS_HOME/venv-sim/bin/python" -m pip install --upgrade pip setuptools wheel
"$AEGIS_HOME/venv-vqa/bin/python" -m pip install --upgrade pip setuptools wheel
```

For example, if the current selector supplies `pip3 install ...`, use `"$AEGIS_HOME/venv-sim/bin/python" -m pip install ...` with the selector's exact packages and index, then repeat for `venv-vqa`. Do not paste the literal `...`. An older driver may require an older supported PyTorch wheel pair. Record the chosen command and versions. Do not launch model downloads during the presentation.

## 4 Install the workload dependencies

After installing the selected PyTorch pair in both environments:

```bash
"$AEGIS_HOME/venv-sim/bin/python" -m pip install -r "$AEGIS_STARTER/templates/requirements-sim.in"
"$AEGIS_HOME/venv-vqa/bin/python" -m pip install -r "$AEGIS_STARTER/templates/requirements-vqa.in"
"$AEGIS_HOME/venv-sim/bin/python" -m pip check
"$AEGIS_HOME/venv-vqa/bin/python" -m pip check
```

Use the Python tools supplied with the same SUMO distribution as your executable. For the Ubuntu package location used in the handbook, set the following before imports in each relevant terminal. If SUMO was installed elsewhere, replace `/usr/share/sumo` with its actual distribution root; do not use an unrelated tools directory.

```bash
export SUMO_HOME=/usr/share/sumo
export PYTHONPATH="$SUMO_HOME/tools${PYTHONPATH:+:$PYTHONPATH}"
test -d "$SUMO_HOME/tools/traci"
"$AEGIS_HOME/venv-sim/bin/python" -c 'import traci; print(traci.__file__)'
"$AEGIS_HOME/venv-sim/bin/python" "$AEGIS_STARTER/scripts/environment_smoke.py" --stack sim --require-cuda
"$AEGIS_HOME/venv-vqa/bin/python" "$AEGIS_STARTER/scripts/environment_smoke.py" --stack vqa --require-cuda
```

These `.in` files are dependency inputs, not a tested lockfile. The OpenCV upper bound preserves compatibility with the NumPy 1.x constraint. `traci` and `sumolib` must match the installed SUMO release: check `sumo --version`, package versions and the printed `traci.__file__`. The matching distribution's tools take priority through the `PYTHONPATH` prefix above; pip package metadata may still describe a different installed copy. Alternatively, install matching pip package versions and consistently use those instead of mixing copies. A passing import check does not establish rendering, camera calibration, network mapping or model accuracy.

The VQA probe may use CPU if scheduled GPU access is unavailable; omit `--require-cuda` for that explicit CPU smoke test. Do not describe it as a GPU result. Keep Python 3.10 services bound to loopback and access them through SSH for this bounded compatibility setup.

## 5 Real simulator gates

Install the official CARLA 0.9.15 server distribution and the SUMO executable separately, then follow the handbook's rendering and map setup gates. While CARLA is asynchronous and the co-simulation coordinator is stopped:

```bash
"$AEGIS_HOME/venv-sim/bin/python" "$AEGIS_STARTER/scripts/camera_smoke.py" --output "$AEGIS_HOME/smoke/camera.png"
```

This probe checks client/server version agreement and saves a real camera frame. Inspect the image. Run YOLOv10 on that saved image before integrating continuous inference. Once the coordinator is running, do not start this standalone probe or a second script that calls `world.tick()`.

With the official 0.9.15 source tree downloaded and `CARLA_SOURCE` set to its absolute path, run the official co-simulation script with SUMO as traffic-light authority. Choose a real, verified `.sumocfg`; the placeholder path below must be replaced:

```bash
cd "$CARLA_SOURCE/Co-Simulation/Sumo"
"$AEGIS_HOME/venv-sim/bin/python" run_synchronization.py /absolute/path/to/verified.sumocfg --tls-manager sumo
```

P2 owns this live process. P3's rollout workers use separate headless SUMO instances. A shared Python environment does not grant any other worker ownership of CARLA's clock.

## 6 API tunnel from the presentation laptop

Keep the API bound to cloud `127.0.0.1:8000`. In a local terminal, replace the SSH port and destination with the values supplied for your own instance:

```bash
ssh -N -L 8000:127.0.0.1:8000 -p SSH_PORT USER@HOST
```

If the local mock already uses port 8000, stop it or use local port 8001:

```bash
ssh -N -L 8001:127.0.0.1:8000 -p SSH_PORT USER@HOST
```

Open <http://127.0.0.1:8000> or <http://127.0.0.1:8001> as appropriate. `SSH_PORT` and `USER@HOST` are placeholders, not literal connection values. The tutorial's API process is still your team's implementation task; the included mock stays visibly `MOCK` if used for this transport check.

In the live app, compress frames and run YOLO near CARLA. Send structured telemetry plus compressed selected views; bound queues and discard stale preview frames. Measure capture-to-display latency and show frame age. This reduces network load; it cannot promise zero latency or eliminate stalls.

## 7 Record the working versions

After the imports, real frame, perception and SUMO mapping checks pass:

```bash
mkdir -p "$AEGIS_HOME/manifests"
"$AEGIS_HOME/venv-sim/bin/python" -m pip freeze > "$AEGIS_HOME/manifests/requirements-sim.lock.txt"
"$AEGIS_HOME/venv-vqa/bin/python" -m pip freeze > "$AEGIS_HOME/manifests/requirements-vqa.lock.txt"
sumo --version > "$AEGIS_HOME/manifests/sumo-version.txt"
```

Save the server version, host driver, Python version, selected torch command and map/config hashes with those files. Copy evidence off the cloud before shutdown. Check the console's storage and transfer charges as well as compute; stopping a rental may retain billed storage. No script in this kit rents, stops or destroys an instance.

## Official setup references

- CARLA 0.9.15 Python wheels: <https://pypi.org/project/carla/0.9.15/>
- CARLA SUMO synchronization: <https://carla.readthedocs.io/en/0.9.15/adv_sumo/>
- CARLA synchronous clock ownership: <https://carla.readthedocs.io/en/0.9.15/adv_synchrony_timestep/>
- PyTorch install selector: <https://pytorch.org/get-started/locally/>
- Ultralytics YOLOv10: <https://docs.ultralytics.com/models/yolov10/>
- SUMO TraCI: <https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html>
