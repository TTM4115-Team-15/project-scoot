import os
import time
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app import App
from mqtt_client import MQTT_Client

# --- Logging Setup ---
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

# Configure console handler with formatter
if not logger.handlers:
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# --- FastAPI App Setup ---
app = FastAPI()

# Disable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Global Variables ---
broker = os.getenv("MQTT_BROKER", "localhost")
port = int(os.getenv("MQTT_PORT", "8883"))
username = os.getenv("MQTT_USER", "scooter_app")
password = os.getenv("MQTT_PASS", "")

# TODO: Refactor
# This only works with 1 active user as it is a mock-up
backend = None
driver = None

# --- Translation Layer ---
@app.post("/available")
async def get_available_scooters(data: Dict):
    global backend, driver

    if(backend and len(backend.scooters) > 0):
        # This can cause some issues if the frontend is "out of sync"
        print("Returning cache: {backend.scooters}")
        return backend.scooters
    
    # Set up instance
    id = data["user_id"]
    loc = data["location"]

    myclient = MQTT_Client(id, username, password)
    backend = App(myclient, id, loc)

    # MQTT Client coupling
    driver = backend.get_driver()
    myclient.stm_driver = driver

    # Start
    driver.start()
    myclient.start(broker, port)

    # Wait for results and return them
    for _ in range(10): # Timeout in 5 seconds
        if len(backend.scooters) > 0:
            break
        print("Searching for scooters...")
        time.sleep(0.5)
    
    return backend.scooters

    
@app.post("/choose_scooter")
async def choose_scooter(data: Dict):
    driver.send("choose_scooter", "app", kwargs=data)
    return {"ACK":"ACK"}


@app.get("/bac")
async def choose_scooter():
    return {"status": backend.ui_state}


@app.get("/lock")
async def choose_scooter():
    driver.send("lock_btn", "app")
    return {"ACK": "ok"}