#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v cargo >/dev/null || { printf '%s\n' 'Rust is required. On CachyOS install rust and base-devel.'; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check
cargo build --locked
exec .venv/bin/python gui/app.py "$@"
