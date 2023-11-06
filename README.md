# py-BAS Canvas Inspector Automator

**Disclaimer:** This library is under active development. APIs may change without prior notice. Use at your own
discretion.

**Note:** This project originated as a `working proof of concept`. It is not designed to provide exhaustive support or
documentation. Instead, it serves as a foundational tool for further development and experimentation.

## Description

The `py-bas-canvas-inspector-automator` is a Python library crafted to facilitate automated interactions with
Bablosoft's [CanvasInspector](https://wiki.bablosoft.com/doku.php?id=perfectcanvas). This library equips developers with
the means to programmatically manage the `CanvasInspector`, streamlining the automation of tasks related to canvas
fingerprinting.

## Key Features

- **Automation of PerfectCanvas Requests:** Streamline the acquisition of PerfectCanvas requests for any website,
  enabling seamless integration into your automation workflows.
- **Advanced Fingerprinting Bypass:** Utilize cutting-edge techniques to bypass sophisticated canvas fingerprinting
  mechanisms, ensuring privacy and anonymity.

## Supported Websites

The automator is purpose-built to capture canvas fingerprint data during the account creation process.

The platforms listed below have either been implemented or are targeted for future implementation:

- [x] Google: https://www.google.com/
- [x] Vinted: https://www.vinted.com/
- [x] Outlook: https://outlook.live.com/
- [ ] Twitter: https://twitter.com/
- [ ] Reddit: https://www.reddit.com/
- [ ] LinkedIn: https://www.linkedin.com/
- [ ] Twitch: https://www.twitch.tv/
- [ ] TikTok: https://www.tiktok.com/

If you need to add support for a website or have suggestions, feel free to open
an [issue](https://github.com/sergerdn/py-bas-canvas-inspector-automator/issues/new) or create
a [pull request](https://github.com/sergerdn/py-bas-canvas-inspector-automator/pulls).

The current encoded fingerprint data captured from implemented websites is located in
the [fp_request.txt](./docs/data/fp_request.txt) file.

## Workflow Overview

The standard workflow with BAS is outlined in the following steps:

1. **Initiate CanvasInspector**:
   Begin by manually launching the `CanvasInspector` tool.
2. **Automate Canvas Data Capture**:
   Execute the `cmd_worker.py` script to automate the canvas data capture process. The script identifies and interacts
   with the running browser instance via the `CanvasInspector` tool on the local OS.
3. **Restart and Verify**:
   If necessary, restart the `CanvasInspector` tool and repeat the process to verify the accuracy of the data capture.

## Prerequisites

- `Python 3.11` or later
- [Poetry](https://python-poetry.org/) for dependency management
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki#tesseract-installer-for-windows) for reliable
  information retrieval from webpage images.
- A solid understanding of the purpose and mechanisms behind canvas fingerprinting and automation

## Installation

Follow these steps to install the ` py-bas-canvas-inspector-automator`:

1. Clone the repository:
    ```bash
    git clone git@github.com:sergerdn/py-bas-canvas-inspector-automator.git
    ```
2. Navigate to the cloned directory:
    ```bash
    cd  py-bas-canvas-inspector-automator
    ```
3. Retrieve the large files with Git LFS:
    ```bash
    git lfs pull
    ```
4. Install the project dependencies using Poetry:
    ```bash
    poetry install
    ```

## Preparation

Before using the automator, you need to set up the CanvasInspector tool:

1. Extract the [CanvasInspector.zip](contrib/CanvasInspector.zip) to a desired location on your system.
2. Launch `CanvasInspector.exe` and allow it to fully initialize.

## Usage

Leverage the `py-bas-canvas-inspector-automator` to streamline your tasks by following these steps:

1. **Configure CanvasInspector**:
   Launch the `CanvasInspector` application and tailor the settings to fit your requirements. For optimal performance,
   setting a `Profile Path` is advisable. The screenshot below provides a visual guide for configuring the main window
   settings:
   ![CanvasInspector Main Window](docs/images/canvas_main_window.png)
2. **Execute the Automation Script**:
   Kickstart the canvas fingerprint capture by executing the `cmd_worker.py` script:
    ```bash
    make run_worker
    ```
   This script facilitates automated interactions with the CanvasInspector tool to obtain the canvas fingerprint data.

3. **Iterate as Necessary**:
   If you need to adjust settings or capture additional data, restart the `CanvasInspector` application and repeat the
   process to ensure accuracy.
4. **Save the PerfectCanvas Request**:
   Post-completion of the required actions in CanvasInspector, press the `Save Request` button to copy the PerfectCanvas
   request to your clipboard.
   ![CanvasInspector Request](docs/images/canvas_copy_request.png)

**Pro Tip:** Confirm that all configurations in `CanvasInspector` are finalized before initiating the `cmd_worker.py`
script. This precaution helps prevent any inconsistencies or errors during the automation process.
