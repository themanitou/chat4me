
import time
import os
import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image
import google.generativeai as genai

# --- PRE-REQUISITES ---
# 1. Install Tesseract OCR on your system:
#    - Debian/Ubuntu: sudo apt-get install tesseract-ocr
#    - macOS: brew install tesseract
#    - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
#    You may need to set the command path if it's not in your system's PATH:
#    pytesseract.pytesseract.tesseract_cmd = r'/path/to/your/tesseract'

# 2. Set up your Gemini API Key:
#    - Get your key from Google AI Studio: https://aistudio.google.com/app/apikey
#    - Set it as an environment variable named 'GEMINI_API_KEY'.
#      - Linux/macOS: export GEMINI_API_KEY='Your-API-Key'
#      - Windows: setx GEMINI_API_KEY "Your-API-Key"
#    - The script will not run without this key.

# 3. Fail-Safe:
#    - To stop the script at any time, move your mouse cursor to the top-left corner of the screen.
#    - This will trigger a `pyautogui.FailSafeException` and exit the program.

# --- CONFIGURATION ---
# The prompt for the AI. You can customize this to change the AI's personality.
SYSTEM_PROMPT = """
You are an AI assistant integrated into a chat application. 
Your job is to read the ongoing conversation and provide helpful, relevant, and engaging responses.
Keep your replies concise and conversational.
The user you are acting as is the one whose messages are not visible in the history provided.
Based on the provided chat history, generate the next message for the user.
"""

# How often to check for new messages (in seconds)
CHECK_INTERVAL = 5

def select_chat_window():
    """
    Lists all open windows and lets the user select the target chat window.
    """
    print("Listing all open windows...")
    windows = gw.getAllTitles()
    if not windows:
        print("Error: No open windows found.")
        exit()

    for i, title in enumerate(windows):
        if title:
            print(f"{i}: {title}")

    try:
        window_number = int(input("Enter the number of the chat window: "))
        if 0 <= window_number < len(windows):
            window_title = windows[window_number]
            print(f"Selected window: '{window_title}'")
            return gw.getWindowsWithTitle(window_title)[0]
        else:
            print("Invalid number. Please run the script again.")
            exit()
    except (ValueError, IndexError):
        print("Invalid input. Please run the script again.")
        exit()

def capture_window_content(window):
    """
    Captures a screenshot of the specified window's content area.
    """
    if not window.isActive:
        try:
            window.activate()
        except gw.PyGetWindowException:
            print("Could not activate the window. Please make sure it is not minimized.")
            return None
        time.sleep(0.5) # Give the window time to come to the foreground

    # Take a screenshot of the window region
    x, y, width, height = window.left, window.top, window.width, window.height
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    return screenshot

def extract_text_from_image(image: Image.Image) -> str:
    """
    Uses Tesseract OCR to extract text from a PIL Image.
    """
    if image is None:
        return ""
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not in your PATH.")
        print("Please install Tesseract and try again.")
        exit()
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def learn_conversation_history(window, limit=20) -> str:
    """
    Scrolls up to learn the conversation history.
    """
    print("Learning conversation history...")
    if not window.isActive:
        window.activate()
        time.sleep(0.5)

    history_pages = []
    
    # Capture the current (bottom) view first
    # We might want to skip this if we want strictly "past" history, 
    # but usually "history" includes the immediate past.
    # Let's scroll up first.
    
    # Scroll up a few times. 
    # Assuming one PageUp covers ~10-20 lines depending on font size.
    # We want ~20 messages. If messages are short, 2-3 PageUps might be enough.
    # If messages are long, we might need more.
    # Let's try 3 PageUps.
    
    for _ in range(3):
        pyautogui.press('pageup')
        time.sleep(0.5) # Wait for scroll animation
        screenshot = capture_window_content(window)
        text = extract_text_from_image(screenshot)
        history_pages.append(text)
        
    # Scroll back to bottom
    pyautogui.press('end')
    time.sleep(0.5)
    
    # Combine and clean up
    # This is a naive combination; it might have duplicates if PageUp overlaps.
    # For a simple implementation, we'll just concatenate reversed.
    full_history = "\n".join(reversed(history_pages))
    
    # Simple heuristic to limit to ~20 "messages" (blocks of text separated by newlines)
    lines = full_history.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    # If we assume a message is roughly a non-empty line (or a few), 
    # taking the last 50 non-empty lines is a safe bet for context.
    limited_history = "\n".join(non_empty_lines[-50:])
    
    print(f"Learned history (last ~50 lines):")
    print(limited_history)
    print("--------------------------------------------------")
    
    return limited_history

