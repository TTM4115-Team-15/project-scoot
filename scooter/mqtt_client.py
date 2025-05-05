import json
import paho.mqtt.client as mqtt

from stmpy import Machine, Driver

##
class MQTT_Client:
	'''Wrapper for MQTT'''

	def __init__(self, id, username, password):
		self.count = 0
		self.id = id

		self.username = username
		self.password = password

		self.client = mqtt.Client()
		self.client.on_connect = self.on_connect
		self.client.on_message = self.on_message

		# self.client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
		self.client.username_pw_set(username, password)

	#############
	# Callbacks #
	#############
	def on_connect(self, client, userdata, flags, rc):
		print(f"[MQTT] {mqtt.connack_string(rc)}")
		client.subscribe(f"unlock/{self.id}")
		client.subscribe(f"lock/{self.id}")
		client.subscribe("available")
		client.publish("debug/scooter", f"Connected with ID {self.id}")

	def on_message(self, client, userdata, msg):
		print(f"[MQTT] Topic: {msg.topic}")
		msg_type = msg.topic.split("/")[0]
		
		kwargs = {}
		try:
			if(msg_type == "available"):
				payload = msg.payload.decode("utf-8")
				payload = json.loads(payload)
				kwargs = {
					'user_id':payload["user_id"],
					'loc':payload["loc"]
				}
			elif(msg_type == "unlock"):
				payload = msg.payload.decode("utf-8")
				payload = json.loads(payload)
				kwargs = {
					'user_id':payload["user_id"]
				}
		except:
			print(f"Could not decode message of type '{msg_type}'")
			return

		self.stm_driver.send(msg_type, "scooter", kwargs=kwargs)

	def start(self, broker, port):
		print(f"Connecting to {broker}:{port}")
		self.client.connect(broker, port)

		try:
			self.client.loop_forever()
		except KeyboardInterrupt:
			print("Interrupted")
			self.client.disconnect()
