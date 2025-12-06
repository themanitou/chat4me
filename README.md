# Chat4Me

Chat4Me is an AI-powered chat automation tool that reads conversation history from your screen using **Gemini's Multimodal Capabilities** (direct image analysis) and generates context-aware replies. It works across different operating systems (Linux, Windows, macOS) by using manual coordinate selection and standard keyboard/mouse automation.

## Features

-   **AI-Powered Replies**: Uses Google's `gemini-2.5-flash` model to look at your screen and generate relevant, smart, and funny responses.
-   **True Multimodal Context**: Analyzes screenshots directly to understand context, layout, and identifying who is speaking based on visual cues (Right-aligned = Me).
-   **Smart Trigger**: Detects new messages by analyzing the latest screenshot content and sender, filtering out your own messages and visual noise.
-   **Unicode Support**: Correctly handles accented characters when typing replies via clipboard.
-   **Manual Region Selection**: Prompts the user to define the chat window and input box, ensuring compatibility with any app.
-   **Robust Fail-Safe**: Move your mouse to the **top-left corner (within 20x20 pixels)** of the screen to instantly stop the program.
-   **Dry-Run Mode**: Test the visual analysis and AI generation without actually sending messages.

## Prerequisites

1.  **Python 3.x**: Ensure you have Python installed.
2.  **Google Gemini API Key**:
    *   Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3.  **Clipboard Tool (Linux only)**:
    *   `sudo apt-get install xclip` (Required for `pyperclip` to work on Linux).
4.  **Dependencies**:
    *   The project uses `google-generativeai`, `Pillow`, `pyautogui`, and `pyperclip`.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/themanitou/chat4me.git
    cd chat4me
    ```
2.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Set your API Key**:
    *   **Linux/macOS**:
        ```bash
        export GEMINI_API_KEY='your_api_key_here'
        ```
    *   **Windows (Command Prompt)**:
        ```cmd
        setx GEMINI_API_KEY "your_api_key_here"
        ```

2.  **Run the script**:
    ```bash
    python chat4me.py
    ```
    *   To run in **Dry-Run Mode** (safe for testing):
        ```bash
        python chat4me.py --dry-run
        ```

3.  **Follow the on-screen instructions**:
    *   **Step 1**: Define the **Chat Window Region**. Move your mouse to the Top-Left corner and press Enter, then to the Bottom-Right corner and press Enter.
    *   **Step 2**: Define the **Message Input Box Center**. Move your mouse to the center of the text input area and press Enter.

4.  **Stop the Automation**:
    *   Move your mouse cursor to the **Top-Left Corner** of the screen (x < 20, y < 20) to trigger the fail-safe and exit.

## License

MIT License

Copyright (c) 2025 The Manitou

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
