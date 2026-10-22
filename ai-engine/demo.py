#!/usr/bin/env python3
"""
MediChain AI Engine -- Demo / Integration Test Script
======================================================

Starts the FastAPI server in SIMULATION_MODE, waits for it to become healthy,
then exercises every API endpoint with sample data and prints a colour-coded
summary of results.

Usage:
    python demo.py              # Start server automatically, run all tests
    python demo.py --no-server  # Assume server is already running on port 8000

Requirements (already in requirements.txt):
    httpx, Pillow
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ---------------------------------------------------------------------------
#  Terminal colours
# ---------------------------------------------------------------------------

class C:
    """ANSI colour codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def ok(msg: str) -> str:
    return f"{C.GREEN}[PASS]{C.RESET} {msg}"


def fail(msg: str) -> str:
    return f"{C.RED}[FAIL]{C.RESET} {msg}"


def skip(msg: str) -> str:
    return f"{C.YELLOW}[SKIP]{C.RESET} {msg}"


def header(msg: str) -> str:
    return f"\n{C.BOLD}{C.CYAN}{'=' * 64}\n  {msg}\n{'=' * 64}{C.RESET}"


def subheader(msg: str) -> str:
    return f"\n{C.BOLD}--- {msg} ---{C.RESET}"


# ---------------------------------------------------------------------------
#  Globals
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000"
RESULTS: List[Tuple[str, str]] = []   # (test_name, "pass" | "fail" | "skip")


def record(name: str, status: str, detail: str = "") -> None:
    """Record a test result and print it immediately."""
    RESULTS.append((name, status))
    if status == "pass":
        print(ok(f"{name}  {C.DIM}{detail}{C.RESET}"))
    elif status == "fail":
        print(fail(f"{name}  {C.DIM}{detail}{C.RESET}"))
    else:
        print(skip(f"{name}  {C.DIM}{detail}{C.RESET}"))


# ---------------------------------------------------------------------------
#  Generate a small test PNG image using Pillow
# ---------------------------------------------------------------------------

