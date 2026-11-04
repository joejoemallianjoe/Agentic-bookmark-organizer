from ollama import chat
from pydantic import BaseModel
import json
from bs4 import BeautifulSoup

# Define our tools

def organize() -> str:
    """
    Get the user's bookmark file and begins taxonomy creation process.
    """
    pass

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

tools = [organize]

# Functions

def call_tools(tool_calls):
    for call in tool_calls:
        func = available_functions.get(call.function.name)

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