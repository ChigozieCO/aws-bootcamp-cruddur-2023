# Week 6 — Deploying Containers & Solving CORS with a Load Balancer and Custom Domain

This week we moved our app and app resources to AWS, we stored our app images in the AWS ECR, created hosted zones for the custom domains we are hosting the app on. We created a load balancer and so many other sweet stuff that is explained in detail in this week's journal.

# Health Check

We started this week by creating a health check. This is necessary to allow us accurately tell the health of our containers at any point.

The health check code was added to our `app.py` code as seen below:

```py
@app.route('/api/health-check')
def health_check():
  return {'success': True}, 200
```

Then I created a health check script to better define our health check.

```py
#!/usr/bin/env python3

import urllib.request

try:
  response = urllib.request.urlopen('http://localhost:4567/api/health-check')
  if response.getcode() == 200:
    print("[OK] Flask server is running")
    exit(0) # success
  else:
    print("[BAD] Flask server is not running")
    exit(1) # false
# This for some reason is not capturing the error....
#except ConnectionRefusedError as e:
# so we'll just catch on all even though this is a bad practice
except Exception as e:
  print(e)
  exit(1) # false
```

# Test RDS Connection

Next we wrote a python script that would be used to test our connection to our RDS instance when necessary.

The script is located at `backend-flask/bin/db/test`

```py
#!/usr/bin/env python3

import psycopg
import os
import sys

connection_url = os.getenv("CONNECTION_URL")

conn = None
try:
  print('attempting connection')
  conn = psycopg.connect(connection_url)
  print("Connection successful!")
except psycopg.Error as e:
  print("Unable to connect to the database:", e)
finally:
  conn.close()
```

# ECS Cluster

Before we started building our images and pushing them to AWS ECR, I created an ECS cluster through the cli. This is the code that wa used:

```
aws ecs create-cluster \
--cluster-name cruddur \
--service-connect-defaults namespace=cruddur
```

![ECS-cluster](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/15a98465-496d-4349-92bc-8dacd42e813c)

# Pushing Images

To start interacti ng with the AWS ECR from the cli, we must log into the ecr and so this was the first thing I did, using the command below:

At first I had an error as a result of not having set my account id variable but after setting it I was able to login

```
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
```

Owing to the fact that we are loosely coupling our app, which is why it has been broken into the frontend and backend and be have our codes broken into different file code instead of having all the code lumped into one thereby making it hard to read, we have the frontend and backend image.

Our backend image uses a python base image which we had previously been pulling from docker hub. However we will save that base image in our ECR so that when next we use our backend we will pull the base image directly from AWS and no longer from docker hub.

To this effect we would have 3 repos in ECR, the python image, our backebnd image and our frontend image.

### Pushing the Python Image

First I created a private repo on ecr 

```
aws ecr create-repository \
  --repository-name cruddur-python \
  --image-tag-mutability MUTABLE
```
  
Next thing was to set the path for the repo to push our image to.

The below command set the path and output it to confirm that it had been correctly set.

```
export ECR_PYTHON_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/cruddur-python"
echo $ECR_PYTHON_URL
```

Now I was ready to pull down the python image from dockler hub.

```
docker pull python:3.10-slim-buster
```

![Python-image](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/920dde3b-b611-4efc-933d-ccd50a5a17c0)

Next we tag the image with our previous set path

```
docker tag python:3.10-slim-buster $ECR_PYTHON_URL:3.10-slim-buster
```

Then we push it

```
docker push $ECR_PYTHON_URL:3.10-slim-buster
```

![PushImg1](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/eab2809c-c774-44b6-b3bb-4f96fce3a8f1)

### Push Backend Image

Because the source of the base image had changed (we are now pulling the image from ECR and not docker hub anymore) I need to update the backend Dockerfile to pull the base image from AWS ECR instead of docker hub.

Seeing that I did not want to expose my aws account ID I added a context to the [`docker-compose`](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/blob/acc4d2a31e96c80995801a131072e01f548fe65b/docker-compose.yml) file where I defined the base image as

```yml
    build: 
      context: ./backend-flask
      args:
        baseimage: "${ECR_PYTHON_URL}:3.10-slim-buster"
```

I then added an argument in the `backend-flask/Dockerfile` to use the baseimage I define in the docker-compose file

