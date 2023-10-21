# Week 8 — Serverless Image Processing

Serverless Image Processing

CDK - Cloud development kit

It is an Infrastructure as code tool (IaC)

For cloudformation, you define your infrastructure in JSON but with CDK you can define in python, java, typescript whatever lang you want.

This week we worked on the serverless Avatar Image processing piece of our application. The purpose of using this serverless pipeline is that in our cruddur application we want to do avatar image processing.

We will create an s3 bucket that will go to a Lambda that will process whatever image is in the s3, this will happen whever something goes into the bucket.

Using CDK, we created resources for S3 bucket, a lambda function that will process our images and some of the interactions with our API and a webhook.

I created a directory that will house all our cdk work, the directory was `thumbing-serverless-cdk`

```sh
mkdir thumbing-serverless-cdk
```

Then installed npm globally so that our cdk library and packages are recognised.

```sh
npm install aws-cdk -g
```

This means my system will be able to recognise AWS cdk when we reference it in our code and also means we'll be able to take advantage of the cdk commands that we will run throughout this week.

The next thing we should do is initialise a cdk application into our new folder. It will give us all the files we need and the folder structure we will need for the project.

```sh
cd thumbing-serverless-cdk
cdk init app --language typescript
```

We are specifying typescript cos that's the language will are using.

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 1 >>>>>>>>>>>>>>>>>>>>>>>>>>>

After initialising cdk we would see a list of files and folders that has been created specifically for this project. In the `thumbing-serverless-cdk-stack.ts` is where we would define all our infrastructure.

# Define S3 Bucket

In the `thumbing-serverless-cdk-stack.ts` we will define the S3 buckect, this is where are Avatar images are going to live for our image processing.

First we import s3 from the cdk library, as shown below:

```ts
import * as s3 from 'aws-cdk-lib/aws-s3';
```

```ts
    const bucketName: string = process.env.THUMBING_BUCKET_NAME as string;
```

### Create the Bucket
 
 It is a best practice to break some of our infrastructure out into separate definitions or functions so that we can interact with it um from the main level.
 
 ```ts
   createBucket(bucketName: string): s3.IBucket {
    const bucket = new s3.Bucket(this, 'ThumbingBucket', {
      bucketName: bucketName,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });
    return bucket;
```

# Synth

To see what we will be building we will run and to make sure that our resources are built correctly I ran the below command.

```sh
cdk synth
```

It is good practice to run this command often before provisioning resources to correct any errors we might have introduced in our code. Synthesizing our code will output a `cdk.out` directory that will show what exactly it is we are building. It is great sanity check before you start doing deployments.

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 2 >>>>>>>>>>>>>>>>>>>>>>>>>>>

# Bootstrap

To provision resources you need to bootstrap your account so that AWS knows you're provisioning resources with cdk

```sh
cdk bootstrap ‘aws://<aws account id>/<aws region you want to use>’
```

Bootstrapping is the process of provisioning resources of AWS cdk before you can deploy cdk apps. 

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 3 >>>>>>>>>>>>>>>>>>>>>>>>>>>

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 4 >>>>>>>>>>>>>>>>>>>>>>>>>>>


# Deploy

After bootstrapping your account you can now go ahead to deploy our resource on AWS by running the deploy command.

```sh
cdk deploy
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 5 >>>>>>>>>>>>>>>>>>>>>>>>>>>

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 6 >>>>>>>>>>>>>>>>>>>>>>>>>>>

# Define Lambda Function

The next thing we do is to write the code that will create the lambda function.

```ts

    const functionPath: string = process.env.THUMBING_FUNCTION_PATH as string;
    const folderInput: string = process.env.THUMBING_S3_FOLDER_INPUT as string;
    const folderOutput: string = process.env.THUMBING_S3_FOLDER_OUTPUT as string;

...

    const lambda = this.createLambda(functionPath, bucketName, folderInput, folderOutput);
    
