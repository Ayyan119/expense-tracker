#!/usr/bin/env python3
"""
Black Code Formatter Lifecycle Hook for Antigravity.
Automatically formats Python files after write_to_file or replace_file_content tools.
"""

import json
import os
import shutil
import subprocess
import sys


def find_black_executable():
    # 1. Check PATH
    exe = shutil.which("black")
    if exe:
        return exe
    # 2. Check local user bin
    user_black = os.path.expanduser("~/.local/bin/black")
    if os.path.isfile(user_black) and os.access(user_black, os.X_OK):
        return user_black
    # 3. Check virtualenv bin
    venv_black = os.path.join(os.getcwd(), ".venv", "bin", "black")
    if os.path.isfile(venv_black) and os.access(venv_black, os.X_OK):
        return venv_black
    return None


def main():
    try:
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read()
            if not raw_input.strip():
                print(json.dumps({}))
                return
            payload = json.loads(raw_input)
        else:
            payload = {}
    except Exception:
        print(json.dumps({}))
        return

    tool_call = payload.get("toolCall", {})
    args = tool_call.get("args", {})
    if not isinstance(args, dict):
        print(json.dumps({}))
        return

    # Extract target file path from potential keys
    target_file = None
    for key in (
        "TargetFile",
        "targetFile",
        "target_file",
        "FilePath",
        "filePath",
        "file_path",
        "file",
    ):
        if key in args and isinstance(args[key], str):
            target_file = args[key]
            break

    # If no file found or not a Python file, pass through
    if not target_file or not target_file.endswith(".py"):
        print(json.dumps({}))
        return

    if not os.path.exists(target_file):
        print(json.dumps({}))
        return

    black_bin = find_black_executable()
    if not black_bin:
        print(
            f"\n⚠️  [Black Hook] Triggered for '{target_file}', but 'black' executable was not found.",
            file=sys.stderr,
        )
        print(json.dumps({}))
        return

    # Notify that hook is triggered
    print(
        f"\n✨ [Black Formatter Hook] 🚀 Triggered on: {target_file}", file=sys.stderr
    )

    try:
        result = subprocess.run(
            [black_bin, target_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stderr:
            msg = result.stderr.strip()
            print(f"✨ [Black Formatter Hook] {msg}", file=sys.stderr)
        elif result.stdout:
            msg = result.stdout.strip()
            print(f"✨ [Black Formatter Hook] {msg}", file=sys.stderr)
        else:
            print(
                f"✨ [Black Formatter Hook] Successfully formatted {target_file}",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"⚠️  [Black Hook] Error running black: {e}", file=sys.stderr)

    # PostToolUse contract requires a valid JSON object on stdout
    print(json.dumps({}))


if __name__ == "__main__":
    main()
