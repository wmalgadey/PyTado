#!/bin/bash
set -e

# Abort if `venv` folder already exists
if [ -d ".venv" ]; then
    echo ".venv/ folder already exists. Deactivate your venv and remove .venv/ folder."
    exit 1
fi

# Create and activate a new virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install all projects and their dependencies
pip install --upgrade pip
pip install -e '.[all]'
