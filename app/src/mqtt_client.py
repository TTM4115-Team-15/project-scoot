import json
import paho.mqtt.client as mqtt
from threading import Thread

class MQTT_Client:
	def __init__(self, id, username, password):
		self.id = id
		
		self.username = username
		self.password = password

		self.client = mqtt.Client()
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message

		# self.client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
		self.client.username_pw_set(username, password)

	def on_connect(self, client, userdata, flags, rc):
		print(f"on_connect(): {mqtt.connack_string(rc)}")
		client.subscribe("choose_scooter")
		client.subscribe("lock_btn")
		client.publish("debug/app", f"Connected with ID {self.id}")

	def on_message(self, client, userdata, msg):
		print(f"MQTT topic recieved: {msg.topic}")

		msg_type = msg.topic.split("/")[0]
		payload = json.loads(msg.payload.decode("utf-8"))
		
		kwargs = {}
		if(msg_type == "available"):
			kwargs = {
				's_id':payload["s_id"],
				'loc':payload["loc"]
			}

		# Debug -> Move to app frontend
		if(msg_type == "choose_scooter"):
			print("Choosing scooter: ", payload)
			kwargs = { 
				's_id':payload["s_id"]
			}

		if(msg_type == "unlock"):
			print("Payload: ", payload)
			status = payload["status"]
			if(status == 1):
				# success
				msg_type = "unlock_ack"
				print("Unlocking succeeded")
			if(status == 2):
				# fail
				msg_type = "unlock_fail"
				print("Unlocking failed")

		self.stm_driver.send(msg_type, "app", kwargs=kwargs)

	def start(self, broker, port):
		print(f"Connecting to {broker}:{port}")

		try:
			self.client.connect(broker, port)
			print(f"Connected to MQTT broker at {broker}:{port}")
		except Exception as e:
			print(f"Failed to connect to MQTT broker at {broker}:{port}")

		try:
			thread = Thread(target=self.client.loop_forever)
			thread.start()
		except:
			print("Interrupted")
			self.client.disconnect()