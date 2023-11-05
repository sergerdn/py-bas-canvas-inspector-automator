"""Test the OCR functionality."""
from py_bas_canvas_inspector_automator.ocr import ocr_image


class TestOcrOutlook:  # pylint: disable=too-few-public-methods
    """
    Functional tests for Outlook captcha.
    """

    def test_outlook(self, screenshot_outlook_captcha: str) -> None:
        """
        Test the Outlook captcha.
        :param screenshot_outlook_captcha: The path to the screenshot of the Outlook captcha.
        :return: None.
        :raises AssertionError: If the OCR failed.
        """

        text = ocr_image(screenshot_outlook_captcha, normalize_text=True)

        # Check if the expected text is in the OCR result
        assert "Please solve the puzzle" in text, "OCR failed."
