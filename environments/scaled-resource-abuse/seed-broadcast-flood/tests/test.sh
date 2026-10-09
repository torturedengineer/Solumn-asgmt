#!/bin/bash
set -uo pipefail
mkdir -p /logs/verifier
python3 /tests/grader.py
