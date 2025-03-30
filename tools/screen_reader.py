# tools/screen_reader.py
import base64
import io
from PIL import ImageGrab
from openai import OpenAI, OpenAIError
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

try:
    client = OpenAI()
    # Perform a simple test call or check key existence if needed
    # Although the actual call in the tool will reveal issues
except OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure the OPENAI_API_KEY environment variable is set correctly.")
    client = None # Set client to None to indicate initialization failure

@tool
def describe_screen_content(user_prompt: str = "Describe the current screen content in detail.", detail_level: str = "low"):
    """
    Captures the primary screen, sends it to a vision model (GPT-4o) for analysis,
    and returns the model's description.

    Args:
        user_prompt (str): The prompt to ask the vision model about the screen content.
                           Defaults to "Describe the current screen content in detail.".
        detail_level (str): The level of detail for image analysis ('low' or 'high').
                            'low' saves costs but provides less detail. Defaults to 'low'.

    Returns:
        A string containing the vision model's description of the screen,
        or an error message if the process fails.

    Note: This tool uses the OpenAI API and requires the OPENAI_API_KEY environment
          variable to be set. Sending images incurs token costs.
    """
    if not client:
        return "Error: OpenAI client failed to initialize. Check API key."

    if detail_level not in ["low", "high"]:
        return "Error: Invalid detail_level. Must be 'low' or 'high'."

    try:
        print("Capturing screen for vision analysis...")
        # Capture the primary screen
        screenshot = ImageGrab.grab()
        print("Screen captured.")

        # Convert the image to Base64
        buffered = io.BytesIO()
        # Determine format based on Pillow object type or save as JPEG/PNG
        image_format = "JPEG" # Or PNG
        screenshot.save(buffered, format=image_format)
        base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        print("Image encoded to Base64.")

        # Prepare the payload for OpenAI API
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format.lower()};base64,{base64_image}",
                            "detail": detail_level,
                        },
                    },
                ],
            }
        ]

        print(f"Sending screen image to GPT-4o (detail: {detail_level})...")
        # Call the OpenAI API
        completion = client.chat.completions.create(
            model="gpt-4o", # Ensure this model supports vision
            messages=messages,
            max_tokens=500 # Adjust max tokens as needed for description length
        )
        print("Received response from GPT-4o.")

        description = completion.choices[0].message.content
        return f"Screen Description (from GPT-4o):\n{description}"

    except ImportError:
         return "Error: Required library (Pillow or openai) not installed."
    except OpenAIError as e:
        return f"Error calling OpenAI API: {e}"
    except Exception as e:
        # Catch other potential errors (e.g., screen grab issues, encoding issues)
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return f"Error during screen description generation: {e}"

# # Example usage (uncomment to test directly)
# if __name__ == '__main__':
#     # Ensure OPENAI_API_KEY is set in your environment before running
#     print("Testing screen description tool...")
#     # Test by invoking the tool as LangChain would
#     # Pass arguments as a dictionary to invoke
#     # The default for user_prompt will be used if not specified
#     tool_input = {"detail_level": "low"}
#     # tool_input = {"user_prompt": "What applications are open?", "detail_level": "low"} # Example with custom prompt
#     result = describe_screen_content.invoke(tool_input)

#     print("\n--- Screen Description Test Result ---")
#     print(result)
#     print("-------------------------------------")