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

We need to customize the homefeed page to deliver content based on authentication status. This is necessary to curtail information leakage from the app and encourage visitors to create an account on the app and sign in to use the app. Unauthenticated users will not be able to enjoy the full benefit of the app until the sign into the app.

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

### Enable user signin

I created a user directly from my cognito user pool in other to verify that cognito was setup properly. 

As the user was created directly from cognito interface, I needed the user to be verified and so I ran the below code to enable verification of the user.

```yml
aws cognito-idp admin-set-user-password \
--user-pool-id <your-user-pool-id> \
--username <username> \
--password <password> \
--permanent
```

For the user to interact with the app by signing in and enjoying the content, I need implement the sign in page to allow sign in. To do this I modified the `signinpage.js` page with the code below:

```py
import { Auth } from 'aws-amplify';

...
...

const onsubmit = async (event) => {
    setErrors('')
    event.preventDefault();
    Auth.signIn(email, password)
    .then(user => {
      console.log('user',user)
      localStorage.setItem("access_token", user.signInUserSession.accessToken.jwtToken)
      window.location.href = "/"
    })
    .catch(error => {
      if (error.code == 'UserNotConfirmedException') {
        window.location.href = "/confirm"
      }
      setErrors(error.message)
      });
    return false
  }
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

# Implement Pages

Before now I created a user directly from the cognito user pool interface on AWS but this is not the conventional way with which app users will interact with the app. The users will need to signup on the application itself, comfirm their sign up with the code that will be sent to their email and then have the ability to sign in and out of the app. 

We implemented signing in and signing out of the app already above so next we will implement the sign up page, confiemation page and recovery page in the following sections.
 
 # Implement Signup Page
 
 This page will allow visitors create accounts on tghe app. To do this we will modify the SignupPage.js file with the below code:
 
 ```py
 import { Auth } from 'aws-amplify';
 
 ...
 ...
 
   const onsubmit = async (event) => {
    event.preventDefault();
    setErrors('')
    try {
      const { user } = await Auth.signUp({
        username: email,
        password: password,
        attributes: {
          name: name,
          email: email,
          preferred_username: username,
        },
        autoSignIn: { // optional - enables auto sign in after user is confirmed
            enabled: true,
        }
      });
      console.log(user);
      window.location.href = `/confirm?email=${email}`
    } catch (error) {
        console.log(error);
        setErrors(error.message)
    }
    return false
  }
```

# Implement Confirmation Page

After a user creates an account, a confirmation code will be sent to their email to confirm the action creation. For this conmfirmation to be successful I needed to implement the confirmation page. This was done by modifying the ConfirmationPage.js file with the code below:

```py
import { Auth } from 'aws-amplify';

...
...

 const resend_code = async (event) => {
    setErrors('')
    try {
      await Auth.resendSignUp(email);
      console.log('code resent successfully');
      setCodeSent(true)
    } catch (err) {
      // does not return a code
      // does cognito always return english
      // for this to be an okay match?
      console.log(err)
      if (err.message == 'Username cannot be empty'){
        setErrors("You need to provide an email in order to send Resend Activiation Code")   
      } else if (err.message == "Username/client id combination not found."){
        setErrors("Email is invalid or cannot be found.")   
      }
    }
  }
 
 ...
 ...
 
   const onsubmit = async (event) => {
    event.preventDefault();
    setErrors('')
    try {
      await Auth.confirmSignUp(email, code);
      window.location.href = "/"
    } catch (error) {
      setErrors(error.message)
    }
    return false
  }
```
# Implement Recover Page

This page will allow users recover their username or password in the envent that the forget either of them. We modify the `RecoverPage.js` file for this.

```py
import { Auth } from 'aws-amplify';

...
...

  const onsubmit_send_code = async (event) => {
    event.preventDefault();
    setErrors('')
    Auth.forgotPassword(username)
    .then((data) => setFormState('confirm_code') )
    .catch((err) => setCognitoErrors(err.message) );
    return false
  }
  
  const onsubmit_confirm_code = async (event) => {
    event.preventDefault();
    setErrors('')
    if (password == passwordAgain){
      Auth.forgotPasswordSubmit(username, code, password)
      .then((data) => setFormState('success'))
      .catch((err) => setErrors(err.message) );
    } else {
      setErrors('Passwords do not match')
    }
    return false
  }
```

All these changes made it possi ble for users to create accounts and interact with the app.

![App users](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/38fd9929-fcb8-4e84-847b-f6eff329c713)






