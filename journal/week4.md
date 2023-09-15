# Week 4 — Postgres and RDS

This week we created our databases. We created both a local Postgres database on my local machine and also a retaional database with a Progres engine on AWS.

We also put automation in progress by writing a bunch of scripts to automate a lot of the repititive tasks we will we doing.

We configured a Lambda function as well.

# Create RDS

The first thing I did was create an RDS instance on AWS using the command line. The code below was what was used in creating the RDS instance:

```yml
aws rds create-db-instance \
  --db-instance-identifier cruddur-db-instance \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version  14.6 \
  --master-username cruddurroot \
  --master-user-password <password> \
  --allocated-storage 20 \
  --availability-zone us-east-1a \
  --backup-retention-period 0 \
  --port 5432 \
  --no-multi-az \
  --db-name cruddur \
  --storage-type gp2 \
  --publicly-accessible \
  --storage-encrypted \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --no-deletion-protection
```

![RDS cli](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/b71b3e2d-17c0-46ec-b029-923a11d89e99)

![RDS console](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/c54f4dd8-c938-4b56-b720-7860dce41cdf)


When the RDS instance was in the running state I stopped it temporarily to ensure I do not incure extra charges, it will remain in this state until I am ready to use the database. 

As per AWS mechanisms this will only be valid only for 7 days and will automatically restart after 7 days and so if I still want it stopped after the 7 days elaspes I would have to stop it again then.

### Save Endpoint

As we would continually need to connect to the database I need simplify the login process and reduce the number of times I would need to enter the master username and  master password and so I will save this as an env var.


This is will be done using the master username, master user password, rds endpoint, the database port and the Db name as shown below:

`postgresql://<master username>:<master user password>@<RDS Endpoint>:<Database port>/<Db name>`

I saved this as the connection url for production.

To  save it as an env var and persist it on git pod I used the below commands:

```bash
export PROD_CONNECTION_URL="postgresql://cruddurroot:<password>@cruddur-db-instance.<redacted>.us-east-1.rds.amazonaws.com:5432/cruddur"
gp env PROD_CONNECTION_URL="postgresql://cruddurroot:<password>@cruddur-db-instance.<redacted>.us-east-1.rds.amazonaws.com:5432/cruddur"
```

# Create Local Database

To connect to Postgresql via the psql client cli tool in a container remember to use the host flag to specify localhost. When running directly on your computer you wouldn't need the --host localhost flag.

`psql -Upostgres --host localhost`

Within the PSQL client I created a local database using the below command: 

```bash
CREATE database cruddur;
```

To connect to this local database, just as I did with m RDS database, I created a connection url for this database to somewhat automation the connection process and reduce the number of times I enter my password.

I then saved this as an env var as shown below:

```bash
export CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
gp env CONNECTION_URL="postgresql://postgres:<password>@localhost:5432/cruddur"
```

### Add Connection Urls to Config

After setting up our connection url and our prod connection url the next thing to do is to add them our docker compose file so that our container can find and use them when the need arises.

In my docker compose file I will name both the local database connection url and the prod connection url as connection url and depending on which is to be used at any point the other will be commented out.

That is to say that if I am working in production, then the local connection url will be commented out and vise versa.

In the `docker-compose.yml` file:

```yml
services:
  backend-flask:
    environment:
      CONNECTION_URL: postgresql://postgres:<password>@db:5432/cruddur
      #CONNECTION_URL: "${PROD_CONNECTION_URL}"
```

### Common PSQL commands

```sql
\x on -- expanded display when looking at data
\q -- Quit PSQL
\l -- List all databases
\c database_name -- Connect to a specific database
\dt -- List all tables in the current database
\d table_name -- Describe a specific table
\du -- List all users and their roles
\dn -- List all schemas in the current database
CREATE DATABASE database_name; -- Create a new database
DROP DATABASE database_name; -- Delete a database
CREATE TABLE table_name (column1 datatype1, column2 datatype2, ...); -- Create a new table
DROP TABLE table_name; -- Delete a table
SELECT column1, column2, ... FROM table_name WHERE condition; -- Select data from a table
INSERT INTO table_name (column1, column2, ...) VALUES (value1, value2, ...); -- Insert data into a table
UPDATE table_name SET column1 = value1, column2 = value2, ... WHERE condition; -- Update data in a table
DELETE FROM table_name WHERE condition; -- Delete data from a table
```

