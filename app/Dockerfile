FROM alpine:3.21

# Install Python, pip, and virtualenv
RUN apk add --no-cache python3 py3-pip py3-virtualenv build-base

WORKDIR /usr/src/app
ADD requirements.txt .
ADD src .

# Create and activate a virtual environment, then install requirements
RUN python3 -m venv /venv \
 && . /venv/bin/activate \
 && pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Variables
ENV MQTT_BROKER=localhost
ENV MQTT_PORT=8883
ENV MQTT_USER=scooter_app
ENV MQTT_PASS=Powerpuffs100

# Run the app using Uvicorn
CMD ["/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]