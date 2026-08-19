# Git Commit

## Description

Stages all current changes and commits them using the provided commit message.

## Steps

1. Take the commit message provided as the parameter.
2. Run:
   `git add .`
3. Run:
   `git commit -m "<commit-message>"`
4. Report whether the commit succeeded or failed.

## Rules

- Accept one parameter: the commit message.
- Use the provided commit message as-is.
- Do not run `git push`.
- Do not create or switch branches.
- If no commit message is provided, ask for a commit message.

## Example

`/git-commit "Add expense filtering"`

The workflow should execute:

`git add .`

Then:

`git commit -m "Add expense filtering"`