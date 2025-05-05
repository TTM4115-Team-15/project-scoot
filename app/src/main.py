import os
import time
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app import App
from mqtt_client import MQTT_Client
from stmpy import Machine, Driver

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
broker = os.getenv("MQTT_BROKER")
port = int(os.getenv("MQTT_PORT", "8883"))
username = os.getenv("MQTT_USER", "scooter_app")
password = os.getenv("MQTT_PASS", "")

# TODO: Refactor
# This only works with 1 active user as it is a mock-up
backend = None
driver = None

# --- API ---
@app.post("/available")
async def get_available_scooters(data: Dict):
    global backend, driver

    if(backend):
        return backend.scooters
    
    ##### 
    id = data["user_id"]
    loc = data["location"]

    myclient = MQTT_Client(id, username, password)
    backend = App(myclient, id, loc)

    # Scooter state machine
    transitions = [
        {'source':'initial', 'target':'list scooters', 'effect':'log("A")'},
        {'trigger':'choose_scooter', 'source':'list scooters', 'target':'reserving', 'effect':'save_scooter_id(*)'},
        {'trigger':'unlock', 'source':'reserving', 'target':'breathalyzer', 'effect':'log("Confirmed scooter reservation")'},
        {'trigger':'unlock_ack', 'source':'breathalyzer', 'target':'riding', 'effect':'log("Unlocked scooter!")'},
        {'trigger':'unlock_fail', 'source':'breathalyzer', 'target':'list scooters', 'effect':'log("Failed bac test!")'},
        {'trigger':'lock_btn', 'source':'riding', 'target':'locking', 'effect':'log("Locking scooter")'},
        {'trigger':'lock', 'source':'locking', 'target':'list scooters', 'effect':'log("Locked scooter")'}
    ]

    states = [
        {'name':'list scooters', 'entry':'on_enter_list_scooters', 'exit':'on_exit_list_scooter', 'available':'add_scooter(*)'},
        {'name':'reserving', 'entry':'on_enter_reserving'},
        {'name':'locking', 'entry':'on_enter_locking', 'exit':'on_exit_locking'},
    ]

    app_stm = Machine(transitions=transitions, states=states, obj=backend, name="app")
    backend.stm = app_stm

    driver = Driver()
    driver.add_machine(app_stm)

    # MQTT Client coupling
    myclient.stm_driver = driver

    # Start
    driver.start()
    myclient.start(broker, port)

    # Wait for results and return them
    # while True:
    #     if len(backend.scooters) > 0:
    #         break
    #     print("Searching for scooters...")
    time.sleep(3)
    
    return backend.scooters

    
@app.post("/choose_scooter")
async def choose_scooter(data: Dict):
    driver.send("choose_scooter", "app", kwargs=data)
    return {"ACK":"ACK"}


@app.get("/bac")
async def choose_scooter():
    if(backend.checksum == 10):
        return {"status": 1}
    if(backend.last_test == 0):
        return {"status": 0}
    return {"status": -1}


@app.get("/lock")
async def choose_scooter():
    driver.send("lock_btn", "app")
    return {"ACK": "ok"}