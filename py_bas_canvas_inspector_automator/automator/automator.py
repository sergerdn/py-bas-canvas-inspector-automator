"""This module provides functionality to automate browser interactions using the Playwright library."""

import asyncio
import json
import os
import random
from typing import Any

import httpx
from mimesis import Gender, Locale, Person
from playwright.async_api import Browser, BrowserContext, Page
from playwright.async_api import Playwright as AsyncPlaywright
from playwright.async_api import async_playwright

from ..utils import get_logger
from .models import WebsocketUrl, WsUrlModel

logger = get_logger()


class BrowserWebSocketConnectionError(Exception):
    """
    Exception raised for errors in the WebSocket connection to the browser's remote debugging port.
    """


class BadProxyIPError(Exception):
    """
    Exception raised when a bad proxy IP is detected, often indicated by the presence of a captcha.
    """


def _url_to_ws_endpoint(endpoint_url: str) -> str:
    """
    Convert an HTTP endpoint URL to a WebSocket endpoint URL.

    :param endpoint_url: The HTTP endpoint URL.
    :return: The WebSocket endpoint URL.
    :raises BrowserWsConnectError: If unable to connect to the HTTP endpoint URL.
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


def new_person() -> Person:
    """
    Create a new person object with random attributes.
    :return: A mimesis Person object with random locale-specific data.
    """
    person = Person(Locale("en"))
    return person


class Automator:  # pylint: disable=too-many-instance-attributes
    """
    Handles the automation of browser interactions.

    This class manages the connection to the browser via WebSocket and provides methods to perform actions.
    """

    ws_endpoint: WsUrlModel
    screenshot_dir_path: str
    timeout: int
    remote_debugging_port: int
    pw: AsyncPlaywright
    browser: Browser
    context: BrowserContext
    page: Page

    def __init__(self, remote_debugging_port: int, screenshot_dir_path: str, timeout: int = 60000) -> None:
        """
        Initialize the Automator class.
        """
        if not os.path.exists(screenshot_dir_path):
            raise ValueError(f"Screenshot directory path {screenshot_dir_path} does not exist.")

        self.screenshot_dir_path = screenshot_dir_path
        self.remote_debugging_port = int(remote_debugging_port)
        self.timeout = int(timeout)

    def get_ws_endpoint(self) -> str:
        """
        Get the WebSocket endpoint URL.
        :return: The WebSocket endpoint URL as a string.
        """
        return self.ws_endpoint.ws_url.unicode_string()

    def connect(self) -> None:
        """
        Connect to the browser via the WebSocket protocol.
        :return: None
        """
        ws_endpoint_url = _url_to_ws_endpoint(f"http://localhost:{self.remote_debugging_port}")
        self.ws_endpoint = WsUrlModel(ws_url=WebsocketUrl(ws_endpoint_url))

    async def __aexit__(self, *args: Any) -> None:
        if self.pw:
            await self.pw.stop()

    async def __aenter__(self) -> "Automator":
        self.connect()
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.connect_over_cdp(self.ws_endpoint.ws_url.unicode_string())
        self.context = self.browser.contexts[0]
        self.page = self.context.pages[0]

        # Fetch the attached sessions
        return self

    async def _grab_canvas_gmail(self) -> bool:  # pylint: disable=too-many-statements
        """
        Automate the process of creating a new Gmail account.

        If Google determines that account creation is not possible, typically due to network-related issues
        such as a flagged proxy IP, the method will raise a BadProxyIPError.

        :return: True if the Gmail account creation process is completed successfully, False otherwise.
        :raises BadProxyIPError: If Google indicates that account creation is not possible, which often suggests
                                 a network-related issue such as a flagged proxy IP.
        """

        logger.debug("Initiating Google account creation automation...")

        # Generate a new person with random attributes
        person = new_person()
        first_name = person.first_name(gender=Gender.MALE)
        last_name = person.last_name(gender=Gender.MALE)
        username = f"{person.username()}_{first_name.lower()}_{last_name.lower()}"
        username = username.replace("_", ".")[:30]
        password = f"{person.password(length=15)}{random.randint(0, 9)}"

        # Define the URL for Gmail account creation
        _url = (
            "https://accounts.google.com/signup/v2/createaccount?biz=false&cc=FI"
            "&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en&theme=glif"
        )

        # Navigate to the Gmail account creation page
        logger.info("Navigating to Gmail account creation page...")
        await self.page.goto(_url, wait_until="networkidle", timeout=self.timeout)

        # Fill in the first and last name fields
        logger.info("Filling in the name fields...")
        await self.page.type("#firstName", first_name)
        await self.page.type("#lastName", last_name)

        # Proceed to the next step of the account creation
        logger.info("Proceeding to the next step...")
        next_button_xpath = "//span[text()='Next']"
        await self.page.click(next_button_xpath)

        # Set the birthdate information
        logger.info("Setting birthdate information...")
        await self.page.select_option("#month", f"{random.randint(1, 12)}")
        await self.page.fill("#day", f"{random.randint(1, 28)}")
        await self.page.fill("#year", f"{random.randint(1970, 1985)}")

        # Select the gender
        logger.info("Selecting gender...")
        await self.page.select_option("#gender", "1")

        # Proceed to the next step of the account creation
        logger.info("Proceeding to the next step...")
        await self.page.click(next_button_xpath)

        await asyncio.sleep(5)

        # Check if there is an option to create a Gmail address
        logger.info("Checking for Gmail address creation option...")
        _xpath = "//div[@id='selectionc2']"
        existing_email_element = await self.page.query_selector(_xpath)
        if existing_email_element:
            logger.info("Gmail address creation option available. Clicking on it...")
            await existing_email_element.click()

        # Fill in the username field
        logger.info("Generating and filling in the username...")

        await self.page.fill('input[name="Username"]', username)

        # Proceed to the next step of the account creation
        logger.info("Proceeding to the next step...")
        await self.page.click(next_button_xpath)

        # Generate a password and fill in the password fields
        logger.info("Filling the password...")

        await self.page.fill('input[name="Passwd"]', password)
        await self.page.fill('input[name="PasswdAgain"]', password)

        # Attempt to finalize the account creation
        logger.info("Attempting to finalize account creation...")
        await self.page.click(next_button_xpath)

        await asyncio.sleep(5)

        # Check for captcha or account creation issues
        logger.info("Checking phone verification...")
        _xpath = "//span[contains(text(), 'Confirm you’re not a robot')]"
        if await self.page.query_selector(_xpath):
            logger.info("Gmail account successfully created.")
            return True

        # Check for specific content that indicates account creation failure
        page_content = await self.page.content()
        if "Sorry, we could not create your Google Account." in page_content:
            logger.error("Account creation failed due to a bad proxy IP.")
            raise BadProxyIPError("Bad IP, restart CanvasInspector with new proxy IP.")

        logger.error("Gmail account creation failed.")
        return False

    async def _grab_canvas_vinted(self) -> bool:  # pylint: disable=too-many-statements
        """
        Automate the process of creating a new Vinted account.

        If a captcha challenge is encountered during the process, it may indicate that the current proxy IP
        has been flagged or is deemed suspicious by Vinted's security measures.
        In this case, the method will raise a BadProxyIPError.

        :return: True if the Vinted account creation process is completed successfully, False otherwise.
        :raises BadProxyIPError: Raised when a captcha challenge is detected, suggesting the possibility of a bad or
                                 flagged proxy IP, which could prevent successful account creation.
        """

        logger.debug("Initiating Vinted account creation automation...")

        # Generate a new person with random attributes
        person = new_person()
        password = f"{person.password(length=15)}{random.randint(0, 9)}"
        first_name = person.first_name(gender=Gender.MALE)
        last_name = person.last_name(gender=Gender.MALE)
        username = f"{person.username()}_{first_name.lower()}_{last_name.lower()}".replace("_", "")[:20]
        email = person.email(domains=["gmail.com"])

        # Attempt to navigate to Vinted's homepage
        logger.info("Navigating to Vinted's homepage...")
        await self.page.goto("https://www.vinted.com/", wait_until="networkidle", timeout=self.timeout)

        await asyncio.sleep(10)

        # Select the United States domain if prompted
        logger.info("Checking for domain selection modal...")
        _xpath = "//div[@data-testid='domain-select-modal']//span[text()='United States']"
        if await self.page.query_selector(_xpath):
            logger.info("Domain selection modal found. Selecting United States...")
            await self.page.click(_xpath)
            await self.page.wait_for_load_state()
            logger.info("Domain selected.")

        await asyncio.sleep(5)

        # Accept cookies if prompted
        logger.info("Checking for cookie acceptance prompt...")
        _xpath = "//div[@id='onetrust-button-group']//button[@id='onetrust-accept-btn-handler']"
        if await self.page.query_selector(_xpath):
            logger.info("Cookie acceptance prompt found. Accepting cookies...")
            await self.page.click(_xpath)
            await self.page.wait_for_load_state()
            logger.info("Cookies accepted.")

        await asyncio.sleep(5)

        # Click on the login button to bring up the registration form
        logger.info("Opening the registration form...")
        await self.page.click("//a[@data-testid='header--login-button']")
        await self.page.click("//span[@data-testid='auth-select-type--register-email']")
        logger.info("Registration form opened.")
        await asyncio.sleep(5)

        # Fill the registration form
        logger.info("Filling in the registration form with pre-generated user data...")
        await self.page.fill("//input[@id='realName']", f"{first_name} {last_name}")
        await self.page.fill("//input[@id='login']", username)
        await self.page.fill("//input[@id='email']", email)
        await self.page.fill("//input[@id='password']", password)
        logger.info("Registration form filled.")

        # Opt-in or out of newsletters and agree to terms
        logger.info("Opting out of newsletters and agreeing to terms...")
        await self.page.evaluate(
            """() => {
            const subscribeXpath = "//div[@class='u-fill-width']//input[@id='subscribeToNewsletter']";
            document.evaluate(subscribeXpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();
            const agreeXpath = "//div[@class='u-fill-width']//input[@id='agreeRules']";
            document.evaluate(agreeXpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();
        }"""  # noqa: E501 pylint: disable=line-too-long
        )
        logger.info("Opt-out and agreement actions performed.")

        # Submit the registration form
        logger.info("Submitting the registration form...")
        await self.page.click("//div[@class='u-fill-width']//button[contains(., 'Continue')]")
        await self.page.wait_for_load_state()
        logger.info("Registration form submitted.")
        await asyncio.sleep(10)

        # Check for captcha challenge
        logger.info("Checking for captcha challenge...")
        prefix_captcha_url = "https://geo.captcha-delivery.com/captcha/?initialCid="
        urls = [frame.url for frame in self.page.frames]
        if any(url.startswith(prefix_captcha_url) for url in urls):
            logger.error("Captcha detected, potentially due to a bad proxy IP.")
            raise BadProxyIPError("Captcha detected, restart CanvasInspector with new proxy IP.")

        # Request verification code
        logger.info("Requesting email verification code...")
        await self.page.click("//button[contains(., 'Get my verification code')]")
        await self.page.wait_for_load_state(timeout=self.timeout)
        logger.info("Verification email code requested.")
        await asyncio.sleep(10)

        return True

    async def _clean_up(self) -> None:
        """
        Clean up the browser.
        :return: None
        """
        await self.context.clear_cookies()
        await self.page.goto("https://www.google.com/?hl=en", wait_until="networkidle")

    async def _save_screenshot(self, screenshot_name: str) -> None:
        """
        Save a screenshot of the current page.
        :param screenshot_name: The name of the screenshot.
        :return: None
        """
        filename = f"{screenshot_name}.png"
        await self.page.screenshot(path=os.path.join(self.screenshot_dir_path, filename), full_page=True)

    async def grab_canvas(self) -> bool:
        """
        Perform the sequence of actions to grab the canvas for multiple resources.
        :return: True if the canvas was successfully grabbed, False otherwise.
        """
        await self._clean_up()
        await self._grab_canvas_gmail()
        await self._save_screenshot("gmail")

        await self._clean_up()
        await self._grab_canvas_vinted()
        await self._save_screenshot("vinted")

        return True
