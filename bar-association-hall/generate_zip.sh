#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
zip -r bar-association-hall.zip bar-association-hall -x "*.DS_Store" "bar-association-hall/generated/*"
echo "Created: $(pwd)/bar-association-hall.zip"
