#!/bin/bash
# Deploy to Google Cloud Run

PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="winjay-agent-os"
REGION="us-central1"

echo "Deploying Winjay Infrastructure to Cloud Run..."

# Build and push using Google Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME ../

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production,GEMINI_API_KEY=YOUR_API_KEY_HERE,WEBHOOK_SECRET=YOUR_SECURE_WEBHOOK_SECRET"

echo "Deployment complete! Ensure you set the real secrets in Cloud Run dashboard."
