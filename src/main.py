from ollama import chat
from pydantic import BaseModel
import json
import yaml
from bs4 import BeautifulSoup
from tkinter import filedialog
import bookmarks_parser

# Define our tools
# When we define the tools, it's ideal to use type-hinting and docstrings
# So the agent knows what a function does when reading it off

def organize() -> str:
    """
    Get the user's bookmark file and begins taxonomy creation process.
    """

    print("[TOOL]: Prompting user for file")
    file_path: str = filedialog.askopenfilename(
        title="Select your bookmark file",
        filetypes=[("HTML files", "*.html")]
    )

    # Handle user pressing cancel or not uploading anything
    if file_path:
        try:
            bookmark_data = process_bookmark_data(file_path)
        except ValueError:
            return "User uploaded malformatted HTML file that does not match expected Netscape HTML format."
        
        pass
    else:
        return "User cancelled importing the bookmark file"

# System prompt to help give the LLM context
# Use parenthesized string so we can output in one line but code with
# multiple lines

system_prompt = (
    "You are a helpful browser bookmark assistant. You help the user organize "
    "their browser bookmarks. Your task is to develop a logical, clear, "
    "concise, and user-aligned bookmark taxonomy that classifies all of user's "
    "bookmarks."
)

# Initial chatbot greeting message

greeting_message = (
    "Hello! I am your personal bookmark organizer assistant. Type "
    "/organize to input a bookmark file, and I will generate a proposed "
    "taxonomy and classification for you. Alternatively, ask me to organize "
    "your files and I will call it for you!"
)

# Keep track of message history (LLMs don't "remember" past messages unless
# you manually specify them)

messages = [
    {
        "role": "system",
        "content": system_prompt
    },
    {
        "role": "assistant",
        "content": greeting_message
    }
]

# We need to define a tools dictionary because we cannot blindly trust that an
# LLM will call a tool that exists

available_functions = {
    "organize": organize
}

# At the same time, define a list of tools to pass in for each message
tools = [organize]

# General functions

def call_tools(tool_calls):
    print("tools called")
    for call in tool_calls:
        func = available_functions.get(call.function.name)

        # Ensure the toolcall exists

        if func is not None:
            print("specific tool called")
            print(call.function)
            result = func(**call.function.arguments)
        else:
            result = f"No tool with the name '{call.function.name}' was found."

        messages.append({
            "role": "tool",
            "tool_name": call.function.name,
            "content": str(result)
        })

def process_bookmark_data(file_path):
    with open(file_path, "r") as file:
        first_line = file.readline().strip()

        if first_line != "<!DOCTYPE NETSCAPE-Bookmark-file-1>":
            raise ValueError("File failed Netscape HTML checks. Check if file is valid Netscape HTML.")
            # Check failed
        
    try:
        return bookmarks_parser.parse(file_path)
    # Why catch Exception? bookmarks_parser doesn't have a dedicated validation feature for
    # netscape HTML, which means no dedicated exception for an invalid/malformatted HTML file.
    # This means it could throw any number of unpredictable exceptions. We'll isolate this
    # broad except Exception code specifically to processing data only.
    except Exception as e:
        raise ValueError("File failed Netscape HTML checks. Check if file is valid Netscape HTML.")

print(greeting_message)