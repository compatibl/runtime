#!/usr/bin/env bash

if [ -f ".venv/bin/activate" ]; then
    echo "Monorepo configuration, activating venv from current directory"
    # shellcheck disable=SC1091
    source ".venv/bin/activate"
    return 0 2>/dev/null || exit 0
fi

if [ -f "../.venv/bin/activate" ]; then
    echo "Multirepo configuration, activating venv from parent directory"
    # shellcheck disable=SC1091
    source "../.venv/bin/activate"
    return 0 2>/dev/null || exit 0
fi

echo "ERROR: No .venv found in current or parent directory"
exit 1
