# Week 3 — Decentralized Authentication

# Setup Cognito User Pool

I created a Cognito user pool through the AWS management console.

### Steps
- Click on services
- Select security, Identity and compliance
- Click Cognito

![AWS Management console](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/e741e3d0-74fe-42ab-aab8-98ce7c8b9e1a)

- Click on "create user pool" and follow all the steps to create a user pool.

Once a user pool is created, it would appear on your Cognito dashboard as seen below:

![Cognito user pool](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/72551544-e8af-4bec-b222-195d61569a4a)

# Configure Amplify

In other for our app to properly utilize cognito for authentication we need to configure amplify in the frontend part of the app.

```
cd frontend-react-js 
npm i aws-amplify --save
```

The above lines of code will change into the frontend directory, install AWS amplify and ensure the amplify library is added and saved in the package.json.

I retrieved my user pool client id and my user pool id and set them as environment IDs as well as persit them on gitpod so when next I open my terminal it will be available to use.

```bash
export  env AWS_USER_POOLS_ID="<User Pool Id>"
export env COGNITO_APP_CLIENT_ID="<Client ID>"
gp env AWS_USER_POOLS_ID="<User Pool Id>"
gp env COGNITO_APP_CLIENT_ID="<Client ID>"
```

In other to add the Amplify dependenies to our app, I added the below lines of code to the `app.js` file:

```py
import { Amplify } from 'aws-amplify';

Amplify.configure({
  "AWS_PROJECT_REGION": process.env.REACT_AWS_PROJECT_REGION,
  "aws_cognito_identity_pool_id": process.env.REACT_APP_AWS_COGNITO_IDENTITY_POOL_ID,
  "aws_cognito_region": process.env.REACT_APP_AWS_COGNITO_REGION,
  "aws_user_pools_id": process.env.REACT_APP_AWS_USER_POOLS_ID,
  "aws_user_pools_web_client_id": process.env.REACT_APP_CLIENT_ID,
  "oauth": {},
  Auth: {
    // We are not using an Identity Pool
    // identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID, // REQUIRED - Amazon Cognito Identity Pool ID
    region: process.env.REACT_AWS_PROJECT_REGION,           // REQUIRED - Amazon Cognito Region
    userPoolId: process.env.REACT_APP_AWS_USER_POOLS_ID,         // OPTIONAL - Amazon Cognito User Pool ID
    userPoolWebClientId: process.env.REACT_APP_AWS_USER_POOLS_WEB_CLIENT_ID,   // OPTIONAL - Amazon Cognito Web Client ID (26-char alphanumeric string)
  }
});
```

### Integrate Cognito

To integrate cognito into the containerized app I added the below lines of code to the `docker-compose.yml` file

```bash
      REACT_APP_AWS_PROJECT_REGION: "${AWS_DEFAULT_REGION}"
      REACT_APP_AWS_COGNITO_REGION: "${AWS_DEFAULT_REGION}"
      REACT_APP_AWS_USER_POOLS_ID: "#####redacted#####"
      REACT_APP_CLIENT_ID: "#####redacted#####"
```

### Configure Content to Show based on Login Status

After creating users in the cognito user pool and verifying the ability to login into the app the next thing I did was to customize the home-feed page to deliver content based on authentication status. 

The `HomeFeedPage.js` page was modified to deliver limited content to unautenticated users and unlimited content to authenticated users.

To do this, the below code was added:

```py
import { Auth } from 'aws-amplify';

// check if we are authenicated
const checkAuth = async () => {
  Auth.currentAuthenticatedUser({
    // Optional, By default is false. 
    // If set to true, this call will send a 
    // request to Cognito to get the latest user data
    bypassCache: false 
  })
  .then((user) => {
    console.log('user',user);
    return Auth.currentAuthenticatedUser()
  }).then((cognito_user) => {
      setUser({
        display_name: cognito_user.attributes.name,
        handle: cognito_user.attributes.preferred_username
      })
  })
  .catch((err) => console.log(err));
};

```

### Enable user signout

In other to allow signed in users the ability to sign out, we modified the SignOut block of code in the `ProfileInfo.js` file.

Added the below lines of code:

```py
import { Auth } from 'aws-amplify';
...
    try {
        await Auth.signOut({ global: true });
        window.location.href = "/"
    } catch (error) {
        console.log('error signing out: ', error);
    }
}
```
 


