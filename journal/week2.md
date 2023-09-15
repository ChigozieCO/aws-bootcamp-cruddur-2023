# Week 2 — Distributed Tracing

This week we implemented distributed tracing into our app. This is necessary as a way to easily troubleshoot because as the app services grows it could become really difficult and time consuming to locate issues.

## Instrument HoneyComb

- #### Setup account and create environment

To use Honeycomb for distributed tracing, the first step was to create an account on [honeycomb](https://www.honeycomb.io/).

Honeycomb has both the free and trial versaion and for this project I created a trial version account.

Honeycomb comes with a default environment called test but I created a specific environment which I named bootcamp to use for this project.

![Honeycomb bootcamp environment](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/1d66b131-f90a-424b-92bc-30c3d8903b02)


After creating this environment I was then able to take the Api key for the enviroment and export to my gitpod environment using the below code.

```sh
export HONEYCOMB_API_KEY="######"
export HONEYCOMB_SERVICE_NAME="Cruddur"
gp env HONEYCOMB_API_KEY="#######"
gp env HONEYCOMB_SERVICE_NAME="Cruddur"
```

The export command exports to the present environment while the gp command is used to persist the Api key to the gitpod environment so that even if I close down the this environment, the next environmment will still have the Api key variable.


- #### Implement Open Telemetry (OTEL)

To install the Open Telemetry (OTEL) dependencies I added the below lines of code to the [`requirements.txt`](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/blob/main/backend-flask/requirements.txt)

```
opentelemetry-api 
opentelemetry-sdk 
opentelemetry-exporter-otlp-proto-http 
opentelemetry-instrumentation-flask 
opentelemetry-instrumentation-requests
```

Then I installed these dependencies by running:

```
pip install -r requirements.txt
```

To use Open Telemetry (OTEL) with Honeycomb as provider I had to configure the backend flask app by adding the below code to my [docker-compose.yml](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/blob/main/docker-compose.yml) file. These environment variables were added to `backend-flask` of the docker-compose.yml

```yml
OTEL_EXPORTER_OTLP_ENDPOINT: "https://api.honeycomb.io"
OTEL_EXPORTER_OTLP_HEADERS: "x-honeycomb-team=${HONEYCOMB_API_KEY}"
OTEL_SERVICE_NAME: "${HONEYCOMB_SERVICE_NAME}"
```

- #### Console Tracing

In other to start getting traces in honeycomb, I added the following lines of code to the [`app.py`](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/blob/main/backend-flask/app.py):

```py
# Honeycomb
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize tracing and an exporter that can send data to Honeycomb
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(__name__)


app = Flask(__name__)

# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
```

To run the trace I reran:

```
docker compose up
```

- #### Adding Spans and Attributes

I created spans by acquiring a tracer and spans codes from [Honecomb.io Documentation](https://docs.honeycomb.io/getting-data-in/opentelemetry/python-distro/) and added the code to my [`home_activities.py`](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/blob/main/backend-flask/services/home_activities.py). See code below:

```py
from opentelemetry import trace

tracer = trace.get_tracer("home.activities")
```

```py
with tracer.start_as_current_span("home-activities-mock-data"):
      span = trace.get_current_span()
      span.set_attribute("app.now", now.isoformat)
      ...
      ...
      span.set_attribute("app.result_length", len(results))
 ```

I also added the below code to `app.py`:

```py
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
```

```py
simple_processor = SimpleSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(simple_processor)
```

- Run Query

![backend flask trace](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/3969a3ba-9e03-4908-84da-6bc676f4b33a)


## Instrument X-Ray

- #### Install AWS X-Ray SDK

To get started with AWS X-Ray we will add the X-ray sdk to the `requirements.txt` file

```
aws-xray-sdk
```

Then run

```
pip install -r requirements.txt
```

- #### Install X-Ray Daemon

I added the below code to my `docker-compose.yml` this is so that whenever the containers are run the daemon would be installed

```py
      AWS_XRAY_URL: "*4567-${GITPOD_WORKSPACE_ID}.${GITPOD_WORKSPACE_CLUSTER_HOST}*"
      AWS_XRAY_DAEMON_ADDRESS: "xray-daemon:2000"
```

```py
  xray-daemon:
    image: "amazon/aws-xray-daemon"
    environment:
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
      AWS_REGION: "us-east-1"
    command:
      - "xray -o -b xray-daemon:2000"
    ports:
      - 2000:2000/udp
 ```

- #### X-Ray Group

To ensour that all my traces were in one place, I created an X-Ray group using the command below:

```sh
aws xray create-group \
--group-name "Cruddur" \
--filter-expression "service(\"backend-flask\")"
```

- #### Setup X-Ray Resources

I created an `xray.json` file in the aws/json folder to which I added the below lines of code:

```json
{
  "SamplingRule": {
      "RuleName": "Cruddur",
      "ResourceARN": "*",
      "Priority": 9000,
      "FixedRate": 0.1,
      "ReservoirSize": 5,
      "ServiceName": "Cruddur",
      "ServiceType": "*",
      "Host": "*",
      "HTTPMethod": "*",
      "URLPath": "*",
      "Version": 1
  }
}
```

The above code simply defines the sampling ruole to be created and the command below is the code I ran to create the sampling rule using AWS cli:

```
aws xray create-sampling-rule --cli-input-json file://aws/json/xray.json
```

After all this I proceeded to run docker compose up to see the data collected by X-Ray.

- #### Adding custom segment/subsegment

To further filter X-Ray tracing, I created a subsegment by adding codes to [`user_activities.py`](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/blob/main/backend-flask/services/user_activities.py)

```py
from aws_xray_sdk.core import xray_recorder
...
...
    now = datetime.now(timezone.utc).astimezone()
      model = {
        'errors': None,
        'data': None
      }
...
```

With this I was then able to get data in my subsegments.

![XraySubSeg](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/1a71f2c4-a536-45eb-acc5-abb5fbd32a3d)


## CloudWatch

- #### Install WatchTower

To implement cloudwatch logs first I needed to install watchtower so I added the watchtower to my `requirements.txt` file

```
watchtower
```
Next I installed it by running

```
pip install -r requirements.txt
```

- #### Configure Cloudwatch

THe next step was to configure the logger to use cloudwatch. To do this I inserted the below code into the `app.py` file:

```py
import watchtower
import logging
from time import strftime
...
...
# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
LOGGER.addHandler(console_handler)
LOGGER.addHandler(cw_handler)
LOGGER.info("some message")
...
...
@app.after_request
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response
 ...   
    data = HomeActivities.run(logger=LOGGER)
 ```
 
 I also added some codes to the `services/home_activities.py` file
 
 ```py
 import logging
 ...
 def run(logger):
    logger.info("HomeActivities")
 ```
 
Also had to add the required env vars to the `docker-compose.yml` file:
 
```py
      AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION}"
      AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
      AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
```

With all these setup, I was then able to collect the required cloudwatch logs


![CloudWatch](https://github.com/ChigozieCO/aws-bootcamp-cruddur-2023/assets/107365067/905a7c42-e380-4ed3-8734-bc83fdb9b06f)

## Rollbar

- #### Create account and set Env Vars

The first step was to create a free rollbar account on [Rollbar}(https://rollbar.com)

I then retreived the access tokens and set them to my code environment by running the below code:

```sh
export ROLLBAR_ACCESS_TOKEN="######"
gp env ROLLBAR_ACCESS_TOKEN="######"
```

- #### Install Rollbar

As usual I added the needed dependencies to my `requirements.txt` file

```
blinker
rollbar
```

Then installed the requiredments by running:

```
pip install -r requirements.txt
```

I then added env vars to the `docker-compose.yml` file

```sh
ROLLBAR_ACCESS_TOKEN: "${ROLLBAR_ACCESS_TOKEN}"
```

The next step was to integrate rollbar into our app in other to fully utilize it's error logging funtionalities. To do this i added the code below to my `app.py` file:

```py
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception
...
...
rollbar_access_token = os.getenv('ROLLBAR_ACCESS_TOKEN')
@app.before_first_request
def init_rollbar():
    """init rollbar module"""
    rollbar.init(
        # access token
        rollbar_access_token,
        # environment name
        'production',
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False)

    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
   ...
   
   
   #endpoint to test rollbar
@app.route('/rollbar/test')
def rollbar_test():
    rollbar.report_message('Hello World!', 'warning')
    return "Hello World!"
```

Then I ran `docker compose up` and was able to collect errors in my rollbar account.




