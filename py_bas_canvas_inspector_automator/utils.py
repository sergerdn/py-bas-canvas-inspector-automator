"""Return a logger named based on the caller's full module path."""

import inspect
import json
import logging
from typing import Any, Dict


class ConfigFileNotFoundError(Exception):
    """Exception raised when the config file is not found."""


def get_config(config_path: str) -> Dict[str, Any]:
    """Load a configuration file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Dictionary with configuration data.
    """
    with open(config_path, "r", encoding="utf-8") as config_file:
        config_data: Dict[str, Any] = json.load(config_file)
        return config_data


def get_logger() -> logging.Logger:
    """Return a logger named based on the caller's full module path.

    Format: "[<full-module-path>]"
    """

    # Get the module name of the caller.
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])

    if module is None:
        raise ValueError("Could not determine the caller's module.")

    logger_name = f"[{module.__name__}]"

    logger = logging.getLogger(logger_name)
    # Optional: Set the logging level and formatter, or any other logger configuration you want here.

    return logger
