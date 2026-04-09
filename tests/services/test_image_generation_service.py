import asyncio
from datetime import datetime
from unittest.mock import ANY, AsyncMock, MagicMock

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import ImageGenerationService


def test_generate_and_save_image_writes_expected_jpg_name(tmp_path) -> None:
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(return_value=snapshot)
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    database = MagicMock()
    database.save_generated_image = AsyncMock()
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
        database=database,
    )
    service.generated_image_dir = tmp_path
    service.base_image_path = tmp_path / "sunflower_base.jpg"
    service.base_image_path.write_bytes(b"base-image")
    service._craft_image_prompt = MagicMock(return_value="plant prompt")
    service._timestamp_to_string = MagicMock(
        return_value="2026-04-03:13:39"
    )

    output_path = asyncio.run(service.generate_and_save_image())

    assert output_path.name == "sunflower_2026-04-03:13:39.jpg"
    assert output_path.read_bytes() == b"jpg-bytes"
    image_client.generate_image.assert_called_once_with(
        prompt="plant prompt",
        base_image_bytes=b"base-image",
    )
    database.save_generated_image.assert_awaited_once_with(
        filename="sunflower_2026-04-03:13:39.jpg",
        generated_at=ANY,
        snapshot=snapshot,
    )


def test_get_latest_generated_image_returns_database_value() -> None:
    expected = MagicMock()
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=expected)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
    )

    generated_image = asyncio.run(service.get_latest_generated_image())

    assert generated_image == expected
    database.get_latest_generated_image.assert_awaited_once_with()


def test_timestamp_to_string_formats_date() -> None:
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
    )

    value = datetime(2026, 4, 3, 13, 39)

    assert service._timestamp_to_string(value) == "2026-04-03:13:39"


def test_craft_image_prompt_reflects_sensor_state() -> None:
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
    )

    prompt = service._craft_image_prompt(snapshot)

    assert "soil well hydrated" in prompt
    assert "bright room" in prompt
    assert "warm, comfortable atmosphere" in prompt


def test_craft_image_prompt_skips_easter_egg_when_gate_is_false() -> None:
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
    )
    service._should_include_easter_egg = MagicMock(return_value=False)
    service._get_easter_egg_prompt = MagicMock(return_value="EASTER")

    _ = service._craft_image_prompt(snapshot)

    service._get_easter_egg_prompt.assert_not_called()


def test_craft_image_prompt_calls_easter_egg_when_gate_is_true() -> None:
    snapshot = SensorSnapshot(
        temperature=26.0,
        humidity=45.0,
        light=50.0,
        moisture=40.0,
        pressure=1008.0,
    )
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=MagicMock(),
    )
    service._should_include_easter_egg = MagicMock(return_value=True)
    service._get_easter_egg_prompt = MagicMock(return_value="EASTER")

    prompt = service._craft_image_prompt(snapshot)

    service._get_easter_egg_prompt.assert_called_once_with()
    assert "EASTER" in prompt


def test_get_latest_generated_image_returns_none_when_database_empty() -> None:
    database = MagicMock()
    database.get_latest_generated_image = AsyncMock(return_value=None)
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
        database=database,
    )

    generated_image = asyncio.run(service.get_latest_generated_image())

    assert generated_image is None
    database.get_latest_generated_image.assert_awaited_once_with()
