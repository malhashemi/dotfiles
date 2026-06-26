#!/usr/bin/env bash
set -euo pipefail

pkill -x hypridle 2>/dev/null || true
exec hypridle
