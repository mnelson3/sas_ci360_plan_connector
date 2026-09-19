#!/bin/sh
# Copies the shared core/ package into this adapter before `sam build`.
# connector/core is the single source of truth; this copy is gitignored.
set -e
cd "$(dirname "$0")"
rm -rf core
cp -r ../core ./core
echo "core/ copied into connector/aws/. Now run: sam build && sam deploy --guided"