# Bash Scripts

While using our databases we will have a lot of repetitive tasks and so we can automate those tasks to reduce of execution time considerably.

To automate these tasks we will be write a bunch of bash scripts.


### Bash Script to Connect to the Database

This script was created for ease of connection to the database.

This way when I need to connect to the database all I need to do is to runn the script, the content of the script can be seen below.

```bash
#!/usr/bin/bash 

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-connect"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

if [ "$1" == "prod" ]; then
    echo "Running in production mode"
    URL=$PROD_CONNECTION_URL
else
    URL=$CONNECTION_URL
fi

psql $URL
```

The first line of code is called a shebang and its use is to tell the script what shell it would run wth.

This script was named `db-connect` and was saved in `backend-flask/bin/` directory.

After creating this file, I made the file executable by running the below command:

```sh
chmod u+x bin/db-connect
```

This step will be repeated for all scripts I create.


### Script to Create Database

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-create"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "CREATE DATABASE cruddur;"
```
The printf statement announces what the script is doing on the cli so it is clear, to anyone who looks, what command was just run.

Finally we make this script executable the same way we made the db-connect script executable.

### Script to Drop the Database

In the event that we want to drop the database the script to run is the `db-drop` script which we created here and it's contents are shown below.

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-drop"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

NO_DB_CONNECTION_URL=$(sed 's/\/cruddur//g' <<<"$CONNECTION_URL")
psql $NO_DB_CONNECTION_URL -c "DROP DATABASE cruddur;"
```

### Schema Script

This script contains the sql commands we will use to create our schema.

When the script is run it will create an extension if it doesn't already exit, it would also drop the two tables we are about to create if they alrady exist.

Then it would create the user table and the activities table.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.activities;

CREATE TABLE public.users (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  display_name text,
  handle text,
  cognito_user_id text,
  created_at TIMESTAMP default current_timestamp NOT NULL
);

CREATE TABLE public.activities (
  uuid UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_uuid UUID NOT NULL,
  message text NOT NULL,
  replies_count integer DEFAULT 0,
  reposts_count integer DEFAULT 0,
  likes_count integer DEFAULT 0,
  reply_to_activity_uuid integer,
  expires_at TIMESTAMP,
  created_at TIMESTAMP default current_timestamp NOT NULL
);
```

### Script to Load the Database Schema

At some point when using the database, we will need to load our schema  we created above on the database and so we will also create a script for this task.

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-schema-load"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

schema_path="$(realpath .)/db/schema.sql"
echo $schema_path

if [ "$1" == "prod" ]; then
    echo "Running in production mode"
    URL=$PROD_CONNECTION_URL
else
    URL=$CONNECTION_URL
fi

psql $URL < $schema_path
```

We included a conditional statement in this script to check if the database we are loading the schema for is our production database or our local database.


### Seed Script

This script contains SQL commands that would seed mock information into our tables. 

We are hard coding this data into our database to test that our configuration works.

The contents are contained below:

```sql
-- this file was manually created
INSERT INTO public.users (display_name, handle, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown' ,'MOCK'),
  ('Andrew Bayko', 'bayko' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'andrewbrown' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  )
```

### Script to Seed Data
 
This script is called db-seed, it is a bash script that is used to input the above seed data into our schema which schould already have been loaded on our database.

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-seed"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

seed_path="$(realpath .)/db/seed.sql"
echo $seed_path

if [ "$1" == "prod" ]; then
    echo "Running in production mode"
    URL=$PROD_CONNECTION_URL
else
    URL=$CONNECTION_URL
fi

psql $URL < $seed_path
```

### Script for Session

In the case where you have more than one session running, we might need to see which particular session is running in case we need to kill some of them.

This is what this script will do when run.

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-sessions"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

if [ "$1" == "prod" ]; then
    echo "Running in production mode"
    URL=$PROD_CONNECTION_URL
else
    URL=$CONNECTION_URL
fi

NO_DB_URL=$(sed 's/\/cruddur//g' <<<"$URL")
psql $NO_DB_URL -c "select pid as process_id, \
       usename as user,  \
       datname as db, \
       client_addr, \
       application_name as app,\
       state \
from pg_stat_activity;"
```

