from unittest.mock import patch

from app.hardware.sparkfun_driver import SparkfunDriver
from app.models.domain.sparkfun_reading import SparkfunReading


@patch("app.hardware.sparkfun_driver.time.sleep")
@patch("app.hardware.sparkfun_driver.DigitalOutputDevice")
@patch("app.hardware.sparkfun_driver.MCP3008")
def test_get_reading_powers_sensor_and_maps_adc_value(
    mock_mcp3008,
    mock_power_device,
    mock_sleep,
) -> None:
    # Arrange
    mock_mcp3008.return_value.value = 0.73
    sensor = SparkfunDriver()

    # Act
    reading = sensor.get_reading()

    # Assert
    assert isinstance(reading, SparkfunReading)
    assert reading.soil_hydration == 0.73
    mock_mcp3008.assert_called_once_with(channel=0)
    mock_power_device.assert_called_once_with(18)
    mock_power_device.return_value.on.assert_called_once_with()
    mock_sleep.assert_called_once_with(0.1)
    mock_power_device.return_value.off.assert_called_once_with()
