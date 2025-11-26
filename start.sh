#!/usr/bin/env bash
set -e

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi
source .venv/bin/activate

# Install uv and dependencies
pip install uv
uv sync

# Start the server
python run_server.py
