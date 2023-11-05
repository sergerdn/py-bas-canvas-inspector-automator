"""Initialize the tests package."""
import os
import platform

# Get the absolute path to the root project directory.
ABS_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

# Check if the current operating system is Windows.
is_windows = platform.system().lower() == "windows"

# Define the path to the fixtures directory used in tests.
FIXTURES_DIR = os.path.join(ABS_PATH, "tests", "fixtures")

# Ensure the fixtures directory exists; if not, this will raise an AssertionError.
assert os.path.exists(FIXTURES_DIR)
