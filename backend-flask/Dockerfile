ARG baseimage
FROM ${baseimage}

# Inside the container
# Make a new folder inside the container
WORKDIR /backend-flask

# Outside container to inside the container
# Copy the libraries we want to install to run the app from outside the container, copy then into the container
COPY requirements.txt requirements.txt

# Inside the container
# Install the python libraries used for the app inside the container
RUN pip3 install -r requirements.txt

# Outside container to inside the container
COPY . .

ENV FLASK_DEBUG=1

EXPOSE ${PORT}
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=4567"]