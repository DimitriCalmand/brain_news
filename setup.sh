#!/bin/bash
# setup.sh — Run once to initialize the git repo for brain_news
# Usage: bash setup.sh <your-github-repo-url>
# Example: bash setup.sh https://github.com/yourusername/brain_news.git

set -e

REMOTE_URL="${1:-}"

if [ -z "$REMOTE_URL" ]; then
  echo "Usage: bash setup.sh <github-repo-url>"
  echo "Example: bash setup.sh https://github.com/yourusername/brain_news.git"
  exit 1
fi

echo "→ Initializing git repo..."
git init
git branch -M main

echo "→ Adding remote: $REMOTE_URL"
git remote add origin "$REMOTE_URL"

echo "→ Initial commit..."
git add .
git commit -m "chore: initial brain_news project setup"

echo "→ Pushing to main..."
git push -u origin main

echo ""
echo "✅ Done! The brain_news repo is live at: $REMOTE_URL"
echo ""
echo "Next step: run 'claude' in this folder to kick off the first news fetch."