```
ARG baseimage
FROM ${baseimage}
```

Next step was to create a repo for the backend-flask image

```
aws ecr create-repository \
  --repository-name backend-flask \
  --image-tag-mutability MUTABLE
```

Set the url and confirm it was properly set

```
export ECR_BACKEND_FLASK_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/backend-flask"
echo $ECR_BACKEND_FLASK_URL
```

Finally I built the image.

To build this image I made sure to specify the build argument I added to the dockerfile so as to build the image with the appropriate base image.

```
docker build -t backend-flask --build-arg baseimage=$ECR_PYTHON_URL:3.10-slim-buster . 
```

![BuildingBkend1](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/9919e320-2c86-42b4-9b2e-31d6280e3de2)

![BuildingBkend2](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/5405793d-2467-47b3-909b-bbdf613e9764)

Next we tag and push the image

```
docker tag backend-flask:latest $ECR_BACKEND_FLASK_URL:latest
docker push $ECR_BACKEND_FLASK_URL:latest
```

![Pushimg2](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/0d815015-d61b-419d-9d74-ab05a1f2000f)

# Set Parameter store

We will save our secrets using the parameter store. We are opting to use the parameter store instead of the secrets manager because it is free whereas secret manager isn't.

We are setting the parameters as secureStrings so that it is encrypted server side.

We'll do this via the cli as usual. using the below code, we set the following parameters

```
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_ACCESS_KEY_ID" --value $AWS_ACCESS_KEY_ID
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY" --value $AWS_SECRET_ACCESS_KEY
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/CONNECTION_URL" --value $PROD_CONNECTION_URL
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" --value $ROLLBAR_ACCESS_TOKEN
aws ssm put-parameter --type "SecureString" --name "/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" --value "x-honeycomb-team=$HONEYCOMB_API_KEY"
```

![parastore](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/10e202a9-0d63-4222-b1fc-c3b2f3538eca)

![ParaStore2](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/8ffa9679-0d1b-4826-9860-226d2b2e0b62)

# Execution Roles & Task Definition 

To run our containers we either start a task or a service. The main difference between a task and a service is that a task kills itself once it executes and finishes whereas a service keeps continuously running. A service is a task that continuously runs.

A task is better suited for batch jobs and the likes and a service is suited for web apps which is what we are running and this is why we would create services when we need to.

In other create a service though, we need to have a task definition because it would be used to create the service. So this is what we do here. We will be creating task and execution roles for our task defintion.

Our Task definition file is basically like our docker compose file, it says how we provision our services.

### `CruddurServiceExecutionRole`

I created different files of the policy definition and execution roles

### `aws/policies/service-assume-role-execution-policy.json`

```json
{
  "Version":"2012-10-17",
  "Statement":[{
    "Action":["sts:AssumeRole"],
    "Effect":"Allow",
    "Principal":{
      "Service":["ecs-tasks.amazonaws.com"]
    }
  }]
}
```

### `aws/policies/service-execution-policy.json`

```json
{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters",
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:us-east-1:<aws account id>:parameter/cruddur/backend-flask/*"
    }]
  }
```

This file is then passed with the create command below in the cli

```sh
aws iam create-role \
    --role-name CruddurServiceExecutionRole \
    --assume-role-policy-document file://aws/policies/service-assume-role-execution-policy.json
```

```sh
aws iam put-role-policy \
    --policy-name CruddurServiceExecutionPolicy \
    --role-name CruddurServiceExecutionRole  \
    --policy-document file://aws/policies/service-execution-policy.json 
```

![ServiceExecRole](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/5bea3a3f-b058-4646-9173-6b3fedaee061)

### `CruddurTaskRole`

Next I created the task role via the cli using the command below

```sh
aws iam create-role \
    --role-name CruddurTaskRole \
    --assume-role-policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[\"sts:AssumeRole\"],
    \"Effect\":\"Allow\",
    \"Principal\":{
      \"Service\":[\"ecs-tasks.amazonaws.com\"]
    }
  }]
}"
```

Attach a policy 