...

  createLambda(functionPath: string, bucketName: string, folderInput: string, folderOutput: string):lambda.IFunction {
    const lambdaFunction = new lambda.Function(this, 'Thumblambda', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(functionPath)
      environment: {
        DEST_BUCKET_NAME: bucketName
        FOLDER_INPUT: folderInput,
        FOLDER_OUTPUT: folderOutput,
        PROCESS_WIDTH: '512',
        PROCESS_HEIGHT: '512'
      }
    });
    return lambdaFunction;
  }

}
```

# Loading env vars

Our Lambda would need to read the lambda code from our aws directory and this instruction is passed through the environment variable and so we have to pass the env vars with the code below and also create a `.env` file.

First we load the dependency by running:

```sh
npm i dotenv
```

I then went ahead to add the below code that will enable the env vars be loaded in creation of the lambda

```ts

...
import * as dotenv from 'dotenv';

dotenv.config();
```

In the `.env` I added my env vars as shown below

```ts
THUMBING_BUCKET_NAME="sircloudsalot-cruddur-thumbs"
THUMBING_FUNCTION_PATH="/workspaces/aws-bootcamp-cruddur-2023/aws/lambdas"
THUMBING_S3_FOLDER_INPUT="/avatars/original"
THUMBING_S3_FOLDER_OUTPUT="/avatars/processed"
```

With these changes, when I run `cdk synth` again I can see the added resources to my stack.

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 7 >>>>>>>>>>>>>>>>>>>>>>>>>>>

The above solution, the `.env` file , will work until we reload our IDE because we have added `.env` files to our `.gitignore` file and so won't have it anymore.

To solve this we created a file `.env.example` in the `thumbing-serverless-cdk` and added the code below:

```ts
THUMBING_BUCKET_NAME="assets.sircloudsalot.xyz"
THUMBING_S3_FOLDER_INPUT="/avatars/original"
THUMBING_S3_FOLDER_OUTPUT="/avatars/processed"
THUMBING_WEBHOOK_URL="api.sircloudsalot.xyz/webhooks/avatar"
THUMBING_TOPIC_NAME="cruddur-assets"
THUMBING_FUNCTION_PATH="/workspace/aws-bootcamp-cruddur-2023/aws/lambdas/process-images"
```


Now I updated the code in the `thumbing-serverless-cdk-stack-ts` with the below code.

```ts
	const bucketName: string = process.env.THUMBING_BUCKET_NAME as string;
	const folderInput: string = process.env.THUMBING_S3_FOLDER_INPUT as string;
	const folderOutput: string = process.env.THUMBING_S3_FOLDER_OUTPUT as string;
	const webhookUrl: string = process.env.THUMBING_WEBHOOK_URL as string;
	const topicName: string = process.env.THUMBING_TOPIC_NAME as string;
	const functionPath: string = process.env.THUMBING_FUNCTION_PATH as string;
	console.log('bucketName',bucketName)
	console.log('folderInput',folderInput)
	console.log('folderOutput',folderOutput)
	console.log('webhookUrl',webhookUrl)
	console.log('topicName',topicName)
	console.log('functionPath',functionPath)
```

# Lambda Code

To process our images, we use the sharp.js programming lang cos it is concise and lightweight.

We are saving our lambda code in our `aws/lambda/process-images` directory.

The first file we created was `index.js`

```js
const process = require('process');
const {getClient, getOriginalImage, processImage, uploadProcessedImage} = require('./s3-image-processing.js')

const bucketName = process.env.DEST_BUCKET_NAME
const folderInput = process.env.FOLDER_INPUT
const folderOutput = process.env.FOLDER_OUTPUT
const width = parseInt(process.env.PROCESS_WIDTH)
const height = parseInt(process.env.PROCESS_HEIGHT)

client = getClient();

