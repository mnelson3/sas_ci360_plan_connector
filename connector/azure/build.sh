#!/bin/sh
# Copies the shared core/ package into this adapter before deployment.
# Azure Functions packages exactly this directory, so core/ must be
# physically present here at deploy time - it is not committed here
# (see .gitignore); connector/core is the single source of truth.
set -e
cd "$(dirname "$0")"
rm -rf core
cp -r ../core ./core
echo "core/ copied into connector/azure/. Now deploy with: func azure functionapp publish <app-name>"
