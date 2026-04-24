#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate 2>/dev/null
KEYCLOAK_MOCK=1 python app.py