exports.handler = async (event) => {
  console.log('event',event)

  const srcBucket = event.Records[0].s3.bucket.name;
  const srcKey = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
  console.log('srcBucket',srcBucket)
  console.log('srcKey',srcKey)

  const dstBucket = bucketName;
  const dstKey = srcKey.replace(folderInput,folderOutput)
  console.log('dstBucket',dstBucket)
  console.log('dstKey',dstKey)

  const originalImage = await getOriginalImage(client,srcBucket,srcKey)
  const processedImage = await processImage(originalImage,width,height)
  await uploadProcessedImage(dstBucket,dstKey,processedImage)
};
```

The next file we create was the `test.js`

```js
const {getClient, getOriginalImage, processImage, uploadProcessedImage} = require('./s3-image-processing.js')

async function main(){
  client = getClient()
  const srcBucket = 'cruddur-thumbs'
  const srcKey = 'avatar/original/data.jpg'
  const dstBucket = 'cruddur-thumbs'
  const dstKey = 'avatar/processed/data.png'
  const width = 256
  const height = 256

  const originalImage = await getOriginalImage(client,srcBucket,srcKey)
  console.log(originalImage)
  const processedImage = await processImage(originalImage,width,height)
  await uploadProcessedImage(dstBucket,dstKey,processedImage)
}

main()
```

Then I create another file that was called `s3-image-processing.js` and inputted the below code into it:

```js

const sharp = require('sharp');
const { S3Client, PutObjectCommand, GetObjectCommand } = require("@aws-sdk/client-s3");

function getClient(){
  const client = new S3Client();
  return client;
}

async function getOriginalImage(client,srcBucket,srcKey){
  console.log('get==')
  const params = {
    Bucket: srcBucket,
    Key: srcKey
  };
  console.log('params',params)
  const command = new GetObjectCommand(params);
  const response = await client.send(command);

  const chunks = [];
  for await (const chunk of response.Body) {
    chunks.push(chunk);
  }
  const buffer = Buffer.concat(chunks);
  return buffer;
}

async function processImage(image,width,height){
  const processedImage = await sharp(image)
    .resize(width, height)
    .png()
    .toBuffer();
  return processedImage;
}

async function uploadProcessedImage(client,dstBucket,dstKey,image){
  console.log('upload==')
  const params = {
    Bucket: dstBucket,
    Key: dstKey,
    Body: image,
    ContentType: 'image/png'
  };
  console.log('params',params)
  const command = new PutObjectCommand(params);
  const response = await client.send(command);
  console.log('repsonse',response);
  return response;
}

module.exports = {
  getClient: getClient,
  getOriginalImage: getOriginalImage,
  processImage: processImage,
  uploadProcessedImage: uploadProcessedImage
}
```

# Install Packages.

First I created an empty init file in the `aws/lambdas/process-images` directory by running the below code:

```sh
npm init -y
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 8 >>>>>>>>>>>>>>>>>>>>>>>>>>>
The first thing I then installed was the sharp

```sh
npm install sharp
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 9 >>>>>>>>>>>>>>>>>>>>>>>>>>>
We also need to have the sdk installed to use it locally. So we run the below code:

```sh
npm i @aws-sdk/client-s3
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 10 >>>>>>>>>>>>>>>>>>>>>>>>>>>

# Deploy 

After these changes I deployed the existing infrastructure

```sh
cd thumbing-serverless-cdk
cdk deploy
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 11 >>>>>>>>>>>>>>>>>>>>>>>>>>>

After deploying the Lambda code we need to build out sharp in a particular for deployment for our lambda to work. We do this with the following steps:

```sh
npm install
rm -rf node_modules/sharp
SHARP_IGNORE_GLOBAL_LIBVIPS=1 npm install --arch=x64 --platform=linux --libc=glibc sharp
```

### Script to install sharp for the Lambda 

Everytime I relaunch my IDE i would need to install sharp in the exact way as was done above and so to simplify this process I created a script for this and added a command to my `gitpod.yml` to ensure that this script is run every time I launch my IDE.

The contents of the script is shown below:

```sh
#!/usr/bin/bash