def generate_test_pill_image() -> bytes:
    """Create a small synthetic pill image (64x64 white circle on blue bg)."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (64, 64), color=(30, 60, 120))
    draw = ImageDraw.Draw(img)
    # Draw a white ellipse to simulate a pill shape.
    draw.ellipse([12, 20, 52, 44], fill=(245, 245, 245), outline=(200, 200, 200))
    # Add a score line across the pill.
    draw.line([(32, 20), (32, 44)], fill=(180, 180, 180), width=1)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
#  Wait for server health
# ---------------------------------------------------------------------------

async def wait_for_health(client: httpx.AsyncClient, timeout: float = 60.0) -> bool:
    """Poll /api/health until the server responds with status 'ok'."""
    print(f"\n{C.DIM}Waiting for server to become healthy (timeout={timeout}s)...{C.RESET}")
    start = time.monotonic()
    while (time.monotonic() - start) < timeout:
        try:
            resp = await client.get(f"{BASE_URL}/api/health", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "ok":
                    elapsed = time.monotonic() - start
                    print(f"{C.GREEN}Server healthy after {elapsed:.1f}s{C.RESET}")
                    return True
        except (httpx.ConnectError, httpx.ReadError, httpx.ConnectTimeout):
            pass
        await asyncio.sleep(1.0)
    return False


# ---------------------------------------------------------------------------
#  Individual test functions
# ---------------------------------------------------------------------------

async def test_health(client: httpx.AsyncClient) -> None:
    """GET /api/health"""
    name = "GET /api/health"
    try:
        resp = await client.get(f"{BASE_URL}/api/health")
        data = resp.json()
        if resp.status_code == 200 and data.get("status") == "ok":
            models = data.get("models_loaded", {})
            loaded = sum(1 for v in models.values() if v)
            record(name, "pass", f"status=ok  models_loaded={loaded}/{len(models)}  simulation={data.get('simulation_mode')}")
        else:
            record(name, "fail", f"status_code={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_verify_image(client: httpx.AsyncClient) -> None:
    """POST /api/verify-image with a dummy pill PNG."""
    name = "POST /api/verify-image"
    try:
        image_bytes = generate_test_pill_image()
        files = {"file": ("test_pill.png", image_bytes, "image/png")}
        resp = await client.post(f"{BASE_URL}/api/verify-image", files=files, timeout=30.0)
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"prediction={data.get('prediction')}  confidence={data.get('confidence'):.3f}  "
                f"hash={data.get('embedding_hash', '')[:16]}...  time={data.get('processing_time_ms'):.1f}ms"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Model not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_detect_anomaly_normal(client: httpx.AsyncClient) -> None:
    """POST /api/detect-anomaly with a normal transaction."""
    name = "POST /api/detect-anomaly (normal)"
    payload = {
        "transfer_velocity_kmh": 60.0,
        "time_since_last_transfer_hours": 24.0,
        "transfer_count": 2.0,
        "scan_frequency_24h": 1.0,
        "unique_devices_24h": 1.0,
        "path_deviation_score": 0.0,
        "geographic_consistency": 1.0,
        "hour_of_day": 14,
        "is_weekend": 0,
        "days_since_manufacture": 30.0,
        "batch_anomaly_rate": 0.0,
        "actor_reputation_score": 800.0,
        "medicine_id": 1,
        "transaction_id": "demo-normal-001",
    }
    try:
        resp = await client.post(f"{BASE_URL}/api/detect-anomaly", json=payload, timeout=15.0)
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"is_anomaly={data.get('is_anomaly')}  score={data.get('anomaly_score'):.3f}  "
                f"severity={data.get('recommended_severity')}  reasons={data.get('anomaly_reasons')}"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Detector not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_detect_anomaly_suspicious(client: httpx.AsyncClient) -> None:
    """POST /api/detect-anomaly with a suspicious high-velocity transaction."""
    name = "POST /api/detect-anomaly (anomalous)"
    payload = {
        "transfer_velocity_kmh": 1200.0,      # Impossibly fast
        "time_since_last_transfer_hours": 0.5, # Very recent
        "transfer_count": 12.0,                # Too many transfers
        "scan_frequency_24h": 15.0,            # Excessive scanning
        "unique_devices_24h": 8.0,             # Many devices
        "path_deviation_score": 0.9,           # Far off expected path
        "geographic_consistency": 0.1,         # Poor geographic consistency
        "hour_of_day": 3,                      # Suspicious early morning
        "is_weekend": 1,                       # Weekend
        "days_since_manufacture": 5.0,         # Very new
        "batch_anomaly_rate": 0.25,            # High batch anomaly rate
        "actor_reputation_score": 150.0,       # Low reputation
        "medicine_id": 2,
        "transaction_id": "demo-anomaly-001",
    }
    try:
        resp = await client.post(f"{BASE_URL}/api/detect-anomaly", json=payload, timeout=15.0)
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"is_anomaly={data.get('is_anomaly')}  score={data.get('anomaly_score'):.3f}  "
                f"severity={data.get('recommended_severity')}  reasons={data.get('anomaly_reasons')}"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Detector not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_detect_anomaly_batch(client: httpx.AsyncClient) -> None:
    """POST /api/detect-anomaly-batch with 5 mixed transactions."""
    name = "POST /api/detect-anomaly-batch (5 txns)"

    transactions = [
        # 1. Normal
        {
            "transfer_velocity_kmh": 50.0,
            "time_since_last_transfer_hours": 48.0,
            "transfer_count": 1.0,
            "scan_frequency_24h": 1.0,
            "unique_devices_24h": 1.0,
            "path_deviation_score": 0.0,
            "geographic_consistency": 1.0,
            "hour_of_day": 10,
            "is_weekend": 0,
            "days_since_manufacture": 60.0,
            "batch_anomaly_rate": 0.0,
            "actor_reputation_score": 900.0,
            "transaction_id": "batch-1",
        },
        # 2. Normal
        {
            "transfer_velocity_kmh": 80.0,
            "time_since_last_transfer_hours": 12.0,
            "transfer_count": 3.0,
            "scan_frequency_24h": 2.0,
            "unique_devices_24h": 2.0,
            "path_deviation_score": 0.0,
            "geographic_consistency": 0.9,
            "hour_of_day": 15,
            "is_weekend": 0,
            "days_since_manufacture": 45.0,
            "batch_anomaly_rate": 0.01,
            "actor_reputation_score": 700.0,
            "transaction_id": "batch-2",
        },
        # 3. Suspicious -- high velocity + path deviation
        {
            "transfer_velocity_kmh": 800.0,
            "time_since_last_transfer_hours": 1.0,
            "transfer_count": 7.0,
            "scan_frequency_24h": 5.0,
            "unique_devices_24h": 4.0,
            "path_deviation_score": 0.7,
            "geographic_consistency": 0.3,
            "hour_of_day": 2,
            "is_weekend": 1,
            "days_since_manufacture": 10.0,
            "batch_anomaly_rate": 0.15,
            "actor_reputation_score": 250.0,
            "transaction_id": "batch-3",
        },
        # 4. Normal-ish
        {
            "transfer_velocity_kmh": 120.0,
            "time_since_last_transfer_hours": 6.0,
            "transfer_count": 2.0,
            "scan_frequency_24h": 3.0,
            "unique_devices_24h": 1.0,
            "path_deviation_score": 0.0,
            "geographic_consistency": 0.8,
            "hour_of_day": 9,
            "is_weekend": 0,
            "days_since_manufacture": 90.0,
            "batch_anomaly_rate": 0.02,
            "actor_reputation_score": 650.0,
            "transaction_id": "batch-4",
        },
        # 5. Very suspicious
        {
            "transfer_velocity_kmh": 1500.0,
            "time_since_last_transfer_hours": 0.2,
            "transfer_count": 15.0,
            "scan_frequency_24h": 20.0,
            "unique_devices_24h": 10.0,
            "path_deviation_score": 1.0,
            "geographic_consistency": 0.0,
            "hour_of_day": 4,
            "is_weekend": 1,
            "days_since_manufacture": 2.0,
            "batch_anomaly_rate": 0.5,
            "actor_reputation_score": 100.0,
            "transaction_id": "batch-5",
        },
    ]

    payload = {"transactions": transactions}
    try:
        resp = await client.post(
            f"{BASE_URL}/api/detect-anomaly-batch", json=payload, timeout=30.0
        )
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("summary", {})
            record(
                name, "pass",
                f"total={summary.get('total')}  anomalies={summary.get('anomaly_count')}  "
                f"rate={summary.get('anomaly_rate')}  avg_score={summary.get('avg_anomaly_score'):.3f}  "
                f"time={data.get('processing_time_ms'):.1f}ms"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Detector not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_heatmap_data(client: httpx.AsyncClient) -> None:
    """GET /api/heatmap-data"""
    name = "GET /api/heatmap-data"
    try:
        resp = await client.get(f"{BASE_URL}/api/heatmap-data", timeout=15.0)
        if resp.status_code == 200:
            data = resp.json()
            pts = len(data.get("heatmap_points", []))
            clusters = len(data.get("clusters", []))
            hotspots = len(data.get("predicted_hotspots", []))
            record(
                name, "pass",
                f"points={pts}  clusters={clusters}  predicted_hotspots={hotspots}  "
                f"time={data.get('processing_time_ms'):.1f}ms"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Engine not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_heatmap_zone_risk(client: httpx.AsyncClient) -> None:
    """GET /api/heatmap-zone-risk?lat=17.385&lng=78.4867 (Hyderabad)"""
    name = "GET /api/heatmap-zone-risk (Hyderabad)"
    try:
        resp = await client.get(
            f"{BASE_URL}/api/heatmap-zone-risk",
            params={"lat": 17.385, "lng": 78.4867},
            timeout=15.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"risk_level={data.get('risk_level')}  distance_km={data.get('distance_km')}  "
                f"nearest_cluster={bool(data.get('nearest_cluster'))}"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Engine not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_adverse_events(client: httpx.AsyncClient) -> None:
    """GET /api/adverse-events/aspirin"""
    name = "GET /api/adverse-events/aspirin"
    try:
        resp = await client.get(
            f"{BASE_URL}/api/adverse-events/aspirin",
            timeout=30.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"total_reports={data.get('total_reports')}  recent_30d={data.get('recent_reports_30d')}  "
                f"risk_score={data.get('counterfeit_risk_score'):.3f}  "
                f"alerts={len(data.get('signal_alerts', []))}  "
                f"time={data.get('processing_time_ms'):.1f}ms"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Monitor not loaded')}")
        elif resp.status_code == 502:
            record(name, "skip", f"502: OpenFDA API unreachable -- {resp.json().get('detail', '')[:100]}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_risk_score(client: httpx.AsyncClient) -> None:
    """POST /api/risk-score with a full composite request."""
    name = "POST /api/risk-score"
    payload = {
        "medicine_id": 42,
        "drug_name": "aspirin",
        "location": {"lat": 17.385, "lng": 78.4867},
        "transaction_data": {
            "transfer_velocity_kmh": 100.0,
            "time_since_last_transfer_hours": 12.0,
            "transfer_count": 3.0,
            "scan_frequency_24h": 2.0,
            "unique_devices_24h": 1.0,
            "path_deviation_score": 0.0,
            "geographic_consistency": 0.9,
            "hour_of_day": 14,
            "is_weekend": 0,
            "days_since_manufacture": 45.0,
            "batch_anomaly_rate": 0.02,
            "actor_reputation_score": 700.0,
        },
        "actor_reputation": 0.7,
        "shortage_flag": False,
        "recall_flag": False,
        "auto_flag": False,
    }
    try:
        resp = await client.post(f"{BASE_URL}/api/risk-score", json=payload, timeout=30.0)
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"trust_score={data.get('trust_score')}  risk_level={data.get('risk_level')}  "
                f"flag_severity={data.get('flag_severity')}  auto_flag={data.get('auto_flag')}  "
                f"time={data.get('processing_time_ms'):.1f}ms"
            )
        elif resp.status_code == 503:
            record(name, "skip", f"503: {resp.json().get('detail', 'Scorer not loaded')}")
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_dashboard_stats(client: httpx.AsyncClient) -> None:
    """GET /api/dashboard-stats"""
    name = "GET /api/dashboard-stats"
    try:
        resp = await client.get(f"{BASE_URL}/api/dashboard-stats", timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            record(
                name, "pass",
                f"scans={data.get('total_scans')}  flags={data.get('total_flags')}  "
                f"verifications={data.get('total_verifications')}  anomaly_checks={data.get('total_anomaly_checks')}  "
                f"avg_trust={data.get('avg_trust_score')}  hotspots={data.get('active_hotspots')}  "
                f"ws_clients={data.get('websocket_clients')}"
            )
        else:
            record(name, "fail", f"status={resp.status_code}  body={resp.text[:200]}")
    except Exception as exc:
        record(name, "fail", str(exc))


async def test_websocket_alerts() -> None:
    """Connect to ws://localhost:8000/api/ws/alerts for ~2 seconds."""
    name = "WS /api/ws/alerts"
    try:
        import websockets  # type: ignore
        ws_available = True
    except ImportError:
        ws_available = False

    if not ws_available:
        # Fall back to httpx websocket support if websockets is not installed.
        # httpx does not have native websocket support, so we try the websockets lib
        # or mark as skipped.
        try:
            # Try using httpx-ws or similar
            import httpx_ws  # type: ignore
            ws_available = True
        except ImportError:
            pass

    if not ws_available:
        # Last resort: try raw socket approach or just skip
        record(name, "skip", "Neither 'websockets' nor 'httpx-ws' package available")
        return

    try:
        import websockets

        messages_received: List[Dict[str, Any]] = []
        uri = "ws://localhost:8000/api/ws/alerts"

        async with websockets.connect(uri) as ws:
            # We should receive a welcome message immediately.
            try:
                # Gather messages for 2 seconds.
                end_time = time.monotonic() + 2.0
                while time.monotonic() < end_time:
                    remaining = end_time - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                        msg = json.loads(raw) if isinstance(raw, str) else raw
                        messages_received.append(msg)
                    except asyncio.TimeoutError:
                        break

                # Send a ping to verify two-way communication.
                await ws.send(json.dumps({"type": "ping"}))
                try:
                    pong = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    pong_data = json.loads(pong) if isinstance(pong, str) else pong
                    messages_received.append(pong_data)
                except asyncio.TimeoutError:
                    pass

            except Exception as inner_exc:
                record(name, "fail", f"Error during WS communication: {inner_exc}")
                return

        # Analyse what we received.
        types = [m.get("type", "?") for m in messages_received]
        record(
            name, "pass",
            f"received {len(messages_received)} messages  types={types}"
        )

    except Exception as exc:
        # Connection refused or other error -- if server is up this might mean
        # websocket route is different.
        record(name, "fail", f"{type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
#  Main orchestrator
# ---------------------------------------------------------------------------

async def run_all_tests() -> None:
    """Run every test in sequence, collecting results."""
    async with httpx.AsyncClient() as client:
        print(header("1. Health Check"))
        await test_health(client)

        print(header("2. Pill Image Verification"))
        await test_verify_image(client)

        print(header("3. Anomaly Detection (Single)"))
        await test_detect_anomaly_normal(client)
        await test_detect_anomaly_suspicious(client)

        print(header("4. Anomaly Detection (Batch)"))
        await test_detect_anomaly_batch(client)

        print(header("5. Geographic Heatmap"))
        await test_heatmap_data(client)
        await test_heatmap_zone_risk(client)

        print(header("6. Adverse Event Monitoring"))
        await test_adverse_events(client)

        print(header("7. Composite Risk Score"))
        await test_risk_score(client)

        print(header("8. Dashboard Statistics"))
        await test_dashboard_stats(client)

    print(header("9. WebSocket Alerts"))
    await test_websocket_alerts()


def print_summary() -> None:
    """Print a final colour-coded summary of all test results."""
    passed = sum(1 for _, s in RESULTS if s == "pass")
    failed = sum(1 for _, s in RESULTS if s == "fail")
    skipped = sum(1 for _, s in RESULTS if s == "skip")
    total = len(RESULTS)

    print(header("SUMMARY"))
    print(f"  Total:   {total}")
    print(f"  {C.GREEN}Passed:  {passed}{C.RESET}")
    print(f"  {C.RED}Failed:  {failed}{C.RESET}")
    print(f"  {C.YELLOW}Skipped: {skipped}{C.RESET}")
    print()

    if failed > 0:
        print(f"{C.RED}{C.BOLD}Some tests failed:{C.RESET}")
        for name, status in RESULTS:
            if status == "fail":
                print(f"  {C.RED}- {name}{C.RESET}")
        print()

    if failed == 0 and skipped == 0:
        print(f"{C.GREEN}{C.BOLD}All tests passed!{C.RESET}\n")
    elif failed == 0:
        print(f"{C.GREEN}{C.BOLD}All non-skipped tests passed!{C.RESET}\n")


# ---------------------------------------------------------------------------
#  Server management
# ---------------------------------------------------------------------------

def start_server() -> subprocess.Popen:
    """Start the FastAPI server as a subprocess with SIMULATION_MODE=true."""
    env = os.environ.copy()
    env["SIMULATION_MODE"] = "true"

    ai_engine_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"{C.CYAN}Starting MediChain AI Engine server (SIMULATION_MODE=true)...{C.RESET}")
    print(f"{C.DIM}Working directory: {ai_engine_dir}{C.RESET}")

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ai_engine_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        # Put server output in a background reader so it does not block.
        bufsize=1,
        universal_newlines=True,
    )

    # Start a background thread to drain server output so the pipe does not fill up.
    import threading

    def _drain(proc: subprocess.Popen) -> None:
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                # Optionally print server logs with a prefix for debugging.
                # Uncomment the next line to see server output:
                # print(f"{C.DIM}  [server] {line.rstrip()}{C.RESET}")
                pass
        except Exception:
            pass

    t = threading.Thread(target=_drain, args=(proc,), daemon=True)
    t.start()

    return proc


