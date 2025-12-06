
import time
import os
import pyautogui
# import pytesseract # Removed dependency
from PIL import Image, ImageChops, ImageStat
import google.generativeai as genai
import datetime
import json

# --- PRE-REQUISITES ---
# 1. Set up your Gemini API Key:
#    - Get your key from Google AI Studio: https://aistudio.google.com/app/apikey
#    - Set it as an environment variable named 'GEMINI_API_KEY'.
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
You will be provided with a series of screenshots showing the conversation history.
The screenshots are ordered chronologically.
Your job is to read the conversation from these images and provide helpful, relevant, and engaging responses.
Be smart and funny.

**Crucial Visual Cues:**
- Messages that are **aligned to the RIGHT** side of the chat window are from **[Me] (the user)**.
- Messages aligned to the LEFT are from other participants.

Based on the visible chat history in the images, generate the next message for [Me].
Try to match the style and tone of the [Me] messages.
"""

# How often to check for new messages (in seconds)
CHECK_INTERVAL = 30

# How many screenshots to keep in memory
HISTORY_LIMIT = 10

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

def get_point_from_user(point_name):
    """
    Asks the user to define a point by moving the mouse to the location.
    Returns (x, y).
    """
    print(f"\n--- Defining {point_name} ---")
    print(f"1. Move your mouse to the CENTER of the {point_name}.")
    input("   Press Enter when ready...")
    x, y = pyautogui.position()
    print(f"   Captured Point: ({x}, {y})")
    return (x, y)

def capture_screen_region(region):
    """
    Captures a screenshot of the specified region (x, y, width, height).
    """
    return pyautogui.screenshot(region=region)

def has_screen_changed(img1, img2, threshold_percent=0.05):
    """
    Checks if two screenshots are different by more than a certain percentage.
    threshold_percent: 0.05 corresponds to 5% change.
    """
    if img1 is None and img2 is None:
        return False
    if img1 is None or img2 is None:
        return True
    
    # Ensure images are the same size
    if img1.size != img2.size:
        return True

    # Calculate absolute difference
    diff = ImageChops.difference(img1, img2).convert('L')
    
    # Create a binary mask: 0 for identical (or close), 255 for different
    # We use a small pixel-level tolerance (e.g.,>15) to ignore compression artifacts/noise
    # 'point' is efficient for pixel-wise mapping
    mask = diff.point(lambda p: 255 if p > 15 else 0)
    
    # Calculate average pixel value of the mask (0 to 255)
    stat = ImageStat.Stat(mask)
    avg_diff = stat.mean[0] # List of means per channel (we have one L channel)
    
    # Percentage of changed pixels
    percent_changed = avg_diff / 255.0
    
    # debug print (optional, can remove later)
    # print(f"Screen diff: {percent_changed*100:.2f}%")
    
    return percent_changed > threshold_percent

def learn_conversation_history(chat_region, limit=HISTORY_LIMIT) -> list:
    """
    Scrolls up to learn the conversation history.
    And stitches screenshots into a single image saved in 'logs/'.
    """
    print("Learning conversation history...")
    
    # Ensure logs directory exists
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Click at bottom-right to focus
    x, y, w, h = chat_region
    bottom_right_x = x + w
    bottom_right_y = y + h
    pyautogui.click(bottom_right_x, bottom_right_y)
    time.sleep(0.5)

    history_pages_images = []
    
    # Using scroll(h) is more reliable than PageUp on some systems.
    # We scroll multiple times to capture enough history.
    # The loop runs 10 times to gather a good amount of context.
    
    for _ in range(limit):
        pyautogui.scroll(h)
        time.sleep(0.5) # Wait for scroll animation
        screenshot = capture_screen_region(chat_region)
        history_pages_images.append(screenshot)

    # Scroll back to the bottom
    for _ in range(limit + 2):
        pyautogui.scroll(-h)
        time.sleep(0.5) # Wait for scroll animation
        
    # --- Save Individual Images ---
    # Convert captured history_pages_images (Newest -> Oldest) to (Oldest -> Newest) for correct context
    ordered_images = []
    if history_pages_images:
        ordered_images = list(reversed(history_pages_images))
        
        for i, img in enumerate(ordered_images):
            # Save as screen_xx.png
            filename = f"logs/screen_{i:02d}.png"
            img.save(filename)
            print(f"Saved screenshot to {filename}")

    # No more text processing
    
    return ordered_images

def generate_reply(history_images: list, current_screenshot) -> str:
    """
    Sends the conversation history (images) to the Gemini API and gets a reply.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set.")
            exit()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Determine strict chronological order:
        # history_images contains [oldest, ..., newest-1]
        # current_screenshot is [newest]
        # We want to provide them in order.
        
        content_parts = [SYSTEM_PROMPT]
        
        # Add history images with context labels if possible, or just sequence them
        for i, img in enumerate(history_images):
            content_parts.append(f"Screenshot History Part {i+1}:")
            content_parts.append(img)
            
        content_parts.append("Current Chat View (Latest):")
        content_parts.append(current_screenshot)
        
        content_parts.append("Based on the above screenshots, what should [Me] reply?")
        
        response = model.generate_content(content_parts)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating reply from AI: {e}")
        return ""