### Setup Script 

This script drops the database if it already exists, creates a new database, loads the schema and seeds data.

There is a line of code that stops the process if any of the steps fail.

```sh
#!/usr/bin/bash

-e # stop if it fails at any point

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="db-setup"
printf "${CYAN}==== ${LABEL}${NO_COLOR}\n"

bin_path="$(realpath .)/bin"

source "$bin_path/db-drop"
source "$bin_path/db-create"
source "$bin_path/db-schema-load"
source "$bin_path/db-seed"
```

### Script to Allow Connection to the AWS RDS Instance.

By default our RDS instance will only allow traffic from the default security group, this is to secure our database and limit it's interaction with ecternal factors whether malicious or otherwise.

Therefore we need to add an inbound rule to allow traffic from our IDE to the RDS.

I interchanglably use Gitpod and Github codespaces and so I will add inbound rules to allow traffic from both IDEs.

The first step is to save the security group id and security rule id as env vars. This is done as shown below:

```sh
export DB_SG_ID="<redacted>"
gp env DB_SG_ID="<redacted>"

export DB_SG_RULE_ID="<redacted>"
gp env DB_SG_RULE_ID="<redacted>"
```

I also set the IP address of my IDE as an env variable but here I will not hard code the value because it changes with each relaunch of the IDE.

The command below is what I use to set my IDE IP for both Gitpod and Codespaces.

```sh
GITPOD_IP=$(curl ifconfig.me)
CODESPACES_IP=$(curl ifconfig.me)
```

Now I go ahead and create my script which is named `update-sg-rule` and save in `backend-flask/bin/rds/`

```sh
#!/usr/bin/bash

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="rds-update-sg-rule"
printf "${CYAN}== ${LABEL}${NO_COLOR}\n"

# When using Gitpod
aws ec2 modify-security-group-rules \
    --group-id $DB_SG_ID \
    --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=GITPOD,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$GITPOD_IP/32}"
    
# When using Codespaces
# aws ec2 modify-security-group-rules \
#     --group-id $DB_SG_ID \
#     --security-group-rules "SecurityGroupRuleId=$DB_SG_RULE_ID,SecurityGroupRule={Description=CODESPACES,IpProtocol=tcp,FromPort=5432,ToPort=5432,CidrIpv4=$CODESPACES_IP/32}"
```

Depending on which IDE I am using at the time, the other is commented out.

The last step hers is to update my `.gitpod.yaml` file as well as my `postCreateCommand.sh` file to update my IDE IP address in the env var for Gitpod and Codespaces respectively on launch of whichever IDE.

In my `.devContainer` directory I update my `postCreateCommand.sh` file to include the below:

```sh
# Update rds security rules
export CODESPACES_IP=$(curl ifconfig.me)
source /workspaces/aws-bootcamp-cruddur-2023/backend-flask/bin/rds/update-sg-rule
```

Next I update my `.gitpod.yml` file with the command below:

```sh
    command: |
      export GITPOD_IP=$(curl ifconfig.me)
      source "$THEIA_WORKSPACE_ROOT/backend-flask/bin/rds/update-sg-rule"
```

Now whenever I launch my IDEs their current IP is saved and the correct value is used to update my RDS security group rule.

![Security group](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/37d70f63-e024-496e-bd4d-a84840492838)


# Install Postgres client, Implement DB Object and Connection Pool

### Add Psycopg Library to Requirements.

To connect to the Postgres database, I need to include psycopg library to my `requirements.txt` file:

```
...
psycopg[binary]
psycopg[pool]
```

### Implement DB Object

I created a new file `db.py` in the `backend-flask/lib/` directory and added the following lines of code:

```py
from psycopg_pool import ConnectionPool
import os

def query_wrap_object(template):
  sql = f"""
  (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
  {template}
  ) object_row);
  """
  return sql

def query_wrap_array(template):
  sql = f"""
  (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
  {template}
  ) array_row);
  """
  return sql

connection_url = os.getenv("CONNECTION_URL")
pool = ConnectionPool(connection_url)
```

