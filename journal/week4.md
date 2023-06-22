# Week 4 — Postgres and RDS

This week we created our databases. We created both a local Postgres database on my local machine and also a retaional database with a Progres engine on AWS.

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

![RDS cli](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/b71b3e2d-17c0-46ec-b029-923a11d89e99)

![RDS console](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/c54f4dd8-c938-4b56-b720-7860dce41cdf)


When the RDS instance was in the running state I stopped it temporarily to ensure I do not incure extra charges, it will remain in this state until I am ready to use the database. 

As per AWS mechanisms this will only be valid only for 7 days and will automatically restart after 7 days and so if I still want it stopped after the 7 days elaspes I would have to stop it again then.

### Save Endpoint

As we would continually need to connect to the database I need simplify the login process and reduce the number of times I would need to enter the master username and  master password and so I will save this as an env var.


This is will be done using the master username, master user password, rds endpoint, the database port and the Db name as shown below:

`postgresql://<master username>:<master user password>@<RDS Endpoint>:<Database port>/<Db name>`

I saved this as the connection url for production.

To  save it as an env var and persist it on git pod I used the below commands:

```bash
export PROD_CONNECTION_URL="postgresql://cruddurroot:<password>@cruddur-db-instance.ca6twdsr0oxi.us-east-1.rds.amazonaws.com:5432/cruddur"
gp env PROD_CONNECTION_URL="postgresql://cruddurroot:<password>@cruddur-db-instance.ca6twdsr0oxi.us-east-1.rds.amazonaws.com:5432/cruddur"
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

psql $CONNECTION_URL
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
 
THis script is called db-seed, it is a bash script that is used to input the above seed data into our schema which schould already have been loaded on our database.

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








