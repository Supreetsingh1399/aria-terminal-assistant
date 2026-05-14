import os
import readline
import json
import subprocess
from datetime import datetime
from groq import Groq

# ── Colors ──────────────────────────────────────────
R = "\033[0m"        # reset
B = "\033[1m"        # bold
DIM = "\033[2m"      # dim
CYAN = "\033[96m"    # cyan
GREEN = "\033[92m"   # green
YELLOW = "\033[93m"  # yellow
RED = "\033[91m"     # red
WHITE = "\033[97m"   # white

# ── Setup ────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MEMORY_FILE = os.path.expanduser("~/.assistant_memory.json")
MODES = ["chat", "code", "cmd"]
current_mode = "chat"

MODE_PROMPTS = {
    "chat": "You are a helpful, concise AI assistant.",
    "code": (
        "You are an expert code assistant. "
        "When giving code, always explain what it does briefly. "
        "Format code cleanly."
    ),
    "cmd": (
        "You are a Linux/Android terminal expert running in Termux. "
        "When the user asks to run something, reply with exactly: RUN: <command>. "
        "Be careful with destructive commands — warn the user first."
    ),
}

# ── Memory ───────────────────────────────────────────
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history[-40:], f, indent=2)

# ── UI Helpers ───────────────────────────────────────
def divider():
    print(f"{DIM}{'─' * 40}{R}")

def header():
    os.system("clear")
    divider()
    print(f"{B}{WHITE}  ARIA — AI Terminal Assistant{R}")
    print(f"{DIM}  Model: llama-3.3-70b  |  Mode: {mode_label()}{R}")
    divider()
    print(f"{DIM}  Commands: /mode  /clear  /history  /exit{R}")
    divider()
    print()

def mode_label():
    colors = {"chat": CYAN, "code": GREEN, "cmd": YELLOW}
    return f"{colors[current_mode]}{current_mode.upper()}{R}"

def show_modes():
    divider()
    print(f"  Select mode:")
    print(f"  {CYAN}1. chat{R}  — General assistant")
    print(f"  {GREEN}2. code{R}  — Code helper")
    print(f"  {YELLOW}3. cmd{R}   — Terminal commands")
    divider()

def show_history(history):
    divider()
    if not history:
        print(f"  {DIM}No history yet.{R}")
    else:
        for msg in history[-10:]:
            if msg["role"] == "user":
                print(f"  {CYAN}You:{R} {msg['content'][:80]}")
            elif msg["role"] == "assistant":
                print(f"  {WHITE}ARIA:{R} {msg['content'][:80]}")
    divider()

# ── Main ─────────────────────────────────────────────
def build_history(memory):
    system = {"role": "system", "content": MODE_PROMPTS[current_mode]}
    return [system] + memory

def ask(history):
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=history,
        max_tokens=1024
    ).choices[0].message.content.strip()

def run_command(command):
    print(f"\n  {YELLOW}>{R} {B}{command}{R}")
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True
    )
    output = (result.stdout or result.stderr).strip()
    if output:
        print(f"\n{DIM}{output}{R}\n")
    else:
        print(f"  {DIM}(no output){R}\n")
    return output

def confirm(prompt):
    ans = input(f"  {RED}{prompt} (y/n):{R} ").strip().lower()
    return ans == "y"
MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
]

def ask(history):
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=history,
                max_tokens=1024
            )
            print(f"  {DIM}[{model}]{R}", end="\r")
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                print(f"  {DIM}{model} limit hit, trying next...{R}")
                continue
            raise
    return "All models are rate limited. Please wait 30 minutes."
# ── Run ──────────────────────────────────────────────
memory = load_memory()
header()

while True:
    try:
        prompt = input(f"{CYAN}>{R} ").strip()
    except KeyboardInterrupt:
        print(f"\n  {DIM}Bye.{R}\n")
        break

    if not prompt:
        continue

    # ── Built-in commands ──
    if prompt == "/exit":
        print(f"\n  {DIM}Bye.{R}\n")
        break

    elif prompt == "/clear":
        memory = []
        save_memory(memory)
        header()
        print(f"  {DIM}Memory cleared.{R}\n")
        continue

    elif prompt == "/history":
        show_history(memory)
        continue

    elif prompt == "/mode":
        show_modes()
        choice = input("  Choose (1/2/3): ").strip()
        mapping = {"1": "chat", "2": "code", "3": "cmd"}
        if choice in mapping:
            current_mode = mapping[choice]
            header()
        continue

    # ── AI response ──
    memory.append({"role": "user", "content": prompt})
    history = build_history(memory)

    print(f"  {DIM}thinking...{R}", end="\r")
    reply = ask(history)
    print(" " * 20, end="\r")

    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)

    # ── Command execution ──
    if reply.upper().startswith("RUN:"):
        command = reply[4:].strip()
        dangerous = any(w in command for w in ["rm ", "dd ", "mkfs", "chmod 777"])
        if dangerous:
            if not confirm(f"⚠ Dangerous command: {command}. Run anyway?"):
                print(f"  {DIM}Skipped.{R}\n")
                continue
        output = run_command(command)
        memory.append({"role": "user", "content": f"Command output: {output}"})
        save_memory(memory)
    else:
        divider()
        print(f"{WHITE}{reply}{R}")
        divider()
        print()
