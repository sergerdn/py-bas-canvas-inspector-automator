""" This is a main worker script to run the automator. """
import asyncio
import logging
import os

from py_bas_canvas_inspector_automator import Automator, find_proc

logging.basicConfig(level=logging.DEBUG)

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR_PATH = os.path.join(ABS_PATH, "docs", "screenshots")


async def main() -> None:
    """
    Run the automator and grab the canvas.
    """

    if not os.path.exists(SCREENSHOT_DIR_PATH):
        os.makedirs(SCREENSHOT_DIR_PATH)

    remote_debugging_port = find_proc()
    async with Automator(
        remote_debugging_port=remote_debugging_port, screenshot_dir_path=SCREENSHOT_DIR_PATH
    ) as automator:
        await automator.grab_canvas()


if __name__ == "__main__":
    asyncio.run(main())
