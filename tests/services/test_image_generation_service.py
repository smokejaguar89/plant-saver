import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.image_generation_service import ImageGenerationService


def test_generate_and_save_image_writes_expected_jpg_name(tmp_path) -> None:
    sensor_service = MagicMock()
    image_client = MagicMock()
    image_client.generate_image = MagicMock(return_value=b"jpg-bytes")
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=image_client,
    )
    service.generated_image_dir = tmp_path
    service._craft_image_prompt = AsyncMock(return_value="plant prompt")
    service._read_base_image_bytes = MagicMock(return_value=b"base-image")
    service._current_timestamp_string = MagicMock(
        return_value="2026-04-03:13:39"
    )

    output_path = asyncio.run(service.generate_and_save_image())

    assert output_path.name == "sunflower_2026-04-03:13:39.jpg"
    assert output_path.read_bytes() == b"jpg-bytes"
    image_client.generate_image.assert_called_once_with(
        prompt="plant prompt",
        base_image_bytes=b"base-image",
    )


def test_get_most_recent_image_returns_recent_image(tmp_path) -> None:
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
    )
    service.generated_image_dir = tmp_path
    recent_image = tmp_path / "sunflower_2026-04-03:13:39.jpg"
    recent_image.write_bytes(b"existing")

    output_path = service.get_most_recent_image()

    assert output_path == recent_image


def test_get_most_recent_image_returns_latest_image(tmp_path) -> None:
    service = ImageGenerationService(
        sensor_service=MagicMock(),
        image_client=MagicMock(),
    )
    service.generated_image_dir = tmp_path
    older_image = tmp_path / "sunflower_2026-04-03:12:00.jpg"
    older_image.write_bytes(b"old")
    latest_image = tmp_path / "sunflower_2026-04-03:13:39.jpg"
    latest_image.write_bytes(b"new")

    output_path = service.get_most_recent_image()

    assert output_path == latest_image


def test_craft_image_prompt_reflects_sensor_state() -> None:
    sensor_service = MagicMock()
    sensor_service.get_snapshot = AsyncMock(
        return_value=SensorSnapshot(
            temperature=26.0,
            humidity=45.0,
            light=50.0,
            moisture=40.0,
            pressure=1008.0,
        )
    )
    service = ImageGenerationService(
        sensor_service=sensor_service,
        image_client=MagicMock(),
    )

    prompt = asyncio.run(service._craft_image_prompt())

    assert "soil well hydrated" in prompt
    assert "strong daylight" in prompt
    assert "warm, comfortable atmosphere" in prompt
