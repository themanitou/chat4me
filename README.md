# Chat4Me

Chat4Me is an AI-powered chat automation tool that reads conversation history from your screen using OCR (Optical Character Recognition) and generates context-aware replies using Google's Gemini API. It is designed to work across different operating systems (Linux, Windows, macOS) by using manual coordinate selection and standard keyboard/mouse automation.

## Features

-   **AI-Powered Replies**: Uses Google's `gemini-2.5-flash` model to generate relevant and conversational responses.
-   **Visual Context Awareness**: Reads the chat history directly from the screen, allowing it to work with any chat application.
-   **Multi-Language Support**: Configured to detect and read English, Vietnamese, and French text.
-   **Unicode Support**: correctly handles accented characters when typing replies.
-   **Manual Region Selection**: Prompts the user to define the chat window and input box, ensuring compatibility with various screen layouts and window managers.
-   **Robust Fail-Safe**: Move your mouse to the **top-left corner** of the screen at any time to instantly stop the program.
-   **Dry-Run Mode**: Test the OCR and AI generation without actually sending messages.

## Prerequisites

1.  **Python 3.x**: Ensure you have Python installed.
2.  **Tesseract OCR**: The tool uses Tesseract for text recognition. You need to install it along with the required language data.
    *   **Ubuntu/Debian**:
        ```bash
        sudo apt-get install tesseract-ocr tesseract-ocr-vie tesseract-ocr-fra
        ```
    *   **macOS**:
        ```bash
        brew install tesseract-lang
        ```
    *   **Windows**: Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki). Ensure you download the additional language data for Vietnamese and French.
3.  **Clipboard Tool (Linux only)**:
    *   `sudo apt-get install xclip` (Required for `pyperclip` to work on Linux).
4.  **Google Gemini API Key**:
    *   Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

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
    *   Move your mouse cursor to the **Top-Left Corner** of the screen (0, 0) to trigger the fail-safe and exit.

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
