"""
P4-04 — AI/VQA Question Service tests.

These tests start the P4 FastAPI service on a temporary port (8002) and
the AEGIS mock backend on another temporary port (8003), then verify the
question API behaviour end-to-end.

The tests require the packages in apps/api/requirements.txt to be installed:
  pip install fastapi uvicorn[standard] httpx python-dotenv Pillow

Run with:
  cd starter
  python -m unittest tests.test_question_api -v
"""

import base64
import io
import json
import os
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

# ---------------------------------------------------------------------------
# Make sure both apps/api and starter are importable regardless of CWD
# ---------------------------------------------------------------------------
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
for _p in [os.path.join(_root, 'apps'), _root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------------
# Minimal stub AEGIS mock backend for testing
# ---------------------------------------------------------------------------

_STUB_SNAPSHOT = {
    "schema_version": "1.0",
    "mode": "MOCK",
    "run_id": "test-run",
    "state_revision": 1,
    "sim_time_s": 0.0,
    "notice": "fixture — test data",
    "junctions": [
        {
            "junction_id": "J1",
            "phase": "NS",
            "camera_status": "AVAILABLE",
            "observed_count": 5,
            "estimated_queue": 5.0,
            "queue_interval": [3.0, 7.0],
            "source": "camera",
            "data_quality": "fixture",
        },
        {
            "junction_id": "J2",
            "phase": "EW",
            "camera_status": "MISSING",
            "observed_count": None,
            "estimated_queue": 2.0,
            "queue_interval": [1.0, 3.0],
            "source": "estimate",
            "data_quality": "fixture",
        },
        {
            "junction_id": "J3",
            "phase": "NS",
            "camera_status": "AVAILABLE",
            "observed_count": 10,
            "estimated_queue": 10.0,
            "queue_interval": [8.0, 12.0],
            "source": "camera",
            "data_quality": "fixture",
        },
        {
            "junction_id": "J4",
            "phase": "EW",
            "camera_status": "AVAILABLE",
            "observed_count": 1,
            "estimated_queue": 1.0,
            "queue_interval": [0.0, 2.0],
            "source": "camera",
            "data_quality": "fixture",
        },
    ],
    "plans": [],
    "metrics": None,
}

_SAMPLE_FRAME_BYTES = b""
try:
    from PIL import Image as _PILImage
    _buf = io.BytesIO()
    _PILImage.new('RGB', (64, 64), color=(60, 70, 80)).save(_buf, format='JPEG')
    _SAMPLE_FRAME_BYTES = _buf.getvalue()
except Exception:
    pass


def _make_stub_handler():
    import http.server

    class StubHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            if self.path == '/health':
                self._json(200, {"ok": True, "mode": "MOCK"})
            elif self.path == '/api/v1/snapshot':
                self._json(200, _STUB_SNAPSHOT)
            elif self.path == '/api/v1/frames/J1':
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(_SAMPLE_FRAME_BYTES)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(_SAMPLE_FRAME_BYTES)
            else:
                self._json(404, {"error": "not_found"})

        def _json(self, code, body):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(data)

    return StubHandler


def _start_stub_backend(port: int):
    handler = _make_stub_handler()
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


# ---------------------------------------------------------------------------
# FastAPI test server helpers
# ---------------------------------------------------------------------------

def _start_qa_service(mock_port: int, qa_port: int):
    """Start the P4 FastAPI QA service using uvicorn in a daemon thread."""
    import uvicorn  # type: ignore

    os.environ['AEGIS_MOCK_API_URL'] = f'http://127.0.0.1:{mock_port}'
    os.environ['AEGIS_VQA_ENABLED'] = 'false'
    os.environ['AEGIS_QA_PORT'] = str(qa_port)
    os.environ['GEMINI_API_KEY'] = ''

    # Import after env vars are set so config picks them up
    from api import main as qa_main  # type: ignore

    config = uvicorn.Config(
        qa_main.app,
        host='127.0.0.1',
        port=qa_port,
        log_level='error',
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server


def _wait_for_port(host: str, port: int, timeout: float = 8.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f'http://{host}:{port}/health', timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def _post_json(url: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

MOCK_PORT = 8903
QA_PORT = 8902
QA_BASE = f'http://127.0.0.1:{QA_PORT}'

_services_started = False


def _ensure_services():
    global _services_started
    if _services_started:
        return
    _start_stub_backend(MOCK_PORT)
    try:
        _start_qa_service(MOCK_PORT, QA_PORT)
    except ImportError as exc:
        raise unittest.SkipTest(
            f'P4 QA service dependencies not installed: {exc}'
        )
    if not _wait_for_port('127.0.0.1', QA_PORT):
        raise RuntimeError(f'QA service did not start on port {QA_PORT}')
    _services_started = True


class TestQAServiceHealth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _ensure_services()

    def test_health_ok(self):
        with urllib.request.urlopen(f'{QA_BASE}/health', timeout=5) as resp:
            body = json.loads(resp.read())
        self.assertTrue(body['ok'])
        self.assertEqual(body['service'], 'aegis-qa')
        self.assertFalse(body['vqa_enabled'])

    def test_health_mock_reachable(self):
        with urllib.request.urlopen(f'{QA_BASE}/health', timeout=5) as resp:
            body = json.loads(resp.read())
        self.assertTrue(body['mock_backend_reachable'])


class TestTextQuestions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _ensure_services()

    def _ask(self, question: str, junction_id=None):
        payload = {'question': question}
        if junction_id:
            payload['junction_id'] = junction_id
        return _post_json(f'{QA_BASE}/api/v1/questions', payload)

    def test_question_returns_200(self):
        code, body = self._ask('What is the traffic situation?')
        self.assertEqual(code, 200)
        self.assertIn('answer', body)
        self.assertIn('source', body)
        self.assertEqual(body['source'], 'snapshot')

    def test_question_has_required_fields(self):
        code, body = self._ask('Camera status?')
        self.assertEqual(code, 200)
        for field in ('session_id', 'question', 'answer', 'source', 'status', 'timestamp'):
            self.assertIn(field, body, f'Missing field: {field}')

    def test_question_highest_queue(self):
        code, body = self._ask('Which junction has the highest queue?')
        self.assertEqual(code, 200)
        # J3 has estimated_queue=10 in stub
        self.assertIn('J3', body['answer'])

    def test_question_camera_status(self):
        code, body = self._ask('Camera status?')
        self.assertEqual(code, 200)
        # J2 is MISSING in stub
        self.assertIn('J2', body['answer'])

    def test_question_junction_filter(self):
        code, body = self._ask('What is the phase?', junction_id='J1')
        self.assertEqual(code, 200)
        self.assertEqual(body['junction_id'], 'J1')

    def test_question_summary(self):
        code, body = self._ask('Give me a summary of all junctions')
        self.assertEqual(code, 200)
        self.assertIn('J1', body['answer'])
        self.assertIn('J2', body['answer'])

    def test_question_too_long_rejected(self):
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions',
            {'question': 'x' * 501},
        )
        self.assertIn(code, (400, 422))

    def test_empty_question_rejected(self):
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions',
            {'question': ''},
        )
        self.assertIn(code, (400, 422))

    def test_invalid_junction_id_rejected(self):
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions',
            {'question': 'queue?', 'junction_id': 'J9'},
        )
        self.assertIn(code, (400, 422))

    def test_session_id_echoed(self):
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions',
            {'question': 'mode?', 'session_id': 'test-session-123'},
        )
        self.assertEqual(code, 200)
        self.assertEqual(body['session_id'], 'test-session-123')


