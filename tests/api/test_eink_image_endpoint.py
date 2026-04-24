import asyncio
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api import router
from app.dependencies import get_image_generation_service
from app.models.domain.generated_image import GeneratedImageMetadata
from app.services.image_generation_service import ImageGenerationService


@pytest.fixture
def image_service_mock():
    """Mock ImageGenerationService for testing."""
    service = MagicMock(spec=ImageGenerationService)
    return service


@pytest.fixture
def app(image_service_mock):
    """Create FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_image_generation_service] = lambda: (
        image_service_mock
    )
    return app


@pytest.fixture
def client(app):
    """Create TestClient for the app."""
    return TestClient(app)


@pytest.fixture
def gemini_image_dir():
    """Create gemini image directory with test image file."""
    gemini_dir = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "static"
        / "img"
        / "gemini"
    )
    gemini_dir.mkdir(parents=True, exist_ok=True)

    image_path = gemini_dir / "test_image.jpg"
    image_path.write_bytes(b"fake JPG content")

    yield gemini_dir, image_path

    # Cleanup
    if image_path.exists():
        image_path.unlink()


def test_eink_pull_returns_200_with_valid_image(
    client, image_service_mock, gemini_image_dir
):
    """Test that eink_pull returns 200 status code with valid image."""
    gemini_dir, image_path = gemini_image_dir

    # Arrange
    image_service_mock.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImageMetadata(
            filename="test_image.jpg",
            generated_at=datetime.now(),
        )
    )

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json()["data"]["image_url"] is not None


def test_eink_pull_calls_image_service(
    client, image_service_mock, gemini_image_dir
):
    """Test that eink_pull calls the image generation service."""
    gemini_dir, image_path = gemini_image_dir

    # Arrange
    image_service_mock.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImageMetadata(
            filename="test_image.jpg",
            generated_at=datetime.now(),
        )
    )

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    image_service_mock.get_latest_generated_image.assert_called_once()
    assert response.status_code == 200


def test_eink_pull_has_correct_media_type_header(
    client, image_service_mock, gemini_image_dir
):
    """Test that eink_pull response has application/json media type."""
    gemini_dir, image_path = gemini_image_dir

    # Arrange
    image_service_mock.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImageMetadata(
            filename="test_image.jpg",
            generated_at=datetime.now(),
        )
    )

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    assert response.headers["content-type"] == "application/json"


def test_eink_pull_returns_file_with_correct_filename(
    client, image_service_mock, gemini_image_dir
):
    """Test that eink_pull response includes correct filename in URL."""
    gemini_dir, image_path = gemini_image_dir

    # Arrange
    image_service_mock.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImageMetadata(
            filename="test_image.jpg",
            generated_at=datetime.now(),
        )
    )

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert
    assert response.status_code == 200
    assert "test_image.jpg" in response.json()["data"]["image_url"]


def test_eink_pull_has_correct_route_path(app):
    """Test that the eink_pull endpoint is registered at correct path."""
    # Verify the route exists
    routes = [route.path for route in app.routes]
    assert "/api/images/eink_pull" in routes


def test_eink_pull_has_get_method(app):
    """Test that the eink_pull endpoint only accepts GET."""
    from fastapi.routing import APIRoute

    eink_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute)
        and route.path == "/api/images/eink_pull"
    ]
    assert len(eink_routes) == 1
    assert "GET" in eink_routes[0].methods


def test_eink_pull_service_receives_correct_dependency(
    image_service_mock, gemini_image_dir
):
    """Test that the service dependency is correctly injected."""
    gemini_dir, image_path = gemini_image_dir

    # Arrange
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_image_generation_service] = lambda: (
        image_service_mock
    )
    client = TestClient(app)

    image_service_mock.get_latest_generated_image = AsyncMock(
        return_value=GeneratedImageMetadata(
            filename="test_image.jpg",
            generated_at=datetime.now(),
        )
    )

    # Act
    response = client.get("/api/images/eink_pull")

    # Assert - Verify the service was called
    assert image_service_mock.get_latest_generated_image.called
