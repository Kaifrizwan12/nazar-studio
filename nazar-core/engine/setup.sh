#!/bin/zsh
# One-time setup: a local venv with the renderer. Needs Python 3.9+ and Cairo (brew install cairo).
cd "$(dirname "$0")"
python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt && echo "ready: .venv/bin/python build.py"