def generate_reply(conversation_history: str, learned_history: str = "") -> str:
    """
    Sends the conversation history to the Gemini API and gets a reply.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set.")
            exit()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Combine learned history with current visible history
        full_context = f"{learned_history}\n\n[...]\n\n{conversation_history}"
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nChat History:\n---\n{full_context}\n---\nYour Reply:"
        
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply from AI: {e}")
        return ""

def send_message(window, message: str):
    """
    Activates the window and types the message into the chat box.
    """
    print(f"Sending message: '{message}'")
    try:
        if not window.isActive:
            window.activate()
        time.sleep(0.5)
        
        # This part is crucial and might need adjustment.
        # It assumes the chat input box is focused when the window is activated.
        # For some apps, you might need to click on the input box first.
        pyautogui.write(message, interval=0.02)
        pyautogui.press('enter')
    except Exception as e:
        print(f"Failed to send message: {e}")

def main():
    """
    The main function to run the chat automation loop.
    """
    print("--- Chat4Me Initializing ---")
    
    chat_window = select_chat_window()
    
    if not chat_window:
        print("No window selected. Exiting.")
        return

    print("\nAutomation will start in 5 seconds.")
    print("IMPORTANT: Make sure the chat application's text input box is selected.")
    print("REMEMBER: Move your mouse to the top-left corner of the screen to stop.")
    time.sleep(5)
    
    # Learn history before starting the loop
    learned_history = learn_conversation_history(chat_window)
    
    last_processed_text = ""
    
    while True:
        try:
            print("\nChecking for new messages...")
            
            # 1. Capture and read the current chat content
            window_image = capture_window_content(chat_window)
            current_text = extract_text_from_image(window_image)

            if not current_text.strip():
                print("No text detected in the window.")
                time.sleep(CHECK_INTERVAL)
                continue
            
            # 2. Check if there are new messages
            if current_text != last_processed_text and last_processed_text in current_text:
                print("New message detected!")
                
                # 3. Generate a reply
                print("Generating reply...")
                reply = generate_reply(current_text, learned_history)
                
                if reply:
                    # 4. Send the reply
                    send_message(chat_window, reply)
                    
                    # Give time for the message to send and appear
                    time.sleep(3)
                    
                    # Update the baseline text to include our own message
                    final_image = capture_window_content(chat_window)
                    last_processed_text = extract_text_from_image(final_image)
                else:
                    print("AI did not generate a reply.")
                    last_processed_text = current_text # Update to avoid re-processing

            elif current_text != last_processed_text:
                # The chat content has changed, but not in an append-only way
                # (e.g., scroll, new day, someone edited/deleted a message)
                print("Chat history seems to have changed or scrolled. Resetting baseline.")
                last_processed_text = current_text

            else:
                print("No new messages.")

            # Wait before the next check
            time.sleep(CHECK_INTERVAL)
            
        except pyautogui.FailSafeException:
            print("\nFailsafe activated. Exiting program.")
            break
        except KeyboardInterrupt:
            print("\nProgram interrupted by user. Exiting.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            time.sleep(10) # Wait a bit longer after an error

if __name__ == "__main__":
    main()
