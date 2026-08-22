#!/usr/bin/env python3

import json
import re
import sys


def deny(reason):
    print(json.dumps({"decision": "deny", "reason": reason}))
    sys.exit(2)


def allow():
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)


try:
    payload = json.load(sys.stdin)

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # This hook is primarily intended to protect shell commands.
    if tool_name != "run_command":
        allow()

    # AGY command argument names can vary by version.
    command = ""

    if isinstance(args, dict):
        for key in ("CommandLine", "commandLine", "command", "cmd"):
            if key in args:
                command = str(args[key])
                break

    if not command:
        allow()

    # Normalize whitespace.
    cmd = re.sub(r"\s+", " ", command).strip()

    # Files that must NEVER be deleted.
    protected_patterns = [
        r"(?:^|/|\\)[^/\s\\]*\.db(?:['\" ]|$)",
        r"(?:^|/|\\)\.env(?:\.[^/\s\\]+)?(?:['\" ]|$)",
    ]

    protected = any(
        re.search(pattern, cmd, re.IGNORECASE) for pattern in protected_patterns
    )

    if not protected:
        allow()

    # Detect common destructive operations.
    destructive_patterns = [
        r"\brm\b",
        r"\bunlink\b",
        r"\brmdir\b",
        r"\bfind\b.*(?:-delete|-exec\s+rm)",
        r"\bshred\b",
        r"\bgit\s+clean\b",
        r"\bdel\b",
        r"\bremove-item\b",
        r"\bRemove-Item\b",
    ]

    destructive = any(
        re.search(pattern, cmd, re.IGNORECASE) for pattern in destructive_patterns
    )

    if destructive:
        deny(
            "BLOCKED: This command attempts to delete a protected file. "
            "AGY is not allowed to delete .db files or .env files under any condition."
        )

    # Also block shell redirection/truncation targeting protected files.
    if re.search(r">\s*['\"]?[^ ]*(?:\.db|\.env(?:\.[^ ]+)?)", cmd, re.IGNORECASE):
        deny(
            "BLOCKED: This command attempts to overwrite/truncate a protected "
            ".db or .env file."
        )

    allow()

except Exception as exc:
    # Fail closed: if the hook cannot understand the command,
    # do NOT allow potentially destructive execution.
    print(
        json.dumps(
            {
                "decision": "deny",
                "reason": f"Security hook failed to inspect the command: {exc}",
            }
        )
    )
