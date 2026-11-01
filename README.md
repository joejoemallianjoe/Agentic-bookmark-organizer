# Agentic Bookmark Organizer
This is a simple agentic bookmark organizer using local LLMs with ollama and Python
Simple agentic bookmark organizer using local LLMs with ollama and Python

## The problem

I often find a lot of interesting articles, TV shows, tutorial resources, etc. that I know I might want to visit later, but I don't like to clutter my tabs, so I usually bookmark it and close the tab as quickly as possible. However, finding the correct place for the bookmark takes time, and I'm usually too lazy to do it. A few months later, when I remember some obscure resource I bookmarked, I search through my bookmarks, but I can't find it because I don't tremember which browser and/or which folder it was in.

## The goal

The goal of this project is to get an MVP agentic bookmark organizer that can take in bookmark data, process it, and then present a new taxonomy for approval.

## How it works

A local LLM is hooked up to Python using the ollama library. When the Python program is run, there will be an initial greeting message. Here, you can ask it to organize your bookmarks. It will then prompt you to enter your bookmarks file (must be in the Netscape HTML format or MS Edge JSON format), process it, brainstorm a new taxonomy, organize your bookmarks, and then present its proposed plan to you. You can then either respond with `/approve` or /`reject` to approve or reject the plan in the terminal line. 

## Tech Stack

- **Language:** Python
- **Libraries:** json, bs4, Pydantic, ollama
- **Local LLM:** Qwen3.5:4b

## Roadmap

- [ ] Pull real-time bookmarks without user needing to upload bookmark file
- [ ] Automatically replace bookmarks once approved without needing to generate export file
- [ ] Experiment with shorter/more concise file formats and prompts to save tokens
- [ ] Add "Uncertain" category to ask user follow-up questions
- [ ] Incorporate user responses from rejected plans to guide local LLM when drafting a new plan
