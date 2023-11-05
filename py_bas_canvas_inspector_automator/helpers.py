"""Helper functions for the Canvas Inspector Automator."""
import os

import psutil

# Define the names of the processes to look for
WORKER_PROC_NAME = "Worker.exe"  # Worker browser process (mother)
BROWSER_PROC_NAME = "worker.exe"  # Chromium browser process (child)

# Define the directory path for the Canvas Inspector
CANVAS_INSPECTOR_CMD_PATH = os.path.join("appsremote", "CanvasInspector3")


def find_proc() -> int:
    """
    Find the process of the Canvas Inspector application.
    :returns: The remote debugging port number of the Canvas Inspector application.
    """

    # Iterate through all running processes
    for proc in psutil.process_iter():
        name = proc.name()

        # Check if the process is a Worker.exe process
        if name == WORKER_PROC_NAME:
            parent_proc = proc.parent()  # Get the parent process (browser process)
            if parent_proc.name() != "FastExecuteScript.exe":
                continue

            found_proc = False
            for _cmd in parent_proc.cmdline():
                if CANVAS_INSPECTOR_CMD_PATH in _cmd:
                    found_proc = True
                    break
            print(found_proc)

            for child in proc.children(recursive=False):
                # Check if the child process is the browser process
                if child.name() != BROWSER_PROC_NAME:
                    continue
                cmd_line = child.cmdline()

                for line in cmd_line:
                    line = line.strip()

                    # Check if the command line argument specifies the user data directory
                    if not line.startswith("--remote-debugging-port="):
                        continue
                    _, _remote_debugging_port = line.split("=")
                    return int(_remote_debugging_port)  # Return the port number

    return 0  # Return 0 if no matching process is found


if __name__ == "__main__":
    remote_debugging_port = find_proc()
    print(f"Remote Debugging Port: {remote_debugging_port}")
