"""Ocr module."""
import os

import pytesseract  # type: ignore
from PIL import Image, ImageEnhance, ImageFilter


def _set_tesseract_installed_path() -> None:
    """
    Set the path to the Tesseract-OCR installation.
    :return: None
    :raises FileNotFoundError: If Tesseract-OCR is not found.
    """

    paths = ["D:\\Program Files\\Tesseract-OCR", "C:\\Program Files\\Tesseract-OCR"]

    for path in paths:
        if os.path.exists(path):
            tesseract_cmd = os.path.join(path, "tesseract.exe")
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                return

    raise FileNotFoundError("Tesseract-OCR not found.")


_set_tesseract_installed_path()


def _preprocess_image(image_path: str) -> Image.Image:
    """
    Preprocess the image for OCR.
    :param image_path: The path to the image.
    :return: A preprocessed image.
    """

    # Open the image
    image = Image.open(image_path)

    # Convert the image to grayscale
    image = image.convert("L")

    # Enhance the image contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)

    # Apply a threshold to get a black and white effect
    # You may need to adjust the threshold level (here it's 150)
    threshold = 150
    image = image.point(lambda p: p > threshold and 255)

    # Optionally apply some additional filtering
    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

    return image


def ocr_image(image_path: str, normalize_text: bool = False) -> str:
    """
    Perform OCR on the image.
    """

    # Preprocess the image for better OCR results
    preprocessed_image = _preprocess_image(image_path)

    # Perform OCR on the preprocessed image
    text = pytesseract.image_to_string(preprocessed_image) or ""
    if normalize_text and text:
        text = text.replace("\n", " ").replace("\r", " ").strip()

    return text
