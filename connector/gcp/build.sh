#!/bin/sh
# Copies the shared core/ package into this adapter before deploying.
# connector/core is the single source of truth; this copy is gitignored.
set -e
cd "$(dirname "$0")"
rm -rf core
cp -r ../core ./core
echo "core/ copied into connector/gcp/. Now deploy each function, e.g.:"
echo "  gcloud functions deploy create-offer --gen2 --runtime=python311 \\"
echo "    --entry-point=create_offer --trigger-http --env-vars-file=.env.yaml"
