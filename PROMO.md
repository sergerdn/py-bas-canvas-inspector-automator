🌐 **Automated Canvas Fingerprinting Capture with py-BAS Canvas Inspector Automator** 🌐

In the realm of digital fingerprinting, canvas fingerprinting stands as a formidable challenge for developers and
automation enthusiasts alike. The _py-BAS Canvas Inspector Automator_ library is a Python-based solution designed to
automate the capture of canvas fingerprinting, particularly useful when dealing with multiple websites and the need to
grab and verify fingerprints efficiently.

🔍 **Understanding Canvas Fingerprinting**:

Canvas fingerprinting is a tracking technique that websites use to identify and track visitors. By drawing a hidden
image in the browser, the website can generate a unique fingerprint based on the rendered image data. This fingerprint
can be used to track users across sessions, even if they change their IP address or clear cookies.

🛠 **The Solution: PerfectCanvas**:

PerfectCanvas is a technology that allows for the accurate rendering of canvas data on a remote machine, which is then
sent to your PC to replace the canvas data inside the browser. This method ensures that the canvas data is
indistinguishable from a real user's data, bypassing sophisticated anti-fraud systems.

🤖 **Introducing py-BAS Canvas Inspector Automator**:

The _py-BAS Canvas Inspector Automator_ library automates the process of capturing this canvas fingerprint data. It's
especially handy when you're working with multiple websites and need to ensure that the canvas fingerprints have not
changed over time.

💻 **How It Works**:

1. **CanvasInspector Tool**: The library works with the CanvasInspector tool, which captures the PerfectCanvas request
   from the website you're working with.
2. **Automated Data Capture**: Once the CanvasInspector is set up, the _py-BAS Canvas Inspector Automator_ can be
   scheduled to run at intervals, automatically capturing the canvas fingerprint data and verifying any changes.
3. **Integration with Automation Workflows**: The captured canvas fingerprint data can be integrated into your
   automation workflows, allowing for seamless and continuous verification processes.

📌 **Key Advantages**:

- **Automated Process**: Once set up, the library can capture and verify canvas fingerprint data without manual
  intervention.
- **Multi-Website Support**: It can handle multiple websites simultaneously, making it ideal for large-scale operations.
- **Accuracy**: By using PerfectCanvas technology, it ensures that the data captured is accurate and reliable.

📢 **Call to Action**:

For developers and automation experts who are tackling the challenges of canvas fingerprinting,
the _py-BAS Canvas Inspector Automator_ offers a powerful tool to automate and streamline your processes. Embrace the
future of automation by integrating this library into your workflow today!

🌐 Supported Websites

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

🛠 **Requirements**:

- _Python 3.11_ or later
- [Poetry](https://python-poetry.org/) for dependency management
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki#tesseract-installer-for-windows) for reliable
  information retrieval from webpage images.
- A solid understanding of the purpose and mechanisms behind canvas fingerprinting and automation

🔧 **Get Started**:

1. Clone the [repo](https://github.com/sergerdn/py-bas-canvas-inspector-automator).
2. Install dependencies with Poetry.
3. Launch the _CanvasInspector_ application and tailor the settings to fit your requirements.
4. Execute the _cmd_worker.py_ script to automate the canvas data capture process.

**Note**:  For detailed instructions, technical support, and further discussion, please refer to
the [GitHub](https://github.com/sergerdn/py-bas-canvas-inspector-automator)
