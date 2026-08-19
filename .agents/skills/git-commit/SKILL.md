---

name: git-commit
description: Creates a Git commit by staging all changes with git add . and committing them with a user-provided commit message. Use when the user asks to commit current changes or perform git add and git commit.
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Git Commit Skill

## Purpose

This skill handles the standard Git commit workflow:

1. Stage all changes using `git add .`
2. Commit the staged changes using `git commit -m "<commit message>"`

## When to use

Use this skill when the user asks to:

* Commit the current changes.
* Run `git add .` and `git commit`.
* Create a Git commit with a specific commit message.

## Workflow

### Step 1 — Check Git status

Run:

```bash
git status
```

Check what files have changed before staging.

### Step 2 — Stage all changes

Run:

```bash
git add .
```

This stages all new, modified, and deleted files under the current repository directory.

### Step 3 — Get the commit message

If the user provided a commit message, use it exactly.

Example:

```text
git commit -m "Fix login authentication"
```

If the user did not provide a commit message, ask them for one.

### Step 4 — Create the commit

Run:

```bash
git commit -m "<user-provided-message>"
```

Do not invent or modify the user's commit message unless necessary for shell escaping.

### Step 5 — Verify the result

After committing, run:

```bash
git status
git log -1 --oneline
```

Report the commit result to the user.

## Important rules

* Do not run `git push` automatically.
* Do not create a new branch.
* Do not modify the user's files as part of this skill.
* Do not use `git add -A` or `git add --all`; use exactly `git add .`.
* Do not invent a commit message.
* If the commit fails, explain the error and do not claim that the commit succeeded.
* If there are no changes to commit, tell the user that there is nothing to commit.
* Preserve the user's intended commit message.

## Example

User:

```text
Commit my changes with message "Add expense filtering"
```

The agent should execute:

```bash
git status
git add .
git commit -m "Add expense filtering"
git status
git log -1 --oneline
```

The skill is complete when the commit has either succeeded or the actual Git error has been reported.
