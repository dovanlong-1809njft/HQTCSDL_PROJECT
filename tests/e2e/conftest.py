"""Shared browser and Vite lifecycle for mocked UI checks and real login E2E."""
from contextlib import contextmanager
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest

playwright = pytest.importorskip("playwright.sync_api")
WEB = Path(__file__).resolve().parents[2] / "apps" / "web"


@pytest.fixture(scope="session")
def e2e_browser():
    if os.getenv("RUN_TASK7_UI") != "1" and os.getenv("RUN_TASK9_E2E") != "1":
        pytest.skip("Set RUN_TASK7_UI=1 or RUN_TASK9_E2E=1 to run browser checks.")
    with playwright.sync_playwright() as engine:
        browser = engine.chromium.launch(channel="msedge" if sys.platform == "win32" else None)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(scope="session")
def vite_server():
    @contextmanager
    def start(proxy_target="http://127.0.0.1:1"):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        # Keep tests off the developer's backend and disable demo authentication.
        env.update(VITE_API_URL="/api", VITE_PROXY_TARGET=proxy_target, VITE_ENABLE_MOCK_AUTH="false")
        server = subprocess.Popen(
            ["node", str(WEB / "node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--port", str(port), "--strictPort"],
            cwd=WEB, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                if server.poll() is not None:
                    pytest.fail("Vite stopped. Check npm install and npm run build in apps/web.")
                try:
                    with urlopen(url, timeout=1):
                        break
                except (URLError, TimeoutError):
                    if time.monotonic() > deadline:
                        pytest.fail("Vite did not start within 30 seconds.")
                    time.sleep(0.1)
            yield url
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    return start
