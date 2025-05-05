from time import sleep

class Hardware():
	'''
	Base class for all hardware interactions with the raspberry pi (or sim).
	Each hardware configuration has its own implementation of this class.
	'''
	def __init__(self):
		# Not used in production
		self.simulated_res = False
	
	def run_bac_test(self, limit = 0.2):
		'''Determine if the BAC level is too high'''
		self.simulated_res = not self.simulated_res
		sleep(2)
		return self.simulated_res
	
	def lock(self):
		print("Scooter locked")

	def unlock(self):
		print("Scooter unlocked")

	def display_success(self):
		print("Success")

	def display_failure(self):
		print("Fail")