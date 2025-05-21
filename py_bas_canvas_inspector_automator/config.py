"""This module provides functionality to read and parse configuration files."""

import json
import os
from typing import Any, Dict


def get_config(config_path: str) -> Dict[str, Any]:
    """Reads a JSON configuration file from the specified path.

    Args:
        config_path: The path to the JSON configuration file.

    Returns:
        A dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, "r", encoding="utf-8") as config_file:
        try:
            config_data: Dict[str, Any] = json.load(config_file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error decoding JSON from {config_path}: {e.msg}", e.doc, e.pos) from e
    return config_data
