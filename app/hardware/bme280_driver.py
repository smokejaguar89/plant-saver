from adafruit_bme280 import basic as adafruit_bme280

from app.models.domain.bme280_reading import BME280Reading


class BME280Driver:
    # Keep this driver as a DI singleton. Multiple instances can appear
    # to work, but they still share the same physical I2C bus/device and
    # can contend under concurrent access.
    def __init__(self, i2c):
        self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

    def get_reading(self) -> BME280Reading:
        # Placeholder value for testing
        return BME280Reading(
            ambient_temp_celsius=self.bme280.temperature,
            relative_humidity_pct=self.bme280.relative_humidity,
            barometric_pressure_hpa=self.bme280.pressure
        )