def analyze_latest_message(image: Image.Image) -> dict:
    """
    Uses Gemini to analyze the latest message in the screenshot.
    Returns a dict with: {'sender': 'Me'|'Other', 'content': str, 'timestamp': str}
    """
    if image is None:
        return {}
    
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {}
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Analyze this chat screenshot. Focus on the very last (bottom-most) message.
        Return a JSON object with the following keys:
        1. "sender": "Me" if the message is aligned to the right, or "Other" if aligned to the left.
        2. "content": A short summary or the first few words of the message text.
        3. "timestamp": The timestamp string if visible near the message, or "Unknown".
        
        Example outputs:
        {"sender": "Me", "content": "Hello there", "timestamp": "10:30 AM"}
        {"sender": "Other", "content": "How are you?", "timestamp": "10:31 AM"}
        
        Return ONLY valid JSON.
        """
        
        response = model.generate_content([prompt, image])
        text = response.text.strip()
        
        # Clean up code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text)
    except Exception as e:
        print(f"Error analyzing latest message: {e}")
        return {}

import pyperclip

def send_message(input_box_center, message: str):
    """
    Clicks the input box and types the message using clipboard paste to support Unicode.
    """
    print(f"Sending message: '{message}'")
    try:
        # Click center of input box
        x, y = input_box_center
        pyautogui.click(x, y)
        time.sleep(0.5)
        
        # Use clipboard to handle Unicode characters (Vietnamese, French, etc.)
        pyperclip.copy(message)
        
        # Paste the message
        # Ctrl+V is standard for Linux/Windows. Command+V for macOS.
        # Detecting OS for safety, though Ctrl+V often works on Linux/Windows.
        if os.name == 'posix': # macOS or Linux
             # Check if it's macOS (Darwin)
             if os.uname().sysname == 'Darwin':
                 pyautogui.hotkey('command', 'v')
             else:
                 pyautogui.hotkey('ctrl', 'v')
        else:
            pyautogui.hotkey('ctrl', 'v')

        time.sleep(0.5) # Wait for paste
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
    
    try:
        # Get regions from user
        print("\nStep 1: Define the Chat Window Region (where messages appear).")
        chat_region = get_region_from_user("Chat Window")
        
        print("\nStep 2: Define the Message Input Box Center (where you type).")
        input_box_center = get_point_from_user("Message Input Box")

        print("\nAutomation will start in 5 seconds.")
        print("REMEMBER: Move your mouse to the top-left corner of the screen to stop.")
        time.sleep(5)
        
        # Learn history before starting the loop
        learned_history_images = learn_conversation_history(chat_region)
        
        last_processed_image = None
        last_message_state = {} # {'sender': '', 'content': '', 'timestamp': ''}
        
        while True:
            # Explicit fail-safe check
            if pyautogui.position().x < 20 and pyautogui.position().y < 20:
                raise pyautogui.FailSafeException("Manual fail-safe trigger")

            print("\nChecking for new messages...")
            
            # 1. Capture and read the current chat content
            current_window_image = capture_screen_region(chat_region)
            
            # 2. Check if screen has changed (Pixel Pre-check)
            has_visual_change = has_screen_changed(current_window_image, last_processed_image)
            
            if last_processed_image is None:
                 print("Initial run: analyzing current state...")
                 has_visual_change = True # Force analysis on first run
            
            if has_visual_change:
                print("Screen visual change (or initial run) detected. Analyzing with Gemini...")
                
                # 3. Analyze the latest message
                analysis = analyze_latest_message(current_window_image)
                print(f"Analysis Result: {analysis}")
                
                sender = analysis.get('sender', 'Unknown')
                content = analysis.get('content', '')
                
                # Check 1: Is the sender Me?
                if sender == 'Me':
                    print("Last message is from [Me]. Ignoring.")
                    last_processed_image = current_window_image
                    last_message_state = analysis
                    time.sleep(CHECK_INTERVAL)
                    continue
                    
                # Check 2: Is it the same message as before? (Duplicate check)
                prev_content = last_message_state.get('content', '')
                if content == prev_content and content != "":
                     print("Message content appears identical to last processed. Ignoring.")
                     last_processed_image = current_window_image
                     # Don't update last_message_state if it's the same, or do? 
                     # If it's the same, we just wait.
                     time.sleep(CHECK_INTERVAL)
                     continue

                print("New message from 'Other' confirmed!")
                
                # 4. Generate a reply
                print("Generating reply...")
                reply = generate_reply(learned_history_images, current_window_image)
                
                if reply:
                    # 5. Send the reply (or print if dry-run)
                    if args.dry_run:
                        print(f"\n[DRY RUN] Generated Reply: {reply}\n")
                    else:
                        send_message(input_box_center, reply)
                        # Give time for the message to send and appear
                        time.sleep(3)
                    
                    # Update the baseline
                    if not args.dry_run:
                        final_image = capture_screen_region(chat_region)
                        last_processed_image = final_image
                    else:
                        last_processed_image = current_window_image
                        
                    last_message_state = analysis # Update this to the triggering message

                    # 6. Update the learned history
                    learned_history_images.append(current_window_image)
                    if len(learned_history_images) > HISTORY_LIMIT:
                        learned_history_images.pop(0)

                else:
                    print("AI did not generate a reply.")
                    last_processed_image = current_window_image
                    last_message_state = analysis

            else:
                print("No visual change detected.")


            # Wait before the next check
            time.sleep(CHECK_INTERVAL)
            
    except pyautogui.FailSafeException:
        print("\nFailsafe activated. Exiting program.")
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        time.sleep(10) # Wait a bit longer after an error

if __name__ == "__main__":
    main()