cd /workspace/aws-bootcamp-cruddur-2023/aws/lambdas/process-images

# Install dependencies
npm install

# Remove the sharp Repository
rm -rf node_modules/sharp

# Install sharp with specific arch, platform and libc flag
SHARP_IGNORE_GLOBAL_LIBVIPS=1 npm install --arch=x64 --platform=linux --libc=glibc sharp
```

To `gitpod.yml` I added the below code

```yml
  - name: sharp
    command: |
      source "$THEIA_WORKSPACE_ROOT/bin/serverless/sharp"
```

I also added the code to the `devContainer` file so that in the case where I use codespace, my script will be run when I launch that IDE.

```sh
# Sharp
source /workspaces/aws-bootcamp-cruddur-2023/bin/serverless/sharp
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 12 >>>>>>>>>>>>>>>>>>>>>>>>>>>

To help us remember the set of command we made a `serverless/build` script (link to the script)

# Create S3 Event Notification to Lambda

We will create our input next, this we will do by including the following code in our `thumbing-serverless-cdk-stack.ts` file

```ts

import * as s3n from 'aws-cdk-lib/aws-s3-notifications';

  this.createS3NotifyToLambda(folderInput,laombda,bucket)

  createS3NotifyToLambda(prefix: string, lambda: lambda.IFunction, bucket: s3.IBucket): void {
    const destination = new s3n.LambdaDestination(lambda);
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_POST,
      destination,
      {prefix: prefix}
    )
```

I went ahead to deploy once again.

```sh
cdk deploy
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 13 >>>>>>>>>>>>>>>>>>>>>>>>>>>

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 14 >>>>>>>>>>>>>>>>>>>>>>>>>>> 


# Import Bucket

Being that we do not want cdk to constantly delete the S3 bucket we decided to create it manually and import it into the cdk code as against creating the bucket directly from the cdk stack.

To do this, I commented out the line of code where we called the create bucket function and added a line of code to call the import bucket function we also added to the code.

Before I added the necessary code, I destroyed the cdk stack with the below command

```sh
cdk destroy
```

Then I went ahead and added the required code to import the bucket as seen below:

```ts

...

    //const bucket = this.createBucket(bucketName);
    const bucket = this.importBucket(bucketName);
    
....


  importBucket(bucketName: string): s3.IBucket {
    const bucket = s3.Bucket.fromBucketName(this,'AssetsBucket',bucketName);
    return bucket;
  }
 ```

We also went ahead and created the S3 bucket manually so that the bucket is available to be imported.

I also created two folders in the S3 bucket manually

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 15 >>>>>>>>>>>>>>>>>>>>>>>>>>>


# Scripts 

As usual, for automation purposes we created scripts.

I created scripts to clear and upload images from and to our S3 bucket.

I saved my domain name as an env vars

```sh
export DOMAIN_NAME=sircloudsalot.xyz
gp env DOMAIN_NAME=sircloudsalot.xyz
```

`upload`

```sh

#!/usr/bin/bash

ABS_PATH=$(readlink -f "$0")
SERVERLESS_PATH=$(dirname $ABS_PATH)
DATA_FILE_PATH="$SERVERLESS_PATH/files/data.jpg"

aws s3 cp "$DATA_FILE_PATH" "s3://assets.$DOMAIN_NAME/avatars/original/data.jpg"

```


`clear`


```sh

#!/usr/bin/bash

ABS_PATH=$(readlink -f "$0")
SERVERLESS_PATH=$(dirname $ABS_PATH)
DATA_FILE_PATH="$SERVERLESS_PATH/

aws s3 rm "s3://assets.$DOMAIN_NAME/avatars/original/data.jpg"
aws s3 rm "s3://assets.$DOMAIN_NAME/avatars/processed/data.png"

```

# Create Policy for Bucket Access and Attach it to Lambda Role

In other to give our stack the permission to access our bucket we will add this line of code to the stack.

```ts

import * as iam from 'aws-cdk-lib/aws-iam';

