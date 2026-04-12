from unittest.mock import MagicMock, patch

import pytest

from app.clients.news_api_client import (
    NewsApiClient,
    NewsApiClientError,
    NewsCategory,
)


def test_news_api_client_raises_when_no_api_key() -> None:
    # Act / Assert
    with (
        patch("app.clients.news_api_client.os.getenv", return_value=None),
        pytest.raises(NewsApiClientError) as error,
    ):
        NewsApiClient(api_key=None)

    assert str(error.value) == "NEWS_API_KEY is not configured."


def test_get_top_headlines_returns_titles_for_200_response() -> None:
    # Arrange
    client = NewsApiClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "articles": [
            {"title": "Headline 1"},
            {"title": "Headline 2"},
        ]
    }

    # Act
    with patch(
        "app.clients.news_api_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        headlines = client.get_top_headlines(category=NewsCategory.SCIENCE)

    # Assert
    assert headlines == ["Headline 1", "Headline 2"]
    mock_get.assert_called_once_with(
        "https://newsapi.org/v2/top-headlines",
        params={
            "category": "science",
            "apiKey": "test-key",
        },
    )


def test_get_top_headlines_raises_for_non_200_response() -> None:
    # Arrange
    client = NewsApiClient(api_key="test-key")
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.text = "rate limited"

    # Act
    with patch(
        "app.clients.news_api_client.requests.get",
        return_value=mock_response,
    ), pytest.raises(NewsApiClientError) as error:
        client.get_top_headlines(category=NewsCategory.GENERAL)

    # Assert
    assert (
        str(error.value)
        == "Error fetching top headlines: 429 - rate limited"
    )
