# tools/ui_automation.py
import pyautogui
from langchain_core.tools import tool

@tool
def click_coordinates(x: int, y: int):
    """Clicks the mouse at the specified screen coordinates (x, y).
    Use this tool *after* analyzing the screen to identify the correct coordinates for the target element.
    Coordinates originate from the top-left corner of the primary screen (0,0).
    Ensure the coordinates are accurate before calling this tool."""
    try:
        print(f"Attempting to click at ({x}, {y})")
        pyautogui.click(x, y)
        print(f"Successfully clicked at ({x}, {y})")
        return f"Successfully clicked at coordinates ({x}, {y})."
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return f"Error clicking at coordinates ({x}, {y}): {e}"

@tool
def type_text(text: str, interval: float = 0.05):
    """Types the given text using the keyboard.
    Make sure the correct input field is focused before calling this tool (e.g., by clicking it first)."""
    try:
        print(f"Attempting to type text: '{text}'")
        pyautogui.write(text, interval=interval)
        print("Successfully typed text.")
        return f"Successfully typed text: '{text}'"
    except Exception as e:
        print(f"Error typing text: {e}")
        return f"Error typing text: {e}"

@tool
def press_key(key: str):
    """Presses a specific keyboard key (e.g., 'enter', 'ctrl', 'shift', 'alt', 'f1', 'a', 'b').
    For special keys like Enter, Tab, Esc, use their names. For key combinations, press them sequentially or investigate pyautogui's hotkey function if needed."""
    try:
        # Basic validation for common keys - can be expanded
        valid_keys = pyautogui.KEYBOARD_KEYS
        if key.lower() not in valid_keys and len(key) != 1: # Allow single characters
             return f"Error: Invalid key name '{key}'. Use standard key names like 'enter', 'esc', 'f1', or single characters."

        print(f"Attempting to press key: '{key}'")
        pyautogui.press(key.lower()) # pyautogui usually expects lowercase key names
        print(f"Successfully pressed key: '{key}'")
        return f"Successfully pressed key '{key}'."
    except Exception as e:
        print(f"Error pressing key '{key}': {e}")
        return f"Error pressing key '{key}': {e}"

# Example of how the agent might use these:
# 1. User: "Describe my screen" -> Agent calls describe_screen_content()
# 2. Agent gets description: "There is a button labeled 'Submit' at coordinates (500, 300)."
# 3. User: "Click the submit button" -> Agent calls click_coordinates(x=500, y=300)
# 4. User: "Type 'hello world' into the text box" -> Agent might need to click the box first, then call type_text(text='hello world')