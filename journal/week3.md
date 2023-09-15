# Week 3 — Decentralized Authentication

# Setup Cognito User Pool

I created a Cognito user pool through the AWS management console.

### Steps
- Click on services
- Select security, Identity and compliance
- Click Cognito

![AWS Management console](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/e741e3d0-74fe-42ab-aab8-98ce7c8b9e1a)

- Click on "create user pool" and follow all the steps to create a user pool.

Once a user pool is created, it would appear on your Cognito dashboard as seen below:

![Cognito user pool](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/72551544-e8af-4bec-b222-195d61569a4a)

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
    .catch((err) => setErrors(err.message) );
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

All these changes made it possible for users to create accounts and interact with the app.

![App users](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/38fd9929-fcb8-4e84-847b-f6eff329c713)


# Cognito Json Web Token for the Backend

Json Web Token, popularly referred to as JWT, authentication is a token-based stateless authentication mechanism. It is popularly used as a client-side-based stateless session, this means the server doesn't have to completely rely on a data store (or) database to save session information.

The JWT signature is a hashed combination of the header and the payload. Amazon Cognito generates two pairs of RSA cryptographic keys for each user pool. One private key signs access tokens, and the other signs ID tokens.

We would be replacing our previously hard coded cookies which was used as session store with the Cognito JWT.

# Added Cognito JWT 

To effectively refence the JWT in our backend we need to have tghe code in our app and so we create a new `cognito_jwt_token.py` file in `backend-flask/lib/`

So we go ahead to add the below blocks of code:

```py

import time
import requests
from jose import jwk, jwt
from jose.exceptions import JOSEError
from jose.utils import base64url_decode

class FlaskAWSCognitoError(Exception):
  pass

class TokenVerifyError(Exception):
  pass

def extract_access_token(request_headers):
    access_token = None
    auth_header = request_headers.get("Authorization")
    if auth_header and " " in auth_header:
        _, access_token = auth_header.split()
    return access_token

class CognitoJwtToken:
    def __init__(self, user_pool_id, user_pool_client_id, region, request_client=None):
        self.region = region
        if not self.region:
            raise FlaskAWSCognitoError("No AWS region provided")
        self.user_pool_id = user_pool_id
        self.user_pool_client_id = user_pool_client_id
        self.claims = None
        if not request_client:
            self.request_client = requests.get
        else:
            self.request_client = request_client
        self._load_jwk_keys()


    def _load_jwk_keys(self):
        keys_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        try:
            response = self.request_client(keys_url)
            self.jwk_keys = response.json()["keys"]
        except requests.exceptions.RequestException as e:
            raise FlaskAWSCognitoError(str(e)) from e

    @staticmethod
    def _extract_headers(token):
        try:
            headers = jwt.get_unverified_headers(token)
            return headers
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e

    def _find_pkey(self, headers):
        kid = headers["kid"]
        # search for the kid in the downloaded public keys
        key_index = -1
        for i in range(len(self.jwk_keys)):
            if kid == self.jwk_keys[i]["kid"]:
                key_index = i
                break
        if key_index == -1:
            raise TokenVerifyError("Public key not found in jwks.json")
        return self.jwk_keys[key_index]

    @staticmethod
    def _verify_signature(token, pkey_data):
        try:
            # construct the public key
            public_key = jwk.construct(pkey_data)
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e
        # get the last two sections of the token,
        # message and signature (encoded in base64)
        message, encoded_signature = str(token).rsplit(".", 1)
        # decode the signature
        decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))
        # verify the signature
        if not public_key.verify(message.encode("utf8"), decoded_signature):
            raise TokenVerifyError("Signature verification failed")

    @staticmethod
    def _extract_claims(token):
        try:
            claims = jwt.get_unverified_claims(token)
            return claims
        except JOSEError as e:
            raise TokenVerifyError(str(e)) from e

    @staticmethod
    def _check_expiration(claims, current_time):
        if not current_time:
            current_time = time.time()
        if current_time > claims["exp"]:
            raise TokenVerifyError("Token is expired")  # probably another exception

    def _check_audience(self, claims):
        # and the Audience  (use claims['client_id'] if verifying an access token)
        audience = claims["aud"] if "aud" in claims else claims["client_id"]
        if audience != self.user_pool_client_id:
            raise TokenVerifyError("Token was not issued for this audience")

    def verify(self, token, current_time=None):
        """ https://github.com/awslabs/aws-support-tools/blob/master/Cognito/decode-verify-jwt/decode-verify-jwt.py """
        if not token:
            raise TokenVerifyError("No token provided")

        headers = self._extract_headers(token)
        pkey_data = self._find_pkey(headers)
        self._verify_signature(token, pkey_data)

        claims = self._extract_claims(token)
        self._check_expiration(claims, current_time)
        self._check_audience(claims)

        self.claims = claims 
        return claims
        
```

