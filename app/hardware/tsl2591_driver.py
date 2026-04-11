import adafruit_tsl2591

from app.hardware.driver_protocols import LockedI2CBusDriver
from app.hardware.locked_i2c_bus import LockedI2CBus
from app.models.domain.tsl2591_reading import TSL2591Reading


class TSL2591Driver(LockedI2CBusDriver[TSL2591Reading]):
    # Multiple driver instances are safe as long as they all share the
    # same LockedI2CBus. The shared bus wrapper is what serializes I2C
    # access; DI singleton usage here is mainly for consistency.
    def __init__(self, i2c_bus: LockedI2CBus):
        self._i2c_bus = i2c_bus
        self.tsl2591 = adafruit_tsl2591.TSL2591(i2c_bus.raw_bus)

    def get_reading(self) -> TSL2591Reading:
        def _read() -> TSL2591Reading:
            return TSL2591Reading(luminous_flux=self.tsl2591.lux)

        return self._i2c_bus.run(_read)
