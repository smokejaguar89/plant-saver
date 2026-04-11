import adafruit_tsl2591

from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver:
    # Keep this driver as a DI singleton. Multiple instances can be
    # created, but they still target one physical I2C bus/device and can
    # contend during concurrent reads.
    def __init__(self, i2c):
        self.tsl2591 = adafruit_tsl2591.TSL2591(i2c)

    def get_reading(self) -> TSL2591Reading:
        return TSL2591Reading(luminous_flux=self.tsl2591.lux)
