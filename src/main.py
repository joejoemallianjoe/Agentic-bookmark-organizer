from ollama import chat
from pydantic import BaseModel
import json
from bs4 import BeautifulSoup
from tkinter import filedialog

# Define our tools
# When we define the tools, it's ideal to use type-hinting and docstrings
# So the agent knows what a function does when reading it off

def organize() -> str:
    """
    Get the user's bookmark file and begins taxonomy creation process.
    """

    # Ask the user to import their bookmark file
    file_path = filedialog.askopenfilename(
        title="Select your bookmark file",
        filetypes=[("JSON files", "*.json"), ("HTML files", "*.html"), 
                   ("All files", "*.*")]
    )

    # Handle user pressing cancel or not uploading anything
    if file_path:
        # If the user does specify something, file_path will be a string
        # to the file
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

# Functions

def call_tools(tool_calls):
    for call in tool_calls:
        func = available_functions.get(call.function.name)

        # Ensure the toolcall exists

        if func is not None:
            result = func(**call.function.arguments)
        else:
            result = f"No tool with the name '{call.function.name}' was found."

        messages.append({
            "role": "tool",
            "tool_name": call.function.name,
            "content": str(result)
        })

print(greeting_message)