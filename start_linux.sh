#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
