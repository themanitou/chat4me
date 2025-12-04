
import time
import os
import pyautogui
import pytesseract
from PIL import Image
import google.generativeai as genai

# --- PRE-REQUISITES ---
# 1. Install Tesseract OCR on your system:
#    - Debian/Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-vie tesseract-ocr-fra
#    - macOS: brew install tesseract-lang
#    - Windows: Download language data from https://github.com/tesseract-ocr/tessdata
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
The user you are acting as is the one whose messages are marked with [Me].
Other messages are from other participants and will usually be preceded by their username.
Based on the provided chat history, generate the next message for the user ([Me]).
Try to match the style and tone of the [Me] messages.
"""

# How often to check for new messages (in seconds)
CHECK_INTERVAL = 30

def get_region_from_user(region_name):
    """
    Asks the user to define a region by moving the mouse to the top-left and bottom-right corners.
    Returns (x, y, width, height).
    """
    print(f"\n--- Defining {region_name} ---")
    print(f"1. Move your mouse to the TOP-LEFT corner of the {region_name}.")
    input("   Press Enter when ready...")
    x1, y1 = pyautogui.position()
    print(f"   Captured Top-Left: ({x1}, {y1})")
    
    print(f"2. Move your mouse to the BOTTOM-RIGHT corner of the {region_name}.")
    input("   Press Enter when ready...")
    x2, y2 = pyautogui.position()
    print(f"   Captured Bottom-Right: ({x2}, {y2})")
    
    min_x = min(x1, x2)
    min_y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    print(f"   Defined Region: (x={min_x}, y={min_y}, w={width}, h={height})")
    return (min_x, min_y, width, height)

def capture_screen_region(region):
    """
    Captures a screenshot of the specified region (x, y, width, height).
    """
    return pyautogui.screenshot(region=region)

def extract_text_from_image(image: Image.Image) -> str:
    """
    Uses Tesseract OCR to extract text from a PIL Image.
    Distinguishes between [Me] (right-aligned) and other messages.
    Supports English, Vietnamese, and French.
    """
    if image is None:
        return ""
    try:
        # Use image_to_data to get bounding box information
        # output_type=Output.DICT returns a dictionary of lists
        from pytesseract import Output
        data = pytesseract.image_to_data(image, output_type=Output.DICT, lang='eng+vie+fra')
        
        image_width = image.width
        formatted_lines = []
        
        # Group words into lines based on 'line_num' and 'block_num' (or just line_num)
        # But image_to_data returns words. We need to reconstruct lines.
        # A simpler approach for alignment is to look at the 'left' of the first word of a line.
        
        current_line_text = []
        current_line_left = -1
        last_line_num = -1
        
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if not text:
                continue
                
            line_num = data['line_num'][i]
            left = data['left'][i]
            
            if line_num != last_line_num:
                # New line started. Process the previous line.
                if current_line_text:
                    full_line = " ".join(current_line_text)
                    # Determine alignment based on the start position (left)
                    # If it starts past the middle, it's likely right-aligned (Me)
                    # This is a heuristic. Right-aligned text usually starts > 50% width, 
                    # but short messages might be tricky. 
                    # However, standard chat bubbles for "Me" usually start on the right half.
                    # Let's use a threshold of 40% to be safe, or check if it's closer to right edge.
                    # Actually, "Me" messages are right aligned, so their *left* bound should be large.
                    
                    # A better heuristic might be:
                    # If left > image_width * 0.4 -> [Me]
                    # Else -> Raw text
                    
                    if current_line_left > (image_width * 0.4):
                        formatted_lines.append(f"[Me]: {full_line}")
                    else:
                        formatted_lines.append(full_line)
                
                current_line_text = []
                current_line_left = left
                last_line_num = line_num
            
            current_line_text.append(text)
            
        # Process the last line
        if current_line_text:
            full_line = " ".join(current_line_text)
            if current_line_left > (image_width * 0.4):
                formatted_lines.append(f"[Me]: {full_line}")
            else:
                formatted_lines.append(full_line)
            
        return "\n".join(formatted_lines)

    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not in your PATH.")
        print("Please install Tesseract and try again.")
        exit()
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def learn_conversation_history(chat_region, limit=20) -> str:
    """
    Scrolls up to learn the conversation history.
    """
    print("Learning conversation history...")
    
    # Click center to focus
    x, y, w, h = chat_region
    center_x = x + w // 2
    center_y = y + h // 2
    pyautogui.click(center_x, center_y)
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
    
    for _ in range(20):
        pyautogui.press('pageup')
        time.sleep(0.5) # Wait for scroll animation
        screenshot = capture_screen_region(chat_region)
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
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Combine learned history with current visible history
        full_context = f"{learned_history}\n\n[...]\n\n{conversation_history}"
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nChat History:\n---\n{full_context}\n---\nYour Reply:"
        
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply from AI: {e}")
        return ""

def send_message(input_box_region, message: str):
    """
    Clicks the input box and types the message.
    """
    print(f"Sending message: '{message}'")
    try:
        # Click center of input box
        x, y, w, h = input_box_region
        center_x = x + w // 2
        center_y = y + h // 2
        pyautogui.click(center_x, center_y)
        time.sleep(0.5)
        
        pyautogui.write(message, interval=0.02)
        pyautogui.press('enter')
    except Exception as e:
        print(f"Failed to send message: {e}")

def main():
    """
    The main function to run the chat automation loop.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Chat4Me - AI Chat Automation")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (do not send messages)")
    args = parser.parse_args()

    print("--- Chat4Me Initializing ---")
    if args.dry_run:
        print("!!! DRY RUN MODE ENABLED - Messages will NOT be sent !!!")
    
    # Get regions from user
    print("\nStep 1: Define the Chat Window Region (where messages appear).")
    chat_region = get_region_from_user("Chat Window")
    
    print("\nStep 2: Define the Message Input Box Region (where you type).")
    input_box_region = get_region_from_user("Message Input Box")

    print("\nAutomation will start in 5 seconds.")
    print("REMEMBER: Move your mouse to the top-left corner of the screen to stop.")
    time.sleep(5)
    
    # Learn history before starting the loop
    learned_history = learn_conversation_history(chat_region)
    
    last_processed_text = ""
    
    while True:
        try:
            # Explicit fail-safe check
            if pyautogui.position() == (0, 0):
                raise pyautogui.FailSafeException("Manual fail-safe trigger")

            print("\nChecking for new messages...")
            
            # 1. Capture and read the current chat content
            window_image = capture_screen_region(chat_region)
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
                    # 4. Send the reply (or print if dry-run)
                    if args.dry_run:
                        print(f"\n[DRY RUN] Generated Reply: {reply}\n")
                    else:
                        send_message(input_box_region, reply)
                        # Give time for the message to send and appear
                        time.sleep(3)
                    
                    # Update the baseline text
                    if not args.dry_run:
                        final_image = capture_screen_region(chat_region)
                        last_processed_text = extract_text_from_image(final_image)
                    else:
                        last_processed_text = current_text

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
