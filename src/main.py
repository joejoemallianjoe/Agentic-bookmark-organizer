from ollama import chat
from pydantic import BaseModel
import json
from bs4 import BeautifulSoup

# Initial chatbot greeting message
# Use parenthesized string so we can output in one line but code with
# multiple lines

system_prompt = (
    "You are a helpful browser bookmark assistant. You help the user organize "
    "their browser bookmarks. Your task is to develop a logical, clear, "
    "concise, and user-aligned bookmark taxonomy that classifies all of user's "
    "bookmarks."
)

greeting_message = (
    "Hello! I am your personal bookmark organizer assistatnt. Type "
    "/organize to input a bookmark file, and I will generate a proposed "
    "taxonomy and classification for you. Next, you can type /approve or "
    "/reject to approve or reject my plan. If you approve, then I will "
    "generate an export bookmark file and output its directory for you. "
    "Start: type /organize"
)

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

print(greeting_message)