import json

##
class App:
	def __init__(self, mqtt_client, id, pos):
		self.id = id
		self.pos = pos
		# Consider making this null to couple at same time as stm_driver
		self.mqtt_client = mqtt_client
		self.scooters = []
		self.last_test = 0
		self.checksum = 0

	################
	# MQTT Wrapper #
	################
	def publish(self, topic, payload : dict):
		self.mqtt_client.client.publish(topic, json.dumps(payload))

	def subscribe(self, topic):
		self.mqtt_client.client.subscribe(topic)
		
	def unsubscribe(self, topic):
		self.mqtt_client.client.unsubscribe(topic)

	###########
	# Helpers #
	###########
	def log(self, msg):
		'''Print debug messages'''
		print(f"[App {self.id}] {msg}")
		
	##########
	# States #
	##########
	def on_enter_list_scooters(self):
		# TODO: Clean up
		while not self.mqtt_client.client.is_connected():
			self.mqtt_client.client.loop()

		self.subscribe(f"available/{self.id}/res")
		self.publish("available", {
			"user_id": self.id,
			"loc": self.pos # TODO: custom
		})

		self.log(f"Last test from {self.last_test}")
		self.last_test = 0
		self.checksum = 0
		self.log(f"Last test to {self.last_test}")

	def on_exit_list_scooter(self):
		self.unsubscribe(f"available/{self.id}/res")

	def add_scooter(self, s_id, loc):
		self.scooters.append({"s_id": s_id, "loc": loc})
		self.log(f"ID: {s_id}, loc: {loc}")

	def on_enter_reserving(self):
		self.log(f"Reserving: {self.active_scooter}")
		
		self.subscribe(f"unlock/{self.active_scooter}/res")
		self.publish(f"unlock/{self.active_scooter}", {
			"user_id": self.id
		})

	def on_enter_breathalyzer(self):
		# TODO: Start timer! (20 seconds?)
		self.unsubscribe(f"unlock/{self.active_scooter}")

	def on_enter_locking(self):
		self.subscribe(f"lock/{self.active_scooter}/res")
		self.publish(f"lock/{self.active_scooter}", {})

	def on_exit_locking(self):
		self.unsubscribe(f"lock/{self.active_scooter}/res")

	def save_scooter_id(self, s_id):
		self.log(f"Saving ID: {s_id}")
		self.active_scooter = s_id