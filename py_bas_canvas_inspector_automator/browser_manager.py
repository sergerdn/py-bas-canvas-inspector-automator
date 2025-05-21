"""This module provides functionality to manage browser connections via WebSocket."""

import json
import os
import shutil
import tempfile
from typing import Any, Dict

import httpx
from playwright.async_api import Browser, BrowserContext, Page
from playwright.async_api import Playwright as AsyncPlaywright
from playwright.async_api import async_playwright

from py_bas_canvas_inspector_automator.automator.models import WebsocketUrl, WsUrlModel
from py_bas_canvas_inspector_automator.config import get_config
from py_bas_canvas_inspector_automator.utils import get_logger

logger = get_logger()


class BrowserWebSocketConnectionError(Exception):
    """Exception raised for errors in the WebSocket connection to the browser's remote
    debugging port."""


def _url_to_ws_endpoint(endpoint_url: str) -> str:
    """Convert an HTTP endpoint URL to a WebSocket endpoint URL.

    Args:
        endpoint_url: The HTTP endpoint URL.

    Returns:
        The WebSocket endpoint URL.

    Raises:
        BrowserWsConnectError: If unable to connect to the HTTP endpoint URL.
    """

    if endpoint_url.startswith("ws"):
        return endpoint_url

    logger.debug("Preparing WebSocket: retrieving WebSocket URL from %s", endpoint_url)

    http_url = endpoint_url if endpoint_url.endswith("/") else f"{endpoint_url}/"
    http_url += "json/version/"
    try:
        response = httpx.get(http_url)
    except httpx.ConnectError as exc:
        raise BrowserWebSocketConnectionError(
            f"Cannot connect to {http_url}. This may not be a DevTools server. Consider connecting via ws://."
        ) from exc

    if response.status_code != 200:
        raise ValueError(
            f"Unexpected status {response.status_code} when connecting to {http_url}. "
            "This might not be a DevTools server. Consider connecting via ws://."
        )

    json_data = json.loads(response.text)
    logger.debug("WebSocket preparation response: %s", json_data)

    return str(json_data["webSocketDebuggerUrl"])


class BrowserManager:
    """Manages browser connections via WebSocket and provides methods for browser
    operations.

    This class handles connecting to a browser via WebSocket, taking screenshots, and
    cleaning up the browser state.
    """

    ws_endpoint: WsUrlModel
    screenshot_dir_path: str
    screenshot_dir_path_temp: str
    timeout: int
    remote_debugging_port: int
    pw: AsyncPlaywright
    browser: Browser
    context: BrowserContext
    page: Page
    browser_info: Dict
    config: Dict

    def __init__(
        self,
        remote_debugging_port: int,
        screenshot_dir_path: str,
        timeout: int = 60000,
        config_path: str = "docconvert_config.json",
    ) -> None:
        """Initialize the BrowserManager class."""
        if not os.path.exists(screenshot_dir_path):
            raise ValueError(f"Screenshot directory path {screenshot_dir_path} does not exist.")

        self.screenshot_dir_path = screenshot_dir_path
        self.remote_debugging_port = int(remote_debugging_port)
        self.timeout = int(timeout)
        self.config = get_config(config_path)

        self.screenshot_dir_path_temp = os.path.join(
            tempfile.gettempdir(), "py-bas-canvas-inspector-automator", "screenshots"
        )

        if os.path.exists(self.screenshot_dir_path_temp):
            shutil.rmtree(self.screenshot_dir_path_temp, ignore_errors=True)

        os.makedirs(self.screenshot_dir_path_temp)

    def get_ws_endpoint(self) -> str:
        """Get the WebSocket endpoint URL.

        Returns:
            The WebSocket endpoint URL as a string.
        """
        return self.ws_endpoint.ws_url.unicode_string()

    def connect(self) -> None:
        """Connect to the browser via the WebSocket protocol.

        Returns:
            None
        """
        ws_endpoint_url = _url_to_ws_endpoint(f"http://localhost:{self.remote_debugging_port}")
        self.ws_endpoint = WsUrlModel(ws_url=WebsocketUrl(ws_endpoint_url))

    async def __aexit__(self, *args: Any) -> None:
        if self.pw:
            await self.pw.stop()

    async def __aenter__(self) -> "BrowserManager":
        self.connect()
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(self.ws_endpoint.ws_url.unicode_string())
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

        # Fetch the attached sessions
        return self

    async def _clean_up(self) -> None:
        """Clean up the browser.

        Returns:
            None
        """
        await self.context.clear_cookies()
        await self.page.goto("https://www.google.com/?hl=en", wait_until="networkidle", timeout=self.timeout)
