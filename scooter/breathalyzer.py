import RPi.GPIO as GPIO
from time import sleep

# name pins
clock = 11
miso = 5
cs = 8
green_light = 6
red_light = 19

from hardware import Hardware

class Breathalyzer(Hardware):
    def __init__(self):
        # set up pins
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(11, GPIO.OUT)
        GPIO.setup(5,GPIO.IN)
        GPIO.setup(8,GPIO.OUT)
        GPIO.setup(6,GPIO.OUT)
        GPIO.setup(19,GPIO.OUT)

        # bring clock and cs high
        GPIO.output(clock, True)
        GPIO.output(cs, True)

    def run_bac_test(self, limit = 0.2):
        readings = []

        print("Starting breathalyzer measurement for 10 seconds at 100 samples/sec...")
        for _ in range(1000):  # 1000 readings over 10 seconds
            GPIO.output(cs, False)

            voltage_bits = ""

            for _ in range(15):
                GPIO.output(clock, False)
                voltage_bits += "1" if GPIO.input(miso) else "0"
                GPIO.output(clock, True)

            voltage_bits = voltage_bits.strip()[2:14]
            voltage = int(voltage_bits, 2) * (5 / 2048)

            # Estimate promille from voltage
            promille = (voltage - 0.4) * (2.0 / 3.0)  # Simple linear map
            promille = max(promille, 0.0)  # No negative promille

            readings.append(promille)

            GPIO.output(cs, True)
            sleep(0.01)  # 0.01 sec = 100 Hz

        avg_promille = sum(readings) / len(readings)
        print(f"Avg. BAC over 10 seconds: {avg_promille:.3f}")
        
        return avg_promille < limit
        
    def display_success(self):
        GPIO.output(green_light, True)
        sleep(4)
        GPIO.output(green_light, False)
    
    def display_failure(self):
        GPIO.output(red_light, True)
        sleep(4)
        GPIO.output(red_light, False)