def stop_server(proc: subprocess.Popen) -> None:
    """Gracefully stop the server subprocess."""
    print(f"\n{C.CYAN}Stopping server (pid={proc.pid})...{C.RESET}")
    try:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print(f"{C.YELLOW}Server did not stop in time; sending SIGKILL...{C.RESET}")
            proc.kill()
            proc.wait(timeout=5)
        print(f"{C.GREEN}Server stopped.{C.RESET}")
    except Exception as exc:
        print(f"{C.RED}Error stopping server: {exc}{C.RESET}")


# ---------------------------------------------------------------------------
#  CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MediChain AI Engine -- Demo & Integration Tests",
    )
    parser.add_argument(
        "--no-server",
        action="store_true",
        help="Skip starting the server (assumes it is already running on port 8000)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the AI engine (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url.rstrip("/")

    server_proc: Optional[subprocess.Popen] = None

    print(f"\n{C.BOLD}{C.CYAN}")
    print("  __  __          _ _  ____ _           _        ")
    print(" |  \\/  | ___  __| (_)/ ___| |__   __ _(_)_ __   ")
    print(" | |\\/| |/ _ \\/ _` | | |   | '_ \\ / _` | | '_ \\  ")
    print(" | |  | |  __/ (_| | | |___| | | | (_| | | | | | ")
    print(" |_|  |_|\\___|\\__,_|_|\\____|_| |_|\\__,_|_|_| |_| ")
    print(f"          AI Engine Demo & Integration Tests       {C.RESET}")
    print()

    try:
        # -- Start server if needed ----------------------------------------- #
        if not args.no_server:
            server_proc = start_server()
        else:
            print(f"{C.YELLOW}--no-server: assuming server is already running at {BASE_URL}{C.RESET}")

        # -- Wait for health ------------------------------------------------ #
        healthy = asyncio.run(_wait_and_run(server_proc))

        if not healthy:
            print(f"\n{C.RED}{C.BOLD}Server did not become healthy within timeout. Aborting.{C.RESET}")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}Interrupted by user.{C.RESET}")
    finally:
        # -- Print summary -------------------------------------------------- #
        if RESULTS:
            print_summary()

        # -- Stop server ---------------------------------------------------- #
        if server_proc is not None:
            stop_server(server_proc)


async def _wait_and_run(server_proc: Optional[subprocess.Popen]) -> bool:
    """Wait for the server and then run all tests."""
    async with httpx.AsyncClient() as client:
        healthy = await wait_for_health(client, timeout=90.0)

    if not healthy:
        return False

    # Check that server process has not crashed (if we started it).
    if server_proc is not None and server_proc.poll() is not None:
        print(f"{C.RED}Server process exited with code {server_proc.returncode}{C.RESET}")
        return False

    await run_all_tests()
    return True


if __name__ == "__main__":
    main()