...

const s3ReadWritePolicy = this.createPolicyBucketAccess(bucket.bucketArn)

...

  createPolicyBucketAccess(bucketArn: string){
    const s3ReadWritePolicy = new iam.PolicyStatement({
      actions: [
        's3:GetObject',
        's3:PutObject',
      ],
      resources: [
        `${bucketArn}/*`,
      ]
    });
    return s3ReadWritePolicy;
  }
  
```

To attach this policy we just created, we add this line if code to the stack

```ts

lambda.addToRolePolicy(s3ReadWritePolicy);
```

# Create SNS Topic and SNS Subscription

As usual the required code is shown below

```ts

...

import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';

...

    const snsTopic = this.createSnsTopic(topicName)
	this.createSnsSubscription(snsTopic,webhookUrl)
	const snsPublishPolicy = this.createPolicySnSPublish(snsTopic.topicArn)
	
	    lambda.addToRolePolicy(s3ReadWritePolicy);

....

  createSnsTopic(topicName: string): sns.ITopic{
    const logicalName = "ThumbingTopic";
    const snsTopic = new sns.Topic(this, logicalName, {
      topicName: topicName
    });
    return snsTopic;
  }

  createSnsSubscription(snsTopic: sns.ITopic, webhookUrl: string): sns.Subscription {
    const snsSubscription = snsTopic.addSubscription(
      new subscriptions.UrlSubscription(webhookUrl)
    )
    return snsSubscription;
  }

  createS3NotifyToSns(prefix: string, snsTopic: sns.ITopic, bucket: s3.IBucket): void {
    const destination = new s3n.SnsDestination(snsTopic)
    bucket.addEventNotification(
      s3.EventType.OBJECT_CREATED_PUT, 
      destination,
      {prefix: prefix}
    );
  }

  /*
  createPolicySnSPublish(topicArn: string){
    const snsPublishPolicy = new iam.PolicyStatement({
      actions: [
        'sns:Publish',
      ],
      resources: [
        topicArn
      ]
    });
    return snsPublishPolicy;
  }
  */
 ```
 
 # CloudFront
 
 We will serve our images and assets through cloudfront because we won't want to have to keep downloading our images everytime to serve it to our application, so we will serve it through a content distribution network which is CloudFront.
 
 We created our cloudfront through the management console.
 
 The following settings were applied:
 
 Origin domain - we used our assets bucket
 Origin access - Origin access control settings (recommended)
 					We created new control settings as shown below
 
 <<<<<<<<<<<<<<<<<<<<<<<<<<<< image 16 >>>>>>>>>>>>>>>>>>>>>>>>>>>
 
 We left everything as default until we got to the Viewer option
 
 Viewer - Select Redirect HTTP to HTTPS
 
 The rest of the selection can be seen from the screenshots below.
 
 <<<<<<<<<<<<<<<<<<<<<<<<<<<< image 17, 18, 19, 20, 21, 22, 23 >>>>>>>>>>>>>>>>>>>>>>>>>>>
 
 ### Give the S3 Bucket the Necessary Permission
 
 Now we copy the policy we create when we were creating the distribution (image 16) and use it to update our bucket.
 
- Click on the bucket
- Click on the permissions tab and scroll down to the buckets policy.
- Edit the permissions and paste the copied policy.

```json
{
        "Version": "2008-10-17",
        "Id": "PolicyForCloudFrontPrivateContent",
        "Statement": [
            {
                "Sid": "AllowCloudFrontServicePrincipal",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudfront.amazonaws.com"
                },
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::assets.sircloudsalot.xyz/*",
                "Condition": {
                    "StringEquals": {
                      "AWS:SourceArn": "arn:aws:cloudfront::<redated>:distribution/<redated>"
                    }
                }
            }
        ]
      }

- Save changes
 
 ### Create Record in Route53
 
 The next thing we did was to point Route53 to the distribution. To do this we navigated to Route53.
 
- Click into the domain
- Click on create record
- Enter records name as `assets`
- Toggle the alias button to on
- On the `Route traffic to` drop-down select `Alias to CloudFront Distribution`
- Choose the  distribution we just created in the next drop-down
- Click on `create record`

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 24 >>>>>>>>>>>>>>>>>>>>>>>>>>>

### Test Test Test

To confirm that our changes work, I navigated to my browser and entered this url 

assets.sircloudsalot.xyz/avatars/processed/data.xyz

From the screenshot below I can see that the changes work.

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 25 >>>>>>>>>>>>>>>>>>>>>>>>>>>

# Reconfigure Architecture

Along the line we decided we didn't want the unprocessed image accessible to the public so we made a bunch of configuration changes that can be see in [this commit ](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/commit/7a0394a6de1b38851827c316b59ec4756f7a9d11)

Below we can see our restructured buckets

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 26 >>>>>>>>>>>>>>>>>>>>>>>>>>>

I then update my `clear` script and my `upload` scripts to reflect the infrastructure change.

### `clear`

```sh
#!/usr/bin/bash


ABS_PATH=$(readlink -f "$0")
SERVERLESS_PATH=$(dirname $ABS_PATH)
DATA_FILE_PATH="$SERVERLESS_PATH/files/data.jpg"

aws s3 rm "s3://sircloudsalot-uploaded-avatars/avatars/original/data.jpg"
aws s3 rm "s3://assets.$DOMAIN_NAME/avatars/processed/data.jpg"
```

### `uploads`

```sh
#!/usr/bin/bash

ABS_PATH=$(readlink -f "$0")
SERVERLESS_PATH=$(dirname $ABS_PATH)
DATA_FILE_PATH="$SERVERLESS_PATH/files/data.jpg"

aws s3 cp "$DATA_FILE_PATH" "s3://sircloudsalot-uploaded-avatars/data.jpg"
```

# Update Script Structure

I updated my script structure and renamed the Serverless directory to be avatar directory.

I then corrected file paths in gitpod.yml and devcontainer files where I made reference to the scripts contained in avatar directory.

### Test Again

After the updates made above we need to test that our configurations still work.

First I did a deplouy to implement the changes 

```ts
cdk deploy
```

Then I upload the image using the `upload` script

```sh
./bin/avatar/upload
```

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 27 >>>>>>>>>>>>>>>>>>>>>>>>>>>

The image above shows that the upload script ran successfully and uploaded the image to the `sircloudsalot-uploaded-avatars` bucket and the image below shows the processed image in the `assets.sircloudsalot.xyz` bucket.

<<<<<<<<<<<<<<<<<<<<<<<<<<<< image 28 >>>>>>>>>>>>>>>>>>>>>>>>>>>


# Create a Place to Upload our Avatar

For the next changes we want to implement, we decided to first test out our changes in our local environment. 

The first thing, in that light, was to generate out our environment variables by running the required scripts with the following command:

```sh
./bin/frontend/generate-env
./bin/backend/generate-env
```

Now I go ahead and start up my container by running

```sh
docker compose up
```

While my containers are spinning up I create a new script called `bootstrap`, this new script will run other scripts.

```sh

#!/usr/bin/bash

set -e # stop if it fails at any point

CYAN='\033[1;36m'
NO_COLOR='\033[0m'
LABEL="bootstrap"
printf "${CYAN}====== ${LABEL}${NO_COLOR}\n"

ABS_PATH=$(readlink -f "$0")
BIN_DIR=$(dirname $ABS_PATH)

source "$BIN_DIR/db/setup"
source "$BIN_DIR/ddb/schema-load"
source "$BIN_DIR/ddb/seed"
```

when the containers are running, load schema using the scripts

./bin/db/setup
./bin/ddb/schema-load
./bin/ddb/seed

Log in to cruddur

I then head back to my codebase and in `backend-flask/db/sql` I make a new sql file called `show.sql`

```sql

