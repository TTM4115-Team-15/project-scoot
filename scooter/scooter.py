import json
from stmpy import Machine, Driver # type: ignore
from hardware import Hardware # Replace the next line with this to simulate
# from breathalyzer import Breathalyzer as Hardware
from mqtt_client import MQTT_Client

class Scooter:
	'''Implements the statemachine for the scooter'''

	def __init__(self, mqtt_client : MQTT_Client, id : int, pos = [63.4177, 10.4921809], debug = True):
		self.driver = None
		self.id = id
		self.pos = pos
		self.debug = debug

		self.hardware = Hardware()

		# Consider making this null to couple at same time as stm_driver
		self.mqtt_client = mqtt_client
		self.mqtt_client.stm_driver = self.get_driver() # TODO: Clean up circular references

	def on_enter_available(self):
		self.mqtt_client.client.subscribe("available")
		self.mqtt_client.client.publish("debug", f"[Scooter {self.id}] is now available")

	def on_exit_available(self):
		self.mqtt_client.client.unsubscribe("available")
		self.mqtt_client.client.publish("debug", f"[Scooter {self.id}] is no longer available")

	def on_enter_reserved(self, user_id):
		self.mqtt_client.client.publish(f"unlock/{self.id}/res", json.dumps({
			"user_id": user_id,
			"status": 0 # Reserved (ACK)
		}))
		self.log(f"Reserving for {user_id}")

		bac_level = self.hardware.run_bac_test(limit = 0.2)
		self.log(f"BAC test: {"passed" if bac_level else "failed"}")

		if(bac_level):
			self.driver.send("BAC_success", "scooter")
		else:
			self.driver.send("BAC_fail", "scooter")
			self.hardware.display_failure()

	def on_enter_riding(self):
		self.hardware.unlock()
		self.hardware.display_success()

	def on_exit_riding(self):
		self.hardware.lock()
		self.hardware.display_success()
		self.mqtt_client.client.publish(f"lock/{self.id}/res", json.dumps({"status":"gucci"}))

	def geo_check_distance(self, user_id, loc):
		x, y = loc[0], loc[1]
		maxDistance = 75
		distanceSqrMag = (self.pos[0] - x)**2 + (self.pos[1] - y)**2

		if(distanceSqrMag < maxDistance**2):
			self.log(f"Scooter is close enough ({distanceSqrMag**(1/2)})")
			payload = json.dumps({ "s_id":self.id, "loc":self.pos })
			self.mqtt_client.client.publish(f"available/{user_id}/res", payload)
		else:
			self.log("Scooter is too far away :(")
			self.log(f"{distanceSqrMag**(1/2)} / {maxDistance}")

		return "available"

	def log(self, msg):
		if (self.debug):
			print(f"[Scooter {self.id}] {msg}")

	def send_bac(self, success):
		self.log(f"BAC Status: {success}")
		self.mqtt_client.client.publish(f"unlock/{self.id}/res", json.dumps({
			# 1 = success, 2 = fail
			"status": 1 if success else 2
		}))

	#######
	# API #
	#######
	def get_driver(self):
		if self.driver:
			return self.driver

		transitions = [
			{'source':'initial', 'target':'available'},
			{'trigger':'unlock', 'source':'available', 'target':'reserved', 'effect':'on_enter_reserved(*)'},
			{'trigger':'BAC_fail', 'source':'reserved', 'target':'available', 'effect':'send_bac(False)'},
			{'trigger':'BAC_success', 'source':'reserved', 'target':'riding', 'effect':'send_bac(True)'},
			{'trigger':'lock', 'source':'riding', 'target':'available'},
		]

		states = [
			{'name':'available', 'entry':'on_enter_available', 'exit':'on_exit_available', 'available':'geo_check_distance(*)'},
			{'name':'riding', 'entry':'on_enter_riding', 'exit':'on_exit_riding'},
		]

		stm = Machine(transitions=transitions, states=states, obj=self, name="scooter")

		driver = Driver()
		driver.add_machine(stm)
		self.driver = driver

		return self.driver