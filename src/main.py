from ollama import chat
from pydantic import BaseModel
import json
import yaml
import random
from collections import deque
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
import bookmarks_parser
from transformers import AutoTokenizer

# Define our tools
# When we define the tools, it's ideal to use type-hinting and docstrings
# So the agent knows what a function does when reading it off

def organize() -> str:
    """
    Get the user's bookmark file and begins taxonomy creation process.
    """

    print("[TOOL]: Prompting user for file")

    # Create a root to force the file opener window to go to front layer
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path: str = filedialog.askopenfilename(
        parent=root,
        title="Select your bookmark file",
        filetypes=[("HTML files", "*.html")]
    )

    root.destroy()


    # Handle user pressing cancel or not uploading anything
    if file_path:
        try:
            bookmark_data = process_bookmark_data(file_path)
        except ValueError:
            return "User uploaded malformatted HTML file that does not match expected Netscape HTML format."

        final_taxonomy = generate_final_taxonomy(bookmark_data)

        print(final_taxonomy)
    else:
        return "User cancelled importing the bookmark file"

# System prompt to help give the LLM context
# Use parenthesized string so we can output in one line but code with
# multiple lines

# If you change the model, change both
model = "qwen3.5:4b"
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-4B")

tokens_per_batch = 3000
context_window_size = 8192
planning_response_budget = 2000

system_prompt = (
    "You are a helpful browser bookmark assistant. You help the user organize "
    "their browser bookmarks. Your task is to develop a logical, clear, "
    "concise, and user-aligned bookmark taxonomy that classifies all of user's "
    "bookmarks."
)

# Initial chatbot greeting message

greeting_message = (
    f"[{model}]: Hello! I am your personal bookmark organizer assistant. Type "
    "/organize to input a bookmark file, and I will generate a proposed "
    "taxonomy and classification for you. Alternatively, ask me to organize "
    "your files and I will call it for you!"
)

# Intermediate planning prompt for chunks

initial_chunk_planning_prompt = (
    "A random, unorganized sample of bookmarks/bookmark folders has been provided. "
    "Your goal is to generate a taxonomy with cohesive, logical, precise, and comprehensive "
    "categories. Follow three phases: drafting, evaluation, and finalization.\n"
    "\n"
    "Phase 1: Drafting\n"
    "Brainstorm possible categories and sub-categories with justifications of why you chose "
    "certain categories and sub-categories.\n"
    "\n"
    "Phase 2: Evaluation\n"
    "Evaluate your current taxonomy. Decide whether merging, subcategorizing, removing, or moving "
    "categories is necessary, or if no change is needed. Additionally, consider if new categories "
    "are needed or not.\n"
    "\n"
    "Phase 3: Finalization\n"
    "Write your final taxonomy using your final set of categories. Underneath it, add a brief "
    "justification paragraph summarizing your core reasons for organizing it this way.\n"
    "\n"
    "Use concise, information-dense text. Use shorthand if possible."
)

intermediate_chunk_planning_addition = (
    "\n\nAdditionally, a previously planned taxonomy with justifications based on a different"
    "sample has been provided below. Build off this taxonomy. \n\n Previous taxonomy:"
)

final_chunk_planning_prompt = (
    "\n\nA carefully thought-out taxonomy with justifications has been provided. Extract the final "
    "taxonomy into a JSON format. Output only JSON."
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
    for call in tool_calls:
        func = available_functions.get(call.function.name)

        messages.append({
            "role": "assistant",
            "content": f"Called {call.function.name} tool. Args:\n" + 
                       "\n".join(f"{key}={value}" for key, value in call.function.arguments.items())
        })

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

def generate_final_taxonomy(validated_bookmark_python, tokens_per_batch=tokens_per_batch):
    def compute_token_count(obj):
        yaml_vers = yaml.dump(obj, sort_keys=False)
        return len(tokenizer.encode(yaml_vers))
    
    # My original idea was to take the raw bookmark data and strip out irrelevant
    # metadata to get a clean yaml format to feed into the LLM so its context window
    # doesn't get flooded, but doing this still leaves 15k-20k tokens, which
    # is far past its 4k token context window

    # Thus, we need a chunking approach. First, use DFS to flatten all the bookmarks
    # and folders into one list

    stack = deque()
    flattened_list = []

    # Append the top-level folders
    for node in reversed(validated_bookmark_python):
        stack.append((node, ""))

    while stack:
        node, parent_directory = stack.pop()

        current_directory = f"{parent_directory}/{node["title"]}"
        object_dict = {
            "type": "other",
            "name": node["title"],
            "directory": current_directory
        }

        # Due to weird browser-specific quirks, not all folders have "type": "folder", 
        # so having the key "children" is a sufficient proxy
        if node.get("children") is not None:
            object_dict["type"] = "folder"
            # Add its children to the stack

            for child in reversed(node["children"]):
                stack.append((child, current_directory))
        elif node.get("type") == "bookmark":
            object_dict["type"] = "bookmark"
            object_dict["url"] = node["url"]

        flattened_list.append(object_dict)

    # Randomly sample chunks to feed to the local LLM

    previous_chunk_taxonomy = None

    while len(flattened_list) > 0:
        batch = []
        current_total_tokens = 0

        while len(flattened_list) > 0:
            index = random.randrange(len(flattened_list))
            sample_token_count = compute_token_count(flattened_list[index])

            # Edge case if a bookmark object is somehow bigger than the total batch budget
            if sample_token_count > tokens_per_batch:
                print("Warning: Bookmark folder/object exceeded max token budget per batch. " + 
                      "Skipped bookmark folder/object.")
                continue
            elif current_total_tokens + sample_token_count > tokens_per_batch:
                break
            else:
                batch.append(flattened_list[index])
                flattened_list.pop(index)
                current_total_tokens += sample_token_count

        prompt = yaml.dump(batch, sort_keys=False) + initial_chunk_planning_prompt

        if previous_chunk_taxonomy:
            prompt += (intermediate_chunk_planning_addition + 
                       "\"\"\"\n" + previous_chunk_taxonomy + "\n\"\"\"")

        previous_chunk_taxonomy = message(
            prompt, 
            messages=messages[0:1],
            options={
                "num_ctx": context_window_size,
                "num_predict": planning_response_budget
            }
        )

    # Use pydantic or smth to validate this later
    final_taxonomy = message(
        "\"\"\"\n" + previous_chunk_taxonomy + "\n\"\"\"" + final_chunk_planning_prompt,
        messages=messages[0:1]
    )

    return final_taxonomy

def message(message: str = None, think:bool = False, messages=messages, options=None) -> str:
    if message is not None:
        messages.append({
            "role": "user",
            "content": message
        })

        print(f"[User]: {message}")

    while True:
        params = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "think": think
        }

        if options:
            params["options"] = options

        response = chat(**params)

        if not response.message.tool_calls:
            return response.message.content

        call_tools(response.message.tool_calls)

print(greeting_message)

organize()