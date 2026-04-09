import time

from gpiozero import MCP3008, DigitalOutputDevice

from app.models.domain.sparkfun_reading import SparkfunReading


class SparkfunDriver:
    def __init__(self):
        self.mcp3008 = MCP3008(channel=0)
        # GPIO pin 18 for power control
        self.sparkfun_power = DigitalOutputDevice(18)

    def get_reading(self) -> SparkfunReading:
        # Placeholder value for testing
        self.sparkfun_power.on()  # Power on the sensor
        time.sleep(0.1)  # Wait for the sensor to stabilize
        reading = SparkfunReading(soil_hydration=self.mcp3008.value)
        self.sparkfun_power.off()  # Power off the sensor to prevent corrosion
        return reading
