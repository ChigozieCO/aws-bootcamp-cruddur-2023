# Week 5 — DynamoDB and Serverless Caching

I started this week by rearranging my file structure.

# Restucture File System

I created a new directory called `db` in the `backend-flask/bin/` directory where I placed all my database scripts.

The `db` directory contains the `create`, `connect`, `drop`, `schema-load`, `seed`, `session and `setup` scripts.

The next directory I created also in the `backend-flask/bin/` directory was the `rds` directory, here I save all rds scripts which for now is only the `update-sg-rule` script.

The last directory I created in the `backend-flask/bin/` directory was the `ddb` directory which will house all scripts for dynamodb.

# Update Setup script

As a result of the changes made to the namea nd filepaths of the scripts, the `bin/setup` script needed to be updated.

```sh
source "$bin_path/db/drop"
source "$bin_path/db/create"
source "$bin_path/db/schema-load"
source "$bin_path/db/seed"
```



