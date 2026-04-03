from datetime import datetime
from pathlib import Path
from typing import Protocol

from fastapi.params import Depends

from app.clients.gemini_client import GeminiClient
from app.models.domain.sensor_snapshot import SensorSnapshot
from app.services.sensor_service import (
    LIGHT_THRESHOLD,
    MOISTURE_THRESHOLD,
    SensorService,
    TEMPERATURE_THRESHOLD,
)


class ImageClient(Protocol):
    def generate_image(self, prompt: str, base_image_bytes: bytes) -> bytes:
        ...


class ImageGenerationService:
    def __init__(
            self,
            sensor_service=Depends(SensorService),
            image_client: ImageClient = Depends(GeminiClient)):
        self.sensor_service = sensor_service
        self.image_client = image_client
        self.base_image_path = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "img"
            / "sunflower_base.jpg"
        )
        self.generated_image_dir = (
            Path(__file__).resolve().parents[1]
            / "static"
            / "img"
            / "gemini"
        )

    async def generate_and_save_image(self) -> Path:
        prompt = await self._craft_image_prompt()
        image_bytes = self.image_client.generate_image(
            prompt=prompt,
            base_image_bytes=self._read_base_image_bytes(),
        )
        self.generated_image_dir.mkdir(parents=True, exist_ok=True)
        filename = f"sunflower_{self._current_timestamp_string()}.jpg"
        output_path = self.generated_image_dir / filename
        output_path.write_bytes(image_bytes)
        return output_path

    def get_most_recent_image(self) -> Path | None:
        if not self.generated_image_dir.exists():
            return None

        image_paths = list(self.generated_image_dir.glob("sunflower_*.jpg"))
        if not image_paths:
            return None

        return max(image_paths, key=lambda path: path.stat().st_mtime)

    async def _craft_image_prompt(self) -> str:
        snapshot: SensorSnapshot = await self.sensor_service.get_snapshot()

        prompt = [
            (
                "Use the provided sunflower painting as the base image. "
                "Edit the scene to reflect the plant's environment."
            )
        ]

        prompt.append("#1:")
        if snapshot.moisture < MOISTURE_THRESHOLD:
            prompt.append("Make the sunflower wilt and the soil appear dry.")
        else:
            prompt.append(
                "Keep the sunflower healthy and the soil well hydrated."
            )

        prompt.append("#2:")
        if snapshot.light < LIGHT_THRESHOLD:
            prompt.append("Dim the scene to suggest a dark room.")
        else:
            prompt.append("Brighten the scene to suggest strong daylight.")

        prompt.append("#3:")
        if snapshot.temperature < TEMPERATURE_THRESHOLD:
            prompt.append("Add a cool, chilly atmosphere to the image.")
        else:
            prompt.append("Add a warm, comfortable atmosphere to the image.")

        return " ".join(prompt)

    def _read_base_image_bytes(self) -> bytes:
        return self.base_image_path.read_bytes()

    def _current_timestamp_string(self) -> str:
        return datetime.now().strftime("%Y-%m-%d:%H:%M")