class TestVQAUnavailable(unittest.TestCase):
    """When AEGIS_VQA_ENABLED=false the service must return a degraded response,
    not an error, for a valid image + question pair."""

    @classmethod
    def setUpClass(cls):
        _ensure_services()

    def _minimal_jpeg_b64(self) -> str:
        """Return a valid 1×1 JPEG as base64."""
        try:
            from PIL import Image  # type: ignore
        except ImportError:
            raise unittest.SkipTest('Pillow not installed')
        buf = io.BytesIO()
        Image.new('RGB', (1, 1), color=(128, 128, 128)).save(buf, format='JPEG')
        return base64.b64encode(buf.getvalue()).decode()

    def test_vqa_unavailable_returns_degraded(self):
        b64 = self._minimal_jpeg_b64()
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'image_b64': b64, 'question': 'How many vehicles?'},
        )
        self.assertEqual(code, 200)
        self.assertEqual(body['status'], 'VQA_UNAVAILABLE')
        self.assertEqual(body['source'], 'degraded')

    def test_vqa_missing_image_returns_422(self):
        code, _body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'question': 'How many vehicles?'},
        )
        self.assertIn(code, (400, 422))

    def test_vqa_bad_base64_returns_400(self):
        code, _body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'image_b64': '!!!not-valid-base64!!!', 'question': 'test?'},
        )
        self.assertIn(code, (400, 422))

    def test_vqa_non_image_b64_returns_400(self):
        # Valid base64 but not a JPEG/PNG
        fake_b64 = base64.b64encode(b'<html>not an image</html>').decode()
        code, _body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'image_b64': fake_b64, 'question': 'test?'},
        )
        self.assertEqual(code, 400)


class TestCameraApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _ensure_services()

    def test_get_frame_available(self):
        req = urllib.request.Request(f'{QA_BASE}/api/v1/frames/J1')
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn('image/', resp.headers.get('Content-Type', ''))
            content = resp.read()
            self.assertGreater(len(content), 10)

    def test_get_frame_missing_returns_404(self):
        # J2 is MISSING in stub snapshot -> must return 404
        req = urllib.request.Request(f'{QA_BASE}/api/v1/frames/J2')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 404)
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)

    def test_get_frame_unpublished_returns_404(self):
        # J3 is AVAILABLE in snapshot, but no frame buffer published -> must return 404 (never demo image)
        req = urllib.request.Request(f'{QA_BASE}/api/v1/frames/J3')
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 404)
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)

    def test_vqa_with_junction_frame_retrieval(self):
        # When no image_b64 is passed, VQA retrieves frame from camera API
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'junction_id': 'J1', 'question': 'How many vehicles?'},
        )
        self.assertEqual(code, 200)
        self.assertIn('status', body)
        self.assertIn('answer', body)

    def test_vqa_with_dropped_camera_returns_camera_unavailable(self):
        # J2 is MISSING in stub snapshot -> must return CAMERA_UNAVAILABLE
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'junction_id': 'J2', 'question': 'How many vehicles?'},
        )
        self.assertEqual(code, 200)
        self.assertEqual(body['status'], 'CAMERA_UNAVAILABLE')
        self.assertIn('unavailable', body['answer'].lower())

    def test_vqa_with_unpublished_camera_returns_camera_unavailable(self):
        # J3 has no published frame buffer upstream -> must return CAMERA_UNAVAILABLE (never demo image)
        code, body = _post_json(
            f'{QA_BASE}/api/v1/questions/vqa',
            {'junction_id': 'J3', 'question': 'How many vehicles?'},
        )
        self.assertEqual(code, 200)
        self.assertEqual(body['status'], 'CAMERA_UNAVAILABLE')
        self.assertIn('unavailable', body['answer'].lower())


class TestGeminiVQA(unittest.TestCase):
    """End-to-end tests for Gemini VQA integration."""

    def test_gemini_vqa_end_to_end_mocked(self):
        """Verify real image and question produce a model response via gemini_client."""
        import asyncio
        from unittest.mock import patch, MagicMock
        from api.gemini_client import generate_vqa_answer

        # Create a real JPEG image buffer
        try:
            from PIL import Image
            buf = io.BytesIO()
            Image.new('RGB', (64, 64), color=(30, 80, 160)).save(buf, format='JPEG')
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
        except ImportError:
            raise unittest.SkipTest('Pillow not installed')

        mock_gemini_resp = MagicMock()
        mock_gemini_resp.status_code = 200
        mock_gemini_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "The camera frame shows a blue vehicle on the roadway."}
                        ]
                    },
                    "finishReason": "STOP"
                }
            ]
        }

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-gemini-key'}):
            with patch('httpx.AsyncClient.post', return_value=mock_gemini_resp) as mock_post:
                answer, model_name, latency = asyncio.run(
                    generate_vqa_answer(b64, "Describe the vehicle in the frame.")
                )

                self.assertEqual(answer, "The camera frame shows a blue vehicle on the roadway.")
                self.assertTrue(latency >= 0)
                # Verify prompt integrity: ground truth must NOT be sent
                call_args = mock_post.call_args
                payload = call_args.kwargs['json']
                headers = call_args.kwargs['headers']
                self.assertIn('x-goog-api-key', headers)
                self.assertEqual(headers['x-goog-api-key'], 'test-gemini-key')
                user_text = payload['contents'][0]['parts'][1]['text']
                self.assertEqual(user_text, "Describe the vehicle in the frame.")


if __name__ == '__main__':
    unittest.main()

