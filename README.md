# ARIA — AI Terminal Assistant

An AI-powered terminal assistant built in Python, running on Android via Termux.

## Features
- 3 modes: Chat, Code Helper, Command Mode
- Auto-runs terminal commands
- Remembers conversation history
- Auto-switches models when rate limited

## Setup
1. Install dependencies
   pip install groq --no-build-isolation --prefer-binary
   pip install httpx anyio distro sniffio typing-extensions --prefer-binary

2. Get free API key from https://console.groq.com

3. Set your key
   export GROQ_API_KEY="your-key-here"

4. Run
   python assistant.py

## Built with
- Python
- Groq API (free)
- LLaMA 3.3 70B
- Built entirely on Android using Termux