```sh
aws iam put-role-policy \
  --policy-name SSMAccessPolicy \
  --role-name CruddurTaskRole \
  --policy-document "{
  \"Version\":\"2012-10-17\",
  \"Statement\":[{
    \"Action\":[
      \"ssmmessages:CreateControlChannel\",
      \"ssmmessages:CreateDataChannel\",
      \"ssmmessages:OpenControlChannel\",
      \"ssmmessages:OpenDataChannel\"
    ],
    \"Effect\":\"Allow\",
    \"Resource\":\"*\"
  }]
}
"
```

```sh
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess --role-name CruddurTaskRole
aws iam attach-role-policy --policy-arn arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess --role-name CruddurTaskRole
```

### Task Definition

Now it was time to create the task definiton for the backend container.

First I saved the definition policy in my file name `backend-flask.json` in the `aws/task-definitions/` directory

```json
{
    "family": "backend-flask",
    "executionRoleArn": "arn:aws:iam::<redacted>:role/CruddurServiceExecutionRole",
    "taskRoleArn": "arn:aws:iam::<redacted>:role/CruddurTaskRole",
    "networkMode": "awsvpc",
    "cpu": "256",
    "memory": "512",
    "requiresCompatibilities": [ 
      "FARGATE" 
    ],
    "containerDefinitions": [
      {
        "name": "backend-flask",
        "image": "<redacted>.dkr.ecr.<region>.amazonaws.com/backend-flask",
        "essential": true,
        "healthCheck": {
          "command": [
            "CMD-SHELL",
            "python /backend-flask/bin/flask/health-check"
          ],
          "interval": 30,
          "timeout": 5,
          "retries": 3,
          "startPeriod": 60
        },
        "portMappings": [
          {
            "name": "backend-flask",
            "containerPort": 4567,
            "protocol": "tcp", 
            "appProtocol": "http"
          }
        ],
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
              "awslogs-group": "cruddur",
              "awslogs-region": "<region>",
              "awslogs-stream-prefix": "backend-flask"
          }
        },
        "environment": [
          {"name": "OTEL_SERVICE_NAME", "value": "backend-flask"},
          {"name": "OTEL_EXPORTER_OTLP_ENDPOINT", "value": "https://api.honeycomb.io"},
          {"name": "AWS_COGNITO_USER_POOL_ID", "value": "<redacted>"},
          {"name": "AWS_COGNITO_USER_POOL_CLIENT_ID", "value": "<redacted>"},
          {"name": "FRONTEND_URL", "value": "*"},
          {"name": "BACKEND_URL", "value": "*"},
          {"name": "AWS_DEFAULT_REGION", "value": "<region>"}
        ],
        "secrets": [
          {"name": "AWS_ACCESS_KEY_ID"    , "valueFrom": "arn:aws:ssm:<region>:<redacted>:parameter/cruddur/backend-flask/AWS_ACCESS_KEY_ID"},
          {"name": "AWS_SECRET_ACCESS_KEY", "valueFrom": "arn:aws:ssm:<region>:<redacted>:parameter/cruddur/backend-flask/AWS_SECRET_ACCESS_KEY"},
          {"name": "CONNECTION_URL"       , "valueFrom": "arn:aws:ssm:<region>:<redacted>:parameter/cruddur/backend-flask/CONNECTION_URL" },
          {"name": "ROLLBAR_ACCESS_TOKEN" , "valueFrom": "arn:aws:ssm:<region>:<redacted>:parameter/cruddur/backend-flask/ROLLBAR_ACCESS_TOKEN" },
          {"name": "OTEL_EXPORTER_OTLP_HEADERS" , "valueFrom": "arn:aws:ssm:<region>:<redacted>:parameter/cruddur/backend-flask/OTEL_EXPORTER_OTLP_HEADERS" }
        ]
      }
    ]
  }
```

This policy document was then used to register the task definition with the below command:

```sh
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/backend-flask.json
```

# Create Backend Service

Before creating the service I created a security group that will be used by the service.

First I set my default VPC as an env var using the command:

```sh
export DEFAULT_VPC_ID=$(aws ec2 describe-vpcs \
--filters "Name=isDefault, Values=true" \
--query "Vpcs[0].VpcId" \
--output text)
echo $DEFAULT_VPC_ID
```

Then I used the below command to create the security group.

