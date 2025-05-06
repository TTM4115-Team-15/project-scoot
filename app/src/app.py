import json
from stmpy import Machine, Driver

##
class App:
	def __init__(self, mqtt_client, id, pos):
		self.id = id
		self.pos = pos
		# TODO: Consider making this None to couple at same time as stm_driver
		self.mqtt_client = mqtt_client
		self.scooters = []
		self.instance = None

		# Used by the app UI (frontend)
		self.ui_state = 0

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
		
	def add_scooter(self, s_id, loc):
		self.scooters.append({"s_id": s_id, "loc": loc})
		self.log(f"ID: {s_id}, loc: {loc}")

	def save_scooter_id(self, s_id):
		self.log(f"Saving ID: {s_id}")
		self.active_scooter = s_id
		
	###############
	# Transitions #
	###############
	def on_enter_list_scooters(self):
		while not self.mqtt_client.client.is_connected():
			self.mqtt_client.client.loop()

		self.subscribe(f"available/{self.id}/res")
		self.publish("available", {
			"user_id": self.id,
			"loc": self.pos
		})

		# UI shows "Failed BAC"
		self.ui_state = 0

	def on_exit_list_scooter(self):
		self.unsubscribe(f"available/{self.id}/res")

	# TODO: Start timer/use scooters last will to reset app on disconnect
	def on_enter_reserving(self):
		self.log(f"Reserving scooter {self.active_scooter}")
		self.subscribe(f"unlock/{self.active_scooter}/res")
		self.publish(f"unlock/{self.active_scooter}", {
			"user_id": self.id
		})

		# UI shows "Running BAC"
		self.ui_state = -1

	def on_exit_breathalyzer(self):
		self.unsubscribe(f"unlock/{self.active_scooter}/res")

	def on_enter_locking(self):
		self.subscribe(f"lock/{self.active_scooter}/res")
		self.publish(f"lock/{self.active_scooter}", {})

	def on_exit_locking(self):
		self.unsubscribe(f"lock/{self.active_scooter}/res")

	def on_enter_riding(self):
		# UI shows "Unlocking scooter"
		self.ui_state = 1

	##########
	# Driver #
	##########
	def get_driver(self):
		if self.instance:
			return self.instance

		transitions = [
			{'source':'initial', 'target':'list scooters'},
			{'trigger':'choose_scooter', 'source':'list scooters', 'target':'reserving', 'effect':'save_scooter_id(*)'},
			{'trigger':'unlock', 'source':'reserving', 'target':'breathalyzer', 'effect':'log("Confirmed scooter reservation")'},
			{'trigger':'unlock_ack', 'source':'breathalyzer', 'target':'riding', 'effect':'log("Ride started")'},
			{'trigger':'unlock_fail', 'source':'breathalyzer', 'target':'list scooters', 'effect':'log("Failed bac test!")'},
			{'trigger':'lock_btn', 'source':'riding', 'target':'locking', 'effect':'log("Locking scooter")'},
			{'trigger':'lock', 'source':'locking', 'target':'list scooters', 'effect':'log("Ride ended")'}
		]

		states = [
			{'name':'list scooters', 'entry':'on_enter_list_scooters', 'exit':'on_exit_list_scooter', 'available':'add_scooter(*)'},
			{'name':'breathalyzer', 'exit':'on_exit_breathalyzer'},
			{'name':'reserving', 'entry':'on_enter_reserving'},
			{'name':'locking', 'entry':'on_enter_locking', 'exit':'on_exit_locking'},
        	{'name':'riding', 'entry':'on_enter_riding'},
		]

		stm = Machine(transitions=transitions, states=states, obj=self, name="app")

		driver = Driver()
		driver.add_machine(stm)
		self.instance = driver

		return self.instance