# Implement backend check for the token

For every api call made, we need the backend of the app to check for valid JW Tokens and some we will go ahead to modify some pages.

### `requirements.txt`

I added a new dependcy to my `requirements.txt` file.

```
Flask-AWSCognito
```

### `HomeFeedPage.js`

To get the Homepage to communicate with the backend server using the JWT as part of the request header, the code in the `HomeFeedPage.js` file was modified to include the below code:

```py
      const backend_url = `${process.env.REACT_APP_BACKEND_URL}/api/activities/home`
      const res = await fetch(backend_url, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`
        },
        method: "GET"
      });
```

### `app.py`

The `app.py` file was modified to include the following lines of code

```py

...

from lib.cognito_jwt_token import CognitoJwtToken, extract_access_token, TokenVerifyError

...
...

app = Flask(__name__)

cognito_jwt_token = CognitoJwtToken(
  user_pool_id=os.getenv("AWS_COGNITO_USER_POOL_ID"),
  user_pool_client_id=os.getenv("AWS_COGNITO_USER_POOL_CLIENT_ID"),
  region=os.getenv("AWS_DEFAULT_REGION")
)

...
...

cors = CORS(
  app, 
  resources={r"/api/*": {"origins": origins}},
  headers=['Content-Type', 'Authorization'], 
  expose_headers='Authorization',
  methods="OPTIONS,GET,HEAD,POST"
)

...
...

def data_home():
  access_token = extract_access_token(request.headers)
  try:
    claims = cognito_jwt_token.verify(access_token)
  # Authenticated request
    app.logger.debug('authenticated')
    app.logger.debug(claims)
    app.logger.debug(claims['username'])
    data = HomeActivities.run(cognito_user_id=claims['username'])
  except TokenVerifyError as e:
    #Unauthenticated request
      app.logger.debug(e)
      app.logger.debug('unauthenticated')

  data = HomeActivities.run()
  return data, 200
```

### `home_activities.py`

The `home_activities.py` was modified and a new activity was hard coded into the application to test out our token.

```py
...
...
  def run(cognito_user_id=None):
    #logger.info("HomeActivities")
    with tracer.start_as_current_span("home-activities-mock-data"):
      span = trace.get_current_span()

...
...

      if cognito_user_id != None:
        extra_crud = {
        'uuid': '248959df-3079-4947-b847-9e0892d1bab4',
        'handle':  'Lore',
        'message': 'My dear brother, it\'s the humans that are the problem.',
        'created_at': (now - timedelta(hours=1)).isoformat(),
        'expires_at': (now + timedelta(hours=12)).isoformat(),
        'likes': 1042,
        'replies': []
        }
        results.insert(0,extra_crud)

    span.set_attribute("app.result_length", len(results))
    return results
    
```

### `ProfileInfo.js`

We want the Json Web Token to be removed when the user logs out and so this is the last thing to do to pull these all together. 

To do this I modify the signOut method in my `ProfileInfo.js` file

```py
...
...
    try {
        await Auth.signOut({ global: true });
        window.location.href = "/"
        localStorage.removeItem('access_token')
    } catch (error) {
        console.log('error signing out: ', error);
    }
```