```sh
export CRUD_SERVICE_SG=$(aws ec2 create-security-group \
  --group-name "crud-srv-sg" \
  --description "Security group for Cruddur services on ECS" \
  --vpc-id $DEFAULT_VPC_ID \
  --query "GroupId" --output text)
echo $CRUD_SERVICE_SG
```

Now I went ahead to create the service.

I initially created the backend service through the cli but I had to delete it as a result of the inability to shell into it as it didn't have the execute command enabled and that can only be set through the cli.

![ConsleDeply](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/65e881f0-49a6-4959-afd3-11369cd7862d)

### Creating service through the cli

First I created and saved a file with the configuration commands so as to run the commands through the file.

### `aws/json/service-backend-flask.json`

```json
{
    "cluster": "cruddur",
    "launchType": "FARGATE",
    "desiredCount": 1,
    "enableECSManagedTags": true,
    "enableExecuteCommand": true,
    "networkConfiguration": {
      "awsvpcConfiguration": {
        "assignPublicIp": "ENABLED",
        "securityGroups": [
          "sg-<redacted>"
        ],
        "subnets": [
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>"
        ]
      }
    },
    "propagateTags": "SERVICE",
    "serviceName": "backend-flask",
    "taskDefinition": "backend-flask",
    "serviceConnectConfiguration": {
        "enabled": true,
        "namespace": "cruddur",
        "services": [
          {
            "portName": "backend-flask",
            "discoveryName": "backend-flask",
            "clientAliases": [{"port": 4567}]
          }
        ]
      }
  }
```

I could then use the below command to create the service through the cli

```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```

![Workng Container](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/10d1abb3-d269-4bb4-979f-cb54fca7f219)

Healthy container

![Health Container](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/09fccb03-6a07-4d52-ae56-b8d552229773)

# Install Sessions Manager

I installed sessions manager to enable us shell into the container to test the service.

```sh
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

Verify it works

```
session-manager-plugin
```

![sessionmgr](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/c6a5c05b-6dc4-41d0-b499-0cc093bb88cb)

This was also added to my `gitpod.yml` and my `postCreateCommand.sh` files so that when next my code environments are launched the sessions manager is installed in that environment.

For Gitpod

```yml
  - name: fargate
    before: |
      curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
      sudo dpkg -i session-manager-plugin.deb
      cd backend-flask
```

For Codespaces

```sh
# Fargate
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

# Connect to the container

Using the below command, I connected to the service and got a bash shell

```
aws ecs execute-command  \
--region $AWS_DEFAULT_REGION \
--cluster cruddur \
--task 1ebdab5b643d42cab1429199aa48a127 \
--container backend-flask \
--command "/bin/bash" \
--interactive
```

![bashShell](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/c43ec29e-4178-4dc7-b765-5be1d3dd186b)

To simplify the process and automate it for future use, I created a script to help connect to the ecs service. This script will then be passed in the command whenever I want to connect to the service.

The contents of the script is below:

```sh
#!/usr/bin/bash

if [ -z "$1" ]; then
  echo "No TASK_ID argument supplied eg ./bin/ecs/connect-to-backend-flask 1ebdab5b643d42cab1429199aa48a127"
  exit 1
fi
TASK_ID=$1

CONTAINER_NAME=backend-flask

echo "Task ID: $TASK_ID"
echo "Container name: $CONTAINER_NAME"

aws ecs execute-command  \
--region $AWS_DEFAULT_REGION \
--cluster cruddur \
--task $TASK_ID \
--container $CONTAINER_NAME \
--command "/bin/bash" \
--interactive
```

# Load Balancer 

The load balancer was created through the management console.

- From Compute, click on EC2
- In the EC2 console, select Load Balancers from the list of features on the right.
- Click on `create` on the Application Load Balancer option.
- Enter the `Load Balancer name`
- Leave it as `internet facing` scheme and `ipv4` Ip address type.
- In the Network Mapping section, select the VPC you would like to use.
- Then select all the AZs (which will select the subnets as well) under the vpc.
- Select your security group, if you dont yet have the one you'd like to use create a new one (which was what we did here).
- Next we create a target group if it doesn't already exist.
- I connected my backend and frontend load balancers
- Click `create load balancer`.

![loadblcnr](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/3a404b68-65fd-49b5-8297-6a5ec4b21623)