### Implement Connection Pool

In the `home_activities.py` file I add these lines of code

```py
...
from lib.db import pool, query_wrap_array
...
...
      sql = query_wrap_array("""
        SELECT
          activities.uuid,
          users.display_name,
          users.handle,
          activities.message,
          activities.replies_count,
          activities.reposts_count,
          activities.likes_count,
          activities.reply_to_activity_uuid,
          activities.expires_at,
          activities.created_at
        FROM public.activities
        LEFT JOIN public.users ON users.uuid = activities.user_uuid
        ORDER BY activities.created_at DESC
      """)
      print("SQL-----------")
      print(sql)
      print("SQL-----------")

      with pool.connection() as conn:
          with conn.cursor() as cur:
            cur.execute(sql)
            # this will return a tuple
            # the first field being the data
            json = cur.fetchall()
            json = cur.fetchone()
      return json[0]
      return results
```

# Lambda Function

### Create Lambda Function

The Lambda function we will be creating here will insert new users and their details into our cruddur app database post confirmation of the user and this is why this function is named `cruddur-post-confirmation`.

Through the AWS console I created a new Lambda function, it was setup as shown in the image below

![cruddur-post-configuration function](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/0f3a8bf0-bb0c-49ea-8f70-83f8faac4182)

### Add Layer

I added a layer to the Lambda function in other to be able to use psycopg2 in the Lambda function.

I selected the appropratiate arn from [here](https://github.com/jetbridge/psycopg2-lambda-layer) that matched my RDS region.

THe settings for the layer is shown below:

![Lambda Layer](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/89775a03-c257-4ae0-90bc-b74a2b3e5327)

### Lambda Code

In order to have all our code in our repo, we created a `cruddur-post-configuration.py` file in the `aws-bootcamp-cruddur-2023/aws/lambdas/` directory where I saved our Lambda function code.

This was the same code I added to my Lambda function.

The code can be seen below:

```py
import json
import psycopg2
import os

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    print('userAttributes')
    print(user)

    user_display_name = user['name']
    user_email        = user['email']
    user_handle       = user['preferred_username']
    user_cognito_id   = user['sub']
    try:
        print('Entered try --------')
        sql = f"""
            INSERT INTO users (
                display_name,
                email,
                handle,
                cognito_user_id
                ) 
            VALUES(%s,%s,%s,%s)
        """
        print('SQL STATEMENT --------')
        print(sql)
        conn = psycopg2.connect(os.getenv('CONNECTION_URL'))
        cur = conn.cursor()
        params = [
            user_display_name,
            user_email,
            user_handle,
            user_cognito_id
        ]
        cur.execute(sql,params)
        conn.commit() 

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            cur.close()
            conn.close()
            print('Database connection closed.')
    return event
```

### Update Permissions

For the function to adequately communicate with all the necesary services I had to add extra policy to the lambda role as the default role would not suffice.

In the default role created with the Lambda, I clicked on `add permission`, clicked on `create Policy` and select `EC2` from the services provided and chose the JSON format to input the code below:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DeleteNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeInstances",
                "ec2:AttachNetworkInterface"
            ],
            "Resource": "*"
        }
    ]
}
```

![EC2 Policy](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/2eb3bb1b-618d-4c43-be0e-63a51b4d9ec7)

I then add this new policy to the default role and save the changes

![Lambda role](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/78ed006e-0877-4ad9-ab8a-5daec0948dbb)


### Add Env Var

The CONNECTION_URL is mentioned in the function code and so we need to add it as an env var that is accessible to our function.

This is done by clicking on the Configurations tab of the function and selecting environment varibles, this where I will enter the CONNECTION_URL. The url here is the PROD_CONNECTION_URL which I setup earlier.

![Lambda Env Var](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/afbf2fb9-e19f-4ae2-8812-25d5200a3ffe)

![Function env var](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/36d8fb76-cdfa-4df1-8743-bb2d57e814c2)

### Connect Function to a VPC

Still in the configurations tab of the function, I clicked on the VPC sub category and connected the default VPC which is the same VPC connected to my RDS Instance.

I connected the VPC and 2 subnets to the cruddur-post-configuration function and attached the required security group.

# Add Lambda Trigger to Cognito

After successfully configuring the cruddur-post-configuration function I can now implment the Lambda trigger in cognito so that when a user confirms their account, the Lambda function is trigger and that user's details are entered into my database.

In AWS Cognito, I select my `cruddur-user-pool`, navigate to User pool properties and click on Add Lambda Trigger.

The required configuration is as shown below:

![Lambda Trigger](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/c4f99ab0-0e82-40d2-b9df-a57a9bc45357)

# Refactor the db library

As we were using the db library `(db.py)` created earlier above we realised that caling the queries in the function would be easier if we put them in a class and made reference to those we put in their seperate files .

So this is what we did here, the refactored code looked as shown below:

```py
from psycopg_pool import ConnectionPool
import os
import re
import sys
from flask import current_app as app

