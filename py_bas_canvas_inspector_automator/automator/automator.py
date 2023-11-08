"""This module provides functionality to automate browser interactions using the Playwright library."""

import asyncio
import json
import os
import random
import shutil
import tempfile
from typing import Any, Dict

import httpx
from mimesis import Gender, Locale, Person
from playwright.async_api import Browser, BrowserContext, Page
from playwright.async_api import Playwright as AsyncPlaywright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from py_bas_canvas_inspector_automator.automator.models import WebsocketUrl, WsUrlModel
from py_bas_canvas_inspector_automator.ocr import ocr_image
from py_bas_canvas_inspector_automator.utils import get_logger

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
    screenshot_dir_path_temp: str
    timeout: int
    remote_debugging_port: int
    pw: AsyncPlaywright
    browser: Browser
    context: BrowserContext
    page: Page
    browser_info: Dict

    def __init__(self, remote_debugging_port: int, screenshot_dir_path: str, timeout: int = 60000) -> None:
        """
        Initialize the Automator class.
        """
        if not os.path.exists(screenshot_dir_path):
            raise ValueError(f"Screenshot directory path {screenshot_dir_path} does not exist.")

        self.screenshot_dir_path = screenshot_dir_path
        self.remote_debugging_port = int(remote_debugging_port)
        self.timeout = int(timeout)

        self.screenshot_dir_path_temp = os.path.join(
            tempfile.gettempdir(), "py-bas-canvas-inspector-automator", "screenshots"
        )

        if os.path.exists(self.screenshot_dir_path_temp):
            shutil.rmtree(self.screenshot_dir_path_temp, ignore_errors=True)

        os.makedirs(self.screenshot_dir_path_temp)

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

    async def _clean_up(self) -> None:
        """
        Clean up the browser.
        :return: None
        """
        await self.context.clear_cookies()
        await self.page.goto("https://www.google.com/?hl=en", wait_until="networkidle", timeout=self.timeout)

    async def _check_prerequisites(self) -> None:
        logger.info("Checking browser info...")
        await self.page.goto("https://lumtest.com/echo.json", wait_until="networkidle", timeout=self.timeout)
        page_source = await self.page.evaluate("document.documentElement.innerText")
        self.browser_info = json.loads(page_source)
        print(json.dumps(self.browser_info, indent=4))
        logger.info("Browser info: %s", self.browser_info)

        # logger.info("Checking IP2Location...")
        # await self.page.goto("https://www.ip2location.com/demo/", wait_until="networkidle", timeout=self.timeout)

    async def _save_screenshot(self, screenshot_name: str) -> None:
        """
        Save a screenshot of the current page.
        :param screenshot_name: The name of the screenshot.
        :return: None
        """
        filename = f"{screenshot_name}.png"
        await self.page.screenshot(path=os.path.join(self.screenshot_dir_path, filename), full_page=True)

    async def _save_temp_screenshot(self, screenshot_name: str) -> str:
        filename = os.path.join(self.screenshot_dir_path_temp, f"{screenshot_name}.png")
        await self.page.screenshot(path=filename, full_page=True)
        return filename

    async def _grab_canvas_gmail(self) -> bool:  # pylint: disable=too-many-statements
        """
        Automate the process of creating a new Gmail account.

        :return: True if the Gmail account creation process is completed successfully, False otherwise.
        :raises BadProxyIPError: If Google indicates that account creation is not possible, which often suggests
                                 a network-related issue such as a flagged proxy IP.
        """

        logger.info("Initiating Google account creation automation...")

        # Generate a new person with random attributes
        person = new_person()
        first_name = person.first_name(gender=Gender.MALE)
        last_name = person.last_name(gender=Gender.MALE)
        username = f"{person.username()}_{first_name.lower()}_{last_name.lower()}"
        username = username.replace("_", ".")[:30]
        password = f"{person.password(length=15)}{random.randint(0, 9)}"

        # Define the URL for Gmail account creation
        url = (
            "https://accounts.google.com/signup/v2/createaccount?biz=false&cc=FI"
            "&flowEntry=SignUp&flowName=GlifWebSignIn&hl=en&theme=glif"
        )

        # Navigate to the Gmail account creation page
        logger.info("Navigating to Gmail account creation page...")
        await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)

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
            logger.warning("Account creation failed due to a bad proxy IP.")
            raise BadProxyIPError("Bad IP, restart CanvasInspector with new proxy IP.")

        logger.warning("Gmail account creation failed.")
        return False

    async def _grab_canvas_vinted(self) -> bool:  # pylint: disable=too-many-statements
        """
        Automate the process of creating a new Vinted account.

        :return: True if the Vinted account creation process is completed successfully, False otherwise.
        :raises BadProxyIPError: Raised when a captcha challenge is detected. it may indicate that the current proxy IP
                                 has been flagged or is deemed suspicious by Vinted's security measures.

        """

        logger.info("Initiating Vinted account creation automation...")

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
            await self.page.wait_for_load_state(timeout=self.timeout)
            logger.info("Domain selected.")

        await asyncio.sleep(5)

        # Accept cookies if prompted
        logger.info("Checking for cookie acceptance prompt...")
        _xpath = "//div[@id='onetrust-button-group']//button[@id='onetrust-accept-btn-handler']"
        if await self.page.query_selector(_xpath):
            logger.info("Cookie acceptance prompt found. Accepting cookies...")
            await self.page.click(_xpath)
            await self.page.wait_for_load_state(timeout=self.timeout)
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
        await self.page.wait_for_load_state(timeout=self.timeout)
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

    async def _grab_canvas_outlook(self) -> bool:  # pylint: disable=too-many-statements
        """
        Automates the process of creating a new Outlook account.

        :return: True if the Outlook account creation process is completed successfully, False otherwise.
        """
        logger.info("Initiating Outlook account creation automation...")

        # Generate a new person with random attributes using a helper function
        person = new_person()
        first_name = person.first_name(gender=Gender.MALE)
        last_name = person.last_name(gender=Gender.MALE)
        username = f"{person.username()}_{first_name.lower()}_{last_name.lower()}".replace("_", ".")[:30]
        password = f"{person.password(length=15)}{random.randint(0, 9)}"

        # Define the URL for Outlook main page
        url = "https://www.microsoft.com/en-us/microsoft-365/outlook/email-and-calendar-software-microsoft-outlook"

        # Navigate to the Outlook account creation page
        logger.info("Navigating to Outlook main page...")
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
        except PlaywrightTimeoutError as exc:
            logger.warning("Timeout error encountered: %s", exc)

        # Click the 'Accept' button to accept cookies and proceed
        logger.info("Looking for the 'Accept' button to handle cookies...")
        accept_button_xpath = "//button[contains(@style, 'overflow-x: visible;') and text()='Accept']"
        accept_button = await self.page.query_selector(accept_button_xpath)
        if accept_button:
            await accept_button.click()
            logger.info("Clicked the 'Accept' button.")
        else:
            logger.info("The 'Accept' button was not found. Proceeding without clicking it.")

        # Proceed to the Sign-in page
        logger.info("Proceeding to the English Sign-up page...")
        await self.page.goto(
            "https://signup.live.com/signup?lic=1&mkt=en-US", wait_until="networkidle", timeout=self.timeout
        )
        logger.info("English Sign-up page loaded.")

        logger.info("Click on 'Create one' button...")
        await self.page.click("//a[@id='liveSwitch' and contains(text(), 'Get a new email address')]")
        await self.page.wait_for_load_state(timeout=self.timeout)
        logger.info("Clicked on 'Create one' button.")

        logger.info("Filling in the registration form with username...")
        await self.page.fill("//input[@id='MemberName']", username)
        await self.page.click("//input[@type='submit' and @value='Next']")
        logger.info("Filled in the registration form with username.")

        logger.info("Filling in the registration form with password...")
        await self.page.fill("//input[@id='PasswordInput']", password)
        await self.page.click("//input[@type='submit' and @id='iSignupAction']")
        await self.page.wait_for_load_state(timeout=self.timeout)
        logger.info("Filled in the registration form with password.")

        logger.info("Filling in the registration form with first name and last name...")
        await self.page.fill("//input[@id='FirstName']", first_name)
        await self.page.fill("//input[@id='LastName']", last_name)
        await self.page.click("//input[@type='submit' and @id='iSignupAction']")
        await self.page.wait_for_load_state(timeout=self.timeout)
        logger.info("Filled in the registration form with first name and last name.")

        # Set the birthdate information
        logger.info("Setting birthdate information...")
        await self.page.select_option("#BirthMonth", f"{random.randint(1, 12)}")
        await self.page.select_option("#BirthDay", f"{random.randint(1, 28)}")
        await self.page.fill("#BirthYear", f"{random.randint(1970, 1985)}")
        await self.page.click("//input[@type='submit' and @id='iSignupAction']")
        await self.page.wait_for_load_state(timeout=self.timeout)
        logger.info("Birthdate information set.")

        await asyncio.sleep(30)

        logger.debug("Checking for captcha challenge via OCR ...")
        # Loop until we are sure there's no captcha.
        while True:
            await asyncio.sleep(30)
            captcha_not_detected_checks = []
            for _ in range(3):
                await asyncio.sleep(5)

                screenshot_outlook_captcha = await self._save_temp_screenshot("outlook_captcha")
                text = ocr_image(screenshot_outlook_captcha, normalize_text=True)
                logger.debug("OCR result: %s", text)

                # Check for specific captcha texts.
                if "Please solve the puzzle" in text or "Use the arrows to " in text:
                    logger.info("Captcha solving in progress, waiting ...")
                    # Captcha is detected
                    captcha_not_detected_checks.append(False)
                    continue
                # No captcha detected
                captcha_not_detected_checks.append(True)

            if all(captcha_not_detected_checks):
                logger.info("Captcha not detected in all checks, proceeding ...")
                break

        await asyncio.sleep(5)
        if self.page.url.startswith("https://privacynotice.account.microsoft.com/notice?"):
            logger.info("Outlook account successfully created.")
            return True

        logger.warning("Outlook account creation failed.")
        return False

    async def _grab_canvas_epicgames(self) -> bool:
        """
        Automates the process of creating a new Epic Games account.

        :return: True if the Epic Games account creation process is completed successfully, False otherwise.
        """

        logger.info("Initiating EpicGames account creation automation...")

        # Generate a new person with random attributes using a helper function
        person = new_person()
        email = person.email(domains=["gmail.com"])

        logger.info("Navigating to the Epic Games main page...")
        await self.page.goto("https://store.epicgames.com/en-US/", wait_until="networkidle", timeout=self.timeout)
        logger.info("Main page loaded.")

        logger.info("Proceeding to the Epic Games sign-up page...")
        await self.page.goto("https://www.epicgames.com/id/login?lang=en-US")
        logger.info("Sign-up page loaded.")

        logger.info("Filling in the registration form with the generated email...")
        email_input = self.page.locator("//input[@id='email']")
        await email_input.fill(email)
        await asyncio.sleep(5)
        await self.page.wait_for_load_state(timeout=self.timeout)

        logger.info("Filled in the registration form with the email.")

        while True:
            await asyncio.sleep(10)
            logger.info("Sending the Enter key to submit the registration form...")
            await email_input.focus()
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(10)
            await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            await asyncio.sleep(10)
            await self.page.keyboard.press("PageUp")
            await asyncio.sleep(10)
            logger.info("Enter key submitted.")

            logger.debug("Checking for captcha challenge via OCR ...")
            screenshot_epicgames_captcha = await self._save_temp_screenshot("epicgames_captcha")
            text = ocr_image(screenshot_epicgames_captcha, normalize_text=True)
            logger.debug("OCR result: %s", text)

            if "Please complete a security check to continue" in text or "Session ID: " in text or "IP Address" in text:
                logger.error("Captcha detected")
                raise BadProxyIPError("Captcha detected, restart CanvasInspector with a new proxy IP.")

            logger.info("Captcha not detected...")

            current_url = self.page.url
            if current_url.startswith("https://www.epicgames.com/id/register/date-of-birth"):
                logger.info("Captcha not detected, proceeding ...")
                break

            logger.info("URL is not changed, retrying ...")

        logger.info("EpicGames account successfully created.")
        return True

    async def grab_canvas(self) -> bool:
        """
        Orchestrates the process of capturing canvas fingerprint data from multiple websites.

        This method sequentially triggers the canvas data capture for each website, ensures
        that the environment is clean before each capture, and stores the results.

        :return: True if the canvas was successfully captured for all targeted websites,
                 False if one or more captures failed.
        :raises BadProxyIPError: Raised when a captcha challenge is detected, suggesting the possibility of a bad or
                flagged proxy IP, which could prevent successful account creation.
        """

        # Ensure all prerequisites for canvas capture are met.
        await self._check_prerequisites()
        # Initialize a list to store the success status for each website.
        capture_results = []

        # Clean the environment and capture canvas for Gmail.
        await self._clean_up()
        canvas_capture_success = False

        try:
            # Attempt to capture canvas data during Epic Games account creation
            canvas_capture_success = await self._grab_canvas_epicgames()
        except BadProxyIPError:
            # Handle BadProxyIPError, typically indicating issues with the proxy IP
            # Notify the CanvasInspector developer to address and fix the problem
            # to enable support for Epic Games in the future.
            pass

        capture_results.append(canvas_capture_success)
        await self._save_screenshot("epicgames")

        # Clean the environment and capture canvas for Gmail.
        await self._clean_up()
        gmail_capture_success = await self._grab_canvas_gmail()
        capture_results.append(gmail_capture_success)
        await self._save_screenshot("gmail")

        # Clean the environment and capture canvas for Vinted.
        await self._clean_up()
        vinted_capture_success = await self._grab_canvas_vinted()
        capture_results.append(vinted_capture_success)
        await self._save_screenshot("vinted")

        # Clean the environment and capture canvas for Outlook.
        await self._clean_up()
        outlook_capture_success = await self._grab_canvas_outlook()
        capture_results.append(outlook_capture_success)
        await self._save_screenshot("outlook")

        # Return True if all captures were successful, False otherwise.
        return all(capture_results)
