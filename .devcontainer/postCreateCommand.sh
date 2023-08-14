#!/usr/bin/bash

# npm install frontend
cd /workspaces/aws-bootcamp-cruddur-2023/frontend-react-js && npm update -g && npm i;

# backend pip requirements
cd /workspaces/aws-bootcamp-cruddur-2023/backend-flask && pip install -r requirements.txt;

# Postgresql
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc|sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" |sudo tee  /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install -y postgresql-client-13 libpq-dev

# Update rds security rules
export CODESPACES_IP=$(curl ifconfig.me)
source /workspaces/aws-bootcamp-cruddur-2023/bin/rds/update-sg-rule

# Fargate
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb

# Create Env for codespace
ruby "/workspaces/aws-bootcamp-cruddur-2023/bin/backend/generate-env-codespace"
ruby "/workspaces/aws-bootcamp-cruddur-2023/bin/frontend/generate-env-codespace"

# CDK
npm install aws-cdk -g