class db:
  def __init__(self):
    self.init_pool()

  def template(self,*args):
    pathing = list((app.root_path,'db','sql','activities',) + args)
    pathing[-1] = pathing[-1] + ".sql"

    template_path = os.path.join(*pathing)

    green = '\033[92m'
    no_color = '\033[0m'
    print("\n")
    print(f'{green} Load SQL Template: {template_path} {no_color}')

    with open(template_path, 'r') as f:
      template_content = f.read()
    return template_content

  def init_pool(self):
    connection_url = os.getenv("CONNECTION_URL")
    self.pool = ConnectionPool(connection_url)
  # We want to commit query such as an insert
  # be sure to check for RETURNING in all uppercases
  def print_params(self,params):
    blue = '\033[94m'
    no_color = '\033[0m'
    print(f'{blue} SQL Params:{no_color}')
    for key, value in params.items():
      print(key, ":", value)

  def print_sql(self,title,sql):
    cyan = '\033[96m'
    no_color = '\033[0m'
    print(f'{cyan} SQL STATEMENT-[{title}]------{no_color}')
    print(sql)
  def query_commit(self,sql,params={}):
    self.print_sql('commit with returning',sql)

    pattern = r"\bRETURNING\b"
    is_returning_id = re.search(pattern, sql)

      with self.pool.connection() as conn:
        cur =  conn.cursor()
        cur.execute(sql,params)
        if is_returning_id:
          returning_id = cur.fetchone()[0]
        conn.commit() 
        if is_returning_id:
          return returning_id
    except Exception as err:
      self.print_sql_err(err)
      #conn.rollback()
  # when we want to return a json object
  def query_array_json(self,sql,params={}):
    self.print_sql('array',sql)

    wrapped_sql = self.query_wrap_array(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql,params)
        json = cur.fetchone()
        return json[0]
  # when we want to return an array of json objects
  def query_object_json(self,sql,params={}):

    self.print_sql('json',sql)
    self.print_params(params)
    wrapped_sql = self.query_wrap_object(sql)
    with self.pool.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(wrapped_sql,params)
        json = cur.fetchone()
        if json == None:
          "{}"
        else:
          return json[0]

  def query_wrap_object(self,template):
    sql = f"""
    (SELECT COALESCE(row_to_json(object_row),'{{}}'::json) FROM (
    {template}
    ) object_row);
    """
    return sql
  def query_wrap_array(self,template):
    sql = f"""
    (SELECT COALESCE(array_to_json(array_agg(row_to_json(array_row))),'[]'::json) FROM (
    {template}
    ) array_row);
    """
    return sql
  def print_sql_err(self,err):
    # get details about the exception
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    line_num = traceback.tb_lineno

    # print the connect() error
    print ("\npsycopg ERROR:", err, "on line number:", line_num)
    print ("psycopg traceback:", traceback, "-- type:", err_type)

    # print the pgcode and pgerror exceptions
    print ("pgerror:", err.pgerror)
    print ("pgcode:", err.pgcode, "\n")
