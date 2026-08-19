#!/bin/bash

if [ -z "$1" ]; then
    echo "Error: Commit message is required."
    echo "Usage: ./git-commit.sh \"your commit message\""
    exit 1
fi

COMMIT_MESSAGE="$1"

git add .
git commit -m "$COMMIT_MESSAGE"