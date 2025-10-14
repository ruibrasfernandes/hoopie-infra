#!/bin/bash

# Ask for project to deploy in
if [ -z "$1" ]
then
      echo "please use: $0 {dev/stag/prod}"
      exit
fi

# GET Project Variables
case $1 in
    "stag")
        echo "Deploying in Staging environment"
        # source .env.stag
        ENV_FILE=".env.stag"

        ;;
    "dev")
        echo "Deploying in DEV environment"
        # source .env.dev
        ENV_FILE=".env.dev"
        ;;
    "prod")
        echo "Deploying in PROD environment"
        # source .env.prod
        ENV_FILE=".env.prod"
        ;;
    *)
        echo "Not possible to deploy in $1"
        exit
esac

# ... Adapting from "ENV_VAR=VALUE" to "export ENV_VAR=VALUE"

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        if [[ ! -z "$key" && ! "$key" =~ ^# ]]; then # Ensure key is not empty and not a comment
            export "$key=$value"
        fi
    done < "$ENV_FILE"
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

echo "Project: $GOOGLE_CLOUD_PROJECT"
echo "ProjectId: $PROJECT_ID"
echo "Location: $GOOGLE_CLOUD_LOCATION"
echo "Using Vertex AI: $GOOGLE_GENAI_USE_VERTEXAI"
echo "Staging Bucket: $STAGING_BUCKET"
echo "Environment: $ENVIRONMENT"

exit


echo

read -p "Are you sure you want to deploy in $1? (y/n) " answer

if [ $answer == 'n' ]
then
    echo FIM
    exit
fi

echo "##################################################
#   Deploying in Project: $PROJECT_ID
##################################################"

# gcloud config configurations activate $PROJECT_ID
# sleep 2
gcloud config set account $ACCOUNT
gcloud config set project $PROJECT_ID

gcloud builds submit  --region=europe-southwest1 \
    --substitutions _IMAGE_NAME="europe-southwest1-docker.pkg.dev/$PROJECT_ID/api/ops-api",_BUCKET_NAME=$PROJECT_ID-ops,_INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION_NAME \
    --config cloudbuild.yaml .