# Push Frontend Image

I set the frontend url

```sh
export ECR_FRONTEND_REACT_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/frontend-react-js"
echo $ECR_FRONTEND_REACT_URL
```

I created a task definition file for my frontend react app. The file contains the below:

```json
{
  "family": "frontend-react-js",
  "executionRoleArn": "arn:aws:iam::<redacted>:role/CruddurServiceExecutionRole",
  "taskRoleArn": "arn:aws:iam::<redacted>:role/CruddurTaskRole",
  "networkMode": "awsvpc",
  "cpu": "256",
  "memory": "512",
  "requiresCompatibilities": [ 
    "FARGATE" 
  ],
  "containerDefinitions": [
    {
      "name": "frontend-react-js",
      "image": "<redacted>.dkr.ecr.us-east-1.amazonaws.com/frontend-react-js",
      "essential": true,
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:3000 || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      },
      "portMappings": [
        {
          "name": "frontend-react-js",
          "containerPort": 3000,
          "protocol": "tcp", 
          "appProtocol": "http"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": "cruddur",
            "awslogs-region": "us-east-1",
            "awslogs-stream-prefix": "frontend-react-js"
        }
      }
    }
  ]
}
```

Next I created a production docker file `Dockerfile.prod`

```sh
# Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM node:16.18 AS build

ARG REACT_APP_BACKEND_URL
ARG REACT_APP_AWS_PROJECT_REGION
ARG REACT_APP_AWS_COGNITO_REGION
ARG REACT_APP_AWS_USER_POOLS_ID
ARG REACT_APP_CLIENT_ID

ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV REACT_APP_AWS_PROJECT_REGION=$REACT_APP_AWS_PROJECT_REGION
ENV REACT_APP_AWS_COGNITO_REGION=$REACT_APP_AWS_COGNITO_REGION
ENV REACT_APP_AWS_USER_POOLS_ID=$REACT_APP_AWS_USER_POOLS_ID
ENV REACT_APP_CLIENT_ID=$REACT_APP_CLIENT_ID

COPY . ./frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
RUN npm run build

# New Base Image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
FROM nginx:1.23.3-alpine

# --from build is coming from the Base Image
COPY --from=build /frontend-react-js/build /usr/share/nginx/html
COPY --from=build /frontend-react-js/nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
```

I then created an `nginx.conf` file because we will use nginx to build out our static assets.

```conf
# Set the worker processes
worker_processes 1;

# Set the events module
events {
  worker_connections 1024;
}

# Set the http module
http {
  # Set the MIME types
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  # Set the log format
  log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

  # Set the access log
  access_log  /var/log/nginx/access.log main;

  # Set the error log
  error_log /var/log/nginx/error.log;

  # Set the server section
  server {
    # Set the listen port
    listen 3000;

    # Set the root directory for the app
    root /usr/share/nginx/html;

    # Set the default file to serve
    index index.html;

    location / {
        # First attempt to serve request as file, then
        # as directory, then fall back to redirecting to index.html
        try_files $uri $uri/ $uri.html /index.html;
    }

    # Set the error page
    error_page  404 /404.html;
    location = /404.html {
      internal;
    }

    # Set the error page for 500 errors
    error_page  500 502 503 504  /50x.html;
    location = /50x.html {
      internal;
    }
  }
}
```

I then went ahead to build the image using the below command

### Build the Frontend Image 

```sh
docker build \
--build-arg REACT_APP_BACKEND_URL="https://cruddur-alb-<redacted>.us-east-1.elb.amazonaws.com:4567" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="<redacted>" \
--build-arg REACT_APP_CLIENT_ID="<redacted>" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

![frontendimg](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/64300193-8bb3-4311-b906-5ab1ba9dad4e)

### Push the Frontend Image

First I ensure I was loged in to ECR, before you perform operations in ECR you must make sure that I are logged in. 

The command is:

```sh
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
```

The next thing was to create the frontend repo, with the below command

```
aws ecr create-repository \
  --repository-name frontend-react-js \
  --image-tag-mutability MUTABLE
