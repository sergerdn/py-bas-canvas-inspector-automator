"""This module provides functionality to manage page navigation, form filling, and
interaction with web elements."""

import json
from typing import Dict, Literal

from playwright.async_api import Page

from py_bas_canvas_inspector_automator.utils import get_logger

logger = get_logger()


class WebNavigator:
    """Manages page navigation, form filling, and interaction with web elements."""

    page: Page
    timeout: int
    browser_info: Dict

    def __init__(self, page: Page, timeout: int = 60000) -> None:
        """Initialize the WebNavigator class.

        Args:
            page: The Playwright Page object.
            timeout: The default timeout for page operations.
        """
        self.page = page
        self.timeout = timeout

    async def navigate_to_page(
        self,
        url: str,
        wait_until: Literal["commit", "domcontentloaded", "load", "networkidle"] = "networkidle",
    ) -> None:
        """Navigate to a specific URL.

        Args:
            url: The URL to navigate to.
            wait_until: The condition to wait for before considering the navigation complete.
                        One of: "commit", "domcontentloaded", "load", "networkidle".
        """
        logger.info("Navigating to: %s", url)
        await self.page.goto(url, wait_until=wait_until, timeout=self.timeout)

    async def fill_form_field(self, selector: str, value: str) -> None:
        """Fill a form field with a specific value.

        Args:
            selector: The selector for the form field.
            value: The value to fill in the form field.
        """
        logger.info("Filling form field: %s with value: %s", selector, value)
        await self.page.fill(selector, value)

    async def click_element(self, selector: str) -> None:
        """Click on a specific element.

        Args:
            selector: The selector for the element to click.
        """
        logger.info("Clicking on element: %s", selector)
        await self.page.click(selector)

    async def select_option(self, selector: str, value: str) -> None:
        """Select an option from a dropdown.

        Args:
            selector: The selector for the dropdown.
            value: The value to select.
        """
        logger.info("Selecting option: %s in dropdown: %s", value, selector)
        await self.page.select_option(selector, value)

    async def get_page_content(self) -> str:
        """Get the content of the page.

        Returns:
            str: Page content
        """
        logger.info("Getting page content")
        content: str = await self.page.evaluate("document.documentElement.innerText")
        return content

    async def check_prerequisites(self) -> None:
        """Check browser prerequisites."""
        logger.info("Checking browser info...")
        await self.navigate_to_page("https://lumtest.com/echo.json", wait_until="networkidle")
        page_source = await self.get_page_content()
        self.browser_info = json.loads(page_source)
        print(json.dumps(self.browser_info, indent=4))
        logger.info("Browser info: %s", self.browser_info)