```

# Create Activity

To improve the functionality of our app, to allow users send cruds (think instant short messaging, think tweets) which will populate the application, we need to improve our codebase.

The first thing we did was create a `create.sql` file. It's contents:

```py
INSERT INTO (
    user_uuid,
    message,
    expires_at
)
VALUES (
    (SELECT uuid 
    from public.users 
    WHERE users.handle = %(handle)s 
    LIMIT 1
    ),
    %(message)s,
    %(expires_at)s,
) RETURNING uuid;
```

Next I created another sql file called `home.sql` that was placed in the `backend-flask/db/sql/activities/` directory. The contents are shown below:

```sql
SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  activities.message,
  activities.replies_count,
  activities.reposts_count,
  activities.likes_count,
  activities.reply_to_activity_uuid,
  activities.expires_at,
  activities.created_at
FROM public.activities
LEFT JOIN public.users ON users.uuid = activities.user_uuid
ORDER BY activities.created_at DESC
```

Now, instead of having this query directly in the home_activities code, I edited the code in the `home_activities.py` file to make reference to this file to run the query as shown:

```py
...
from lib.db import db
...

    sql = db.template('activities','home')
    results = db.query_array_json(sql)
    return results
```

Still in the `backend-flask/db/sql/activities/` directory, I created another sql file that was called `object.sql`. The code was shown below and the query was refenced in our `create_activity` code

```sql
SELECT
  activities.uuid,
  users.display_name,
  users.handle,
  activities.message,
  activities.created_at,
  activities.expires_at
FROM public.activities
INNER JOIN public.users ON users.uuid = activities.user_uuid 
WHERE 
  activities.uuid = %(uuid)s
```

Next we edited the code in the `create_activity.py` file:

```py
...
#from lib.db import db

...
...

    else:
      expires_at = (now + ttl_offset)
      uuid = CreateActivity.create_activity(user_handle,message,expires_at)

      object_json = CreateActivity.query_object_activity(uuid)
      model['data'] = object_json
    return model

  def create_activity(handle, message, expires_at):
    sql = db.template('activities','create')
    uuid = db.query_commit(sql,{
      'handle': handle,
      'message': message,
      'expires_at': expires_at
    })
    return uuid

  def query_object_activity(uuid):
    sql = db.template('activities','object')
    return db.query_object_json(sql,{
      'uuid': uuid
    })
```

# NotNullViolation error

After all this was done and I ran my container again, I kept getting a NotNullViolation error.

After days of troubleshooting and not coming up  with any working solution, I went to the discord channel and with guidance from those who had been able to solve the problem I was able to correct my code in the following ways.

`app.py`

In the `appy.py` codebase I removed the hard coded users, instead a request would be made and the response would then be saved in the variable.

```py
def data_activities():
  user_handle  = request.json['user_handle']
  message = request.json['message']
  ttl = request.json['ttl']
  model = CreateActivity.run(message, user_handle, ttl)
```

I then include 'email" in the `seed.sql` code because the `cruddur-post-configuration` lambda code kept looking for email as that was include in the values but it was present as it wasn't part of the seeded data.

```sql
INSERT INTO public.users (display_name, handle, email, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown' , 'andrew@test.com', 'MOCK'),
  ('Andrew Bayko', 'bayko' , 'bayko@friedfish.com', 'MOCK');
```

I also made some changes to my `db.py` file

```py
class Db:
  def __init__(self):
    self.init_pool()

  def template(self,*args):
    pathing = list((app.root_path,'db','sql',) + args)
    pathing[-1] = pathing[-1] + ".sql"

    template_path = os.path.join(*pathing)

...
...

    print ("pgcode:", err.pgcode, "\n")

db = Db()
```

I needed to forward the "user_handle" to the `ActivityForm` so I updated my `HomeFeedPage.js` file like so:

```js
      <DesktopNavigation user={user} active={'home'} setPopped={setPopped} />
      <div className='content'>
        <ActivityForm  
          user_handle={user}
          popped={popped}
          setPopped={setPopped} 
          setActivities={setActivities}
```

In the `ActivityForm.js` file I include "user_handle" in the post request message:

```js

...
...

        body: JSON.stringify({
          user_handle: props.user_handle.handle,
          message: message,
          ttl: ttl
        }),

...
...

With all these in place I was able to get rid of the NotNullViolation error and my cruddur app ran seamlessly.