```
 
![frontendrepo](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/e1097f1d-134c-47fe-a381-89fbcd1745d5)

I then tagged the image

```sh
docker tag frontend-react-js:latest $ECR_FRONTEND_REACT_URL:latest
```

Then I pushed the image to the repo

```sh
docker push $ECR_FRONTEND_REACT_URL:latest
```

![FrntImageLnP](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/b6476bcc-f48c-4a22-933a-fb3a3360ff88)


# Deploying the Frontend Container Service

I create a `service-frontend-react-js.json` file that I will use to startup my frontend react app whenever I want to startup the frontend app.

```json
{
    "cluster": "cruddur",
    "launchType": "FARGATE",
    "desiredCount": 1,
    "enableECSManagedTags": true,
    "enableExecuteCommand": true,
    "loadBalancers": [
      {
          "targetGroupArn": "arn:aws:elasticloadbalancing:us-east-1:<redacted>:targetgroup/cruddur-frontend-react-js/<redacted>",
          "containerName": "frontend-react-js",
          "containerPort": 3000
      }
    ],
    "networkConfiguration": {
      "awsvpcConfiguration": {
        "assignPublicIp": "ENABLED",
        "securityGroups": [
          "sg-<redacted>"
        ],
        "subnets": [
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>",
          "subnet-<redacted>"
        ]
      }
    },
    "propagateTags": "SERVICE",
    "serviceName": "frontend-react-js",
    "taskDefinition": "frontend-react-js",
    "serviceConnectConfiguration": {
      "enabled": true,
      "namespace": "cruddur",
      "services": [
        {
          "portName": "frontend-react-js",
          "discoveryName": "frontend-react-js",
          "clientAliases": [{"port": 3000}]
        }
      ]
    }
  }
```

Before deploying the service I registered my task definition with the command:

```sh
aws ecs register-task-definition --cli-input-json file://aws/task-definitions/frontend-react-js.json
```

I then used the command below passing the `frontend-react-js.json` task definition file to deploy the frontend service.

```sh
aws ecs create-service --cli-input-json file://aws/json/service-frontend-react-js.json
```

At this point I had both my frontend and backend container running and everything was working perfectly as can been seen in the screenshot below.

![Cruddur app](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/06d618c6-6b1c-4a6a-8ceb-a9cffeaac2c5)

Time to configure my domain on AWS.

# Configure Custom Domain

My custom domain was gotten from third party provider, [namecheap](namecheap.com) and not from AWS.

To create a hosted zone on AWS, I navigated to the Route53 under the network and content delivery category and selected the hosted zone feature.

![Creating hosted zone](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/30d140d1-9f7e-49af-a98b-2cadf39e0f44)

In the domain name section I entered my doman name which is [sircloudsalot](https://sircloudsalot.xyz/)

It is a public hosted zone as can be seen from my selection in the screenshot above.

After the hosted zone was created I then grabbed the nameservers (circled in the screenshot below) with which I replaced the nameservers my custom domain came with.

![Hosted zone](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/af3c6efc-0752-4954-b6c7-6f269b6aeff2)

I then headed to namecheap where I bought the domain from and changed the nameservers of the domain to those grabbed from AWS.

![namecheap nameserver](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/254cdad4-ab07-4da6-8dc5-a9cf7b4880ed)

# Create SSL Certificate

The next thing I did was to create an SSL certificate, this was done from the AWS Certificate Manager (ACM).

![certificate1](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/c9f2e534-4621-42b2-af34-67c49e19a879)

![certificate2](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/f1d4e5c5-3a77-4145-80d6-940c598b191b)

![certificate3](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/5e2b6cc7-8354-4c2c-842c-1351ab7f9473)

After the SSL Certificate was created I clicked into it, scrolled down and selected the "Create Records in Route53" option.

![SSL issued](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/b484b231-c6bd-4dcb-bb97-fb8cfd482604)

![Record](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/c1dcace8-ed79-46a7-baf7-60a754563f69)

# Edit the Loadbalancer

I clicked into the load  balancer, selected the `cruddur-alb` load balancer and added a new listener.

The first listener will redirect from port 80 to port 443 and the next listener will forward from port 443 to the `frontend-react-js` target group.

After creating these listeners I then delete the other 2 I previously had.

Then I added a new rule to the https:443 listener. I added it on the http header `api.sircloudsalot.xyz` to forward the backend-flask target group.

![New rules](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/1c474ce3-c2fd-4ac0-ba87-c68a448b7e85)

The next thing I did was create two new records in Route53 to point it to my loadbalancer. One for the naked domain and the other for the api subdomain.

![image](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/e021e7b5-736b-41f6-809e-c46563bf0646)

The screenshot shows the configurations.

# Check the Domain is Pointing at the Right Place

I used curl to check that my configurations are in order

```sh
curl https://api.sircloudsalot.xyz/api/health-check
```

![health-check](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/73ba31df-17d9-47a7-a079-566919eea8dc)

![sircloudsalot](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/44b513d6-e828-4934-b8ee-f0de74012c60)

# Update origins and Rebuild image

Owing to the fact that our origins is open up to everything (we used wildcards for our fronend and backend urls in the backend task definition) I will now update their values in order to get the endpoints working correctly.

This was done by updating the `aws/task-definitions/backend-flask.json` file with the below values

```json
...
          {"name": "FRONTEND_URL", "value": "https://sircloudsalot.xyz"},
          {"name": "BACKEND_URL", "value": "https://api.sircloudsalot.xyz"},
