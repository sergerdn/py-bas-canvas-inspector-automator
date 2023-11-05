"""Fixtures for the tests."""
import os

import pytesseract  # type: ignore
import pytest

from tests import FIXTURES_DIR


@pytest.fixture(autouse=True)
def _set_tesseract_installed_path() -> None:
    """
    Set the path to the Tesseract-OCR executable.
    """

    paths = ["D:\\Program Files\\Tesseract-OCR", "C:\\Program Files\\Tesseract-OCR"]

    for path in paths:
        if os.path.exists(path):
            tesseract_cmd = os.path.join(path, "tesseract.exe")
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                return

    raise FileNotFoundError("Tesseract-OCR not found.")


@pytest.fixture(scope="module")
def screenshot_outlook_captcha() -> str:
    """
    Return the path to the screenshot of the Outlook captcha.
    """
    image_path = os.path.join(FIXTURES_DIR, "screenshot_outlook_captcha.png")
    assert os.path.exists(image_path)

    return image_path
