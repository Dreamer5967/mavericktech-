# AEGIS P4 — AI/VQA Question Service

A lightweight FastAPI service that provides text-based Q&A and optional
visual question answering (VQA) for the AEGIS operator dashboard.

## Responsibilities

- Answer operator questions about traffic conditions using live snapshot data
fetched from the P2 camera observation API.
- Optionally answer visual questions about camera images using the ViLT model.
- **Read-only role** — no access to control endpoints (`/faults`, `/reset`).

## Quick start

```bash
# 1. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and edit the example env file
copy .env.example .env
# Edit .env to point AEGIS_CAMERA_API_URL at the running P2 observation worker.

# 4. Start the service (text Q&A only — no model download)
uvicorn main:app --host 127.0.0.1 --port 8001

# 5. (Optional) Enable VQA — downloads ~450 MB ViLT model on first use
# In .env: set AEGIS_VQA_ENABLED=true
# Install extra deps:
pip install torch torchvision
# Then start the service as above.
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Service liveness + mock backend reachability |
| `POST` | `/api/v1/questions` | Text Q&A from snapshot data |
| `POST` | `/api/v1/questions/vqa` | Image + text VQA (opt-in) |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AEGIS_CAMERA_API_URL` | `http://127.0.0.1:8765` | URL of loopback P2 camera API |
| `AEGIS_QA_PORT` | `8001` | Port this service listens on |
| `AEGIS_VQA_ENABLED` | `false` | Enable ViLT VQA (requires torch + transformers) |
| `AEGIS_VQA_MODEL` | `dandelin/vilt-b32-finetuned-vqa` | HuggingFace model ID |

## Running alongside P2

```
Terminal 1:  start the P2 live-feed worker on loopback port 8765
Terminal 2:  cd apps/api  &&  uvicorn apps.api.main:app --host 127.0.0.1 --port 8001
Terminal 3:  cd apps/web  &&  npm run dev
```

The Vite dev server (`localhost:5173`) proxies:
- `/api/v1/questions` → `http://127.0.0.1:8001`
- `/api/v1/questions/vqa` → `http://127.0.0.1:8001`
- `/health` → `http://127.0.0.1:8765` (P2 observation API)
- `/api` → `http://127.0.0.1:8765` (camera observations and bounded frame cache)

## Security notes

- No operator token is accepted or forwarded by this service.
- API keys and model paths must be in `.env` — never commit `.env`.
- Body size limits: 4 KB for text requests, 10 MB for VQA image payloads.
- VQA answers are always labelled `ESTIMATE_NOT_MEASUREMENT`.