...
```

This way our frontend would work because it is now pointing to the correct thing.

We then update our backend task definition by registering it again and also rebuild our frontgend image and push to AWS ECR.

The commands to these have already been shown previously above.

# Secure Backend and Restructure Files

After configuring the frontend and backend on my custom domain we discovered that our app was leaking too much information to users and so we had to fix that.

It was obvous that it was the `ENV FLASK_DEBUG=1` line of code that was causing the information leakage (leakeage of that nature is ok )

The first thing we did was to lockdown access to our loadbalacer by limiting access to it to on my IP address.

I edited the `cruddur-alb-sg` security group. The editing involved deleting inbound rules allowing access from port 4567 and port 3000 then updating access from port 80 to traffic originating from only my IP address.

To fix the information leakage, I deleted the `ENV FLASK_DEBUG=1` line of code and updated the `CMD` line of code as shown below

```sh
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567", "--no-debug","--no-debugger","--no-reload"]
```

I created additional scripts to automate ecr login and container build, then moved the new as well as the previous scripts up a directory so that m scripts were top level and no longer only in the `backend-flask` directory.

# Resolving Expired Token Session

We have been experiencing the issue where sometimes when we make API requests our  cognito token expires without attempting to renew our token.

To fix this issue, we first updated the `CheckAuth` lib with the following code

```js
...

export async function getAccessToken(){
  Auth.currentSession()
  .then((cognito_user_session) => {
    const access_token = cognito_user_session.accessToken.jwtToken
    localStorage.setItem("access_token", access_token)
  })
  .catch((err) => console.log(err));
}

export async function checkAuth(setUser){

...
...

  .then((cognito_user) => {
    console.log('cognito_user',cognito_user);
    setUser({
      display_name: cognito_user.attributes.name,
      handle: cognito_user.attributes.preferred_username
    })
    return Auth.currentSession()
  }).then((cognito_user_session) => {
      console.log('cognito_user_session',cognito_user_session);
      localStorage.setItem("access_token", cognito_user_session.accessToken.jwtToken)
  })
  .catch((err) => console.log(err));
};

```

After this update I then upated the imported checkauth function on the pages using authorization by also importing the new `getAccessToken` function. The updated pages were:

`MessageForm.js`
`HomeFeedPage.js`
`MessageGroupNewPage.js`
`MessageGroupPage.js`
`MessageGroupsPage.js`

The code below is what was added to the above pages

```js
...
import {checkAuth, getAccessToken} from '../lib/CheckAuth';

...

      await getAccessToken()
      const access_token = localStorage.getItem("access_token")

          Authorization: `Bearer ${access_token}`
```

# Configure Container Insights to have X-Ray

To use X-Ray in our container insights we had to include that in our backend task definition and update the task definition.

The include X-Ray code is shown below:

```json
...
    {
      "name": "xray",
      "image": "public.ecr.aws/xray/aws-xray-daemon" ,
      "essential": true,
      "user": "1337",
      "portMappings": [
        {
          "name": "xray",
          "containerPort": 2000,
          "protocol": "udp"
        }
      ]
    },
...
```



