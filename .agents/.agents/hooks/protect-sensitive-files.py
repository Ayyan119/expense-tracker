#!/usr/bin/env python3
import json
import re
import sys


def should_deny(tool_name, args):
    if not isinstance(args, dict):
        return False, ""

    # 1. Inspect command execution (run_command, bash, shell, terminal, etc.)
    if tool_name in ("run_command", "bash", "execute_command", "terminal"):
        command = args.get("CommandLine") or args.get("command") or ""
        if not command:
            return False, ""

        # Check direct mentions of my.db with deletion / destructive actions
        if "my.db" in command:
            destructive_patterns = [
                r"\brm\b",
                r"\bunlink\b",
                r"\bshred\b",
                r"\btruncate\b",
                r"\bmv\b",
                r"\btrash\b",
                r"\bdel\b",
                r"\berase\b",
                r"\bwipe\b",
                r"\bclean\b",
                r">",
                r"os\.remove",
                r"os\.unlink",
                r"\.unlink\(",
                r"shutil\.rmtree",
                r"DROP\s+TABLE",
                r"DROP\s+DATABASE",
                r"VACUUM",
            ]
            for pattern in destructive_patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return (
                        True,
                        f"Action blocked by safety hook: Command attempts to delete, move, or modify protected database file 'my.db'.",
                    )

        # Check deletion targeting the parent database directory
        if re.search(
            r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+.*database(/|\b)", command, re.IGNORECASE
        ):
            return (
                True,
                "Action blocked by safety hook: Recursive deletion of 'database/' directory would delete 'my.db'.",
            )

        # Check find ... -delete targeting db files
        if re.search(r"\bfind\b.*-delete", command, re.IGNORECASE) and (
            "db" in command or "database" in command
        ):
            return (
                True,
                "Action blocked by safety hook: Find command with -delete flag targeting database files.",
            )

    # 2. Inspect file writing / overwriting tools
    if tool_name in (
        "write_to_file",
        "create_file",
        "edit_file",
        "replace_file_content",
    ):
        target = (
            args.get("TargetFile")
            or args.get("target_file")
            or args.get("file_path")
            or args.get("path")
            or ""
        )
        if "my.db" in target:
            return (
                True,
                f"Action blocked by safety hook: Tool '{tool_name}' attempted to overwrite protected database file 'my.db'.",
            )

    # 3. Direct inspection of all arg values for any explicit deletion of my.db
    for k, v in args.items():
        if isinstance(v, str) and "my.db" in v:
            if re.search(
                r"\b(rm|unlink|shred|delete|truncate|remove)\b", v, re.IGNORECASE
            ):
                return (
                    True,
                    f"Action blocked by safety hook: Parameter '{k}' contains deletion command targeting 'my.db'.",
                )

    return False, ""


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    deny, reason = should_deny(tool_name, args)

    if deny:
        response = {"decision": "deny", "reason": reason}
    else:
        response = {"decision": "allow"}

    print(json.dumps(response))


if __name__ == "__main__":
    main()
