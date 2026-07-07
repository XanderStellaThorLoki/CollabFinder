#!/usr/bin/env bash
# Deploy the CollabFinder MCP server to Cloud Run.
# Usage: ./scripts/deploy.sh [project-id] [region]
set -euo pipefail

PROJECT="${1:-${GCP_PROJECT:-collabfinder-hack-2026}}"
REGION="${2:-us-central1}"
SERVICE="collabfinder-mcp"

echo "Deploying ${SERVICE} to ${PROJECT}/${REGION}..."
gcloud run deploy "${SERVICE}" \
  --source=. \
  --project="${PROJECT}" \
  --region="${REGION}" \
  --allow-unauthenticated \
  --memory=512Mi \
  --set-env-vars="SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:?export SLACK_BOT_TOKEN first}"

echo
echo "MCP endpoint: $(gcloud run services describe "${SERVICE}" \
  --project="${PROJECT}" --region="${REGION}" --format='value(status.url)')/mcp"
