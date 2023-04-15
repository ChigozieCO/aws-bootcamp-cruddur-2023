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
source /workspaces/aws-bootcamp-cruddur-2023/backend-flask/bin/rds/update-sg-rule