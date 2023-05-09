# Week 2 — Distributed Tracing

This week we implemented distributed tracing into our app. This is necessary as a way to easily troubleshoot because as the app services grows it could become really difficult and time consuming to locate issues.

## Instrument HoneyComb

- #### Setup account and create environment

To use Honeycomb for distributed tracing, the first step was to create an account on [honeycomb](https://www.honeycomb.io/).

Honeycomb has both the free and trial versaion and for this project I created a trial version account.

Honeycomb comes with a default environment called test but I created a specific environment which I named bootcamp to use for this project.

![Honeycomb bootcamp environment](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/1d66b131-f90a-424b-92bc-30c3d8903b02)


After creating this environment I was then able to take the Api key for the enviroment and export to my gitpod environment using the below code.

```sh
export HONEYCOMB_API_KEY="######"
export HONEYCOMB_SERVICE_NAME="Cruddur"
gp env HONEYCOMB_API_KEY="#######"
gp env HONEYCOMB_SERVICE_NAME="Cruddur"
```

The export command exports to the present environment while the gp command is used to persist the Api key to the gitpod environment so that even if I close down the this environment, the next environmment will still have the Api key variable.


- #### Implement Open Telemetry (OTEL)

To install the Open Telemetry (OTEL) dependencies I added the below lines of code to the [`requirements.txt`](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/blob/main/backend-flask/requirements.txt)

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

To use Open Telemetry (OTEL) with Honeycomb as provider I had to configure the backend flask app by adding the below code to my [docker-compose.yml](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/blob/main/docker-compose.yml) file. These environment variables were added to `backend-flask` of the docker-compose.yml

```yml
OTEL_EXPORTER_OTLP_ENDPOINT: "https://api.honeycomb.io"
OTEL_EXPORTER_OTLP_HEADERS: "x-honeycomb-team=${HONEYCOMB_API_KEY}"
OTEL_SERVICE_NAME: "${HONEYCOMB_SERVICE_NAME}"
```

- #### Console Tracing

In other to start getting traces in honeycomb, I added the following lines of code to the [`app.py`](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/blob/main/backend-flask/app.py):

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

I created spans by acquiring a tracer and spans codes from [Honecomb.io Documentation](https://docs.honeycomb.io/getting-data-in/opentelemetry/python-distro/) and added the code to my [`home_activities.py`](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/blob/main/backend-flask/services/home_activities.py). See code below:

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

![backend flask trace](https://github.com/TheGozie/aws-bootcamp-cruddur-2023/assets/107365067/3969a3ba-9e03-4908-84da-6bc676f4b33a)


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



 
