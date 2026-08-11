#!/bin/bash
TOKEN="${GITHUB_TOKEN:-$1}"
if [ -z "$TOKEN" ]; then
    echo "Usage: GITHUB_TOKEN=your_token ./push_to_github.sh"
    exit 1
fi
git push "https://Fayez2016:${TOKEN}@github.com/Fayez2016/deepagent.git" main --force
