# Week 6 — Deploying Containers & Solving CORS with a Load Balancer and Custom Domain

This week we moved our app and app resources to AWS, we stored our app images in the AWS ECR, created hosted zones for the custom domains we are hosting the app on. We create d a load balancer and so many other sweet stuff that is explained in detail in this week's journal.

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
aws ecs register-task-definition --cli-input-json file://aws/task-defintions/backend-flask.json
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
The below command was used to create the service through the cli

```sh
aws ecs create-service --cli-input-json file://aws/json/service-backend-flask.json
```

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

# Load Balancer 

The load balancer was created through the management console

![loadblcnr](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/3a404b68-65fd-49b5-8297-6a5ec4b21623)

# Push Frontend Image

Build the frontend image 

```
docker build \
--build-arg REACT_APP_BACKEND_URL="https://4567-$GITPOD_WORKSPACE_ID.$GITPOD_WORKSPACE_CLUSTER_HOST" \
--build-arg REACT_APP_AWS_PROJECT_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_COGNITO_REGION="$AWS_DEFAULT_REGION" \
--build-arg REACT_APP_AWS_USER_POOLS_ID="<redacted>" \
--build-arg REACT_APP_CLIENT_ID="<redacted>" \
-t frontend-react-js \
-f Dockerfile.prod \
.
```

(screenshot frontendimg)

Build the frontend repo

```
aws ecr create-repository \
  --repository-name frontend-react-js \
  --image-tag-mutability MUTABLE
```
 
(screenshot frntendRepo)

Login to ecr and push

```
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"

docker push $ECR_FRONTEND_REACT_URL:latest
```

(screenshot FrntImageLnP)