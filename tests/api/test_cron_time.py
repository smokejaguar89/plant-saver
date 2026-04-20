"""Tests for cron time calculation and scheduling."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.api import get_next_pull_time, update_cron_time
from app.scheduler.scheduler import IMAGE_GEN_CRON_SCHEDULE


class TestGetNextPullTime:
    """Test get_next_pull_time function for correct cron time calculation."""

    def test_returns_next_slot_when_slots_remain_today(self):
        """Test that it returns the next available slot when there are more slots today."""
        # Arrange: Set current time to 10:30 UTC
        # IMAGE_GEN_CRON_SCHEDULE = [6, 10, 14, 18, 22]
        # Next slot should be 14:00
        mock_now = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                # Preserve the datetime class itself for timedelta operations
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert - Next slot should be 14:00 UTC today
                assert result.hour == 14
                assert result.minute == 0
                assert result.second == 0
                assert result.day == mock_now.day
                assert result.month == mock_now.month
                assert result.year == mock_now.year

        asyncio.run(run_test())

    def test_returns_tomorrow_first_slot_when_all_slots_passed(self):
        """Test that it returns tomorrow's first slot when all slots have passed today."""
        # Arrange: Set current time to 23:00 UTC (after the last slot at 22:00)
        # Next slot should be tomorrow at 06:00
        mock_now = datetime(2026, 4, 20, 23, 0, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert - Next slot should be tomorrow at 06:00
                assert result.hour == 6
                assert result.minute == 0
                assert result.second == 0
                assert result.day == 21
                assert result.month == 4
                assert result.year == 2026

        asyncio.run(run_test())

    def test_skips_slots_in_past_today(self):
        """Test that it skips all slots that have already passed today."""
        # Arrange: Set current time to 15:30 UTC
        # Slots: [6, 10, 14, 18, 22]
        # 6, 10, 14 have passed (with 1 min buffer)
        # Next should be 18:00
        mock_now = datetime(2026, 4, 20, 15, 30, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert
                assert result.hour == 18
                assert result.day == 20

        asyncio.run(run_test())

    def test_first_pull_at_early_morning_slot(self):
        """Test when called very early in the morning, before first slot."""
        # Arrange: Set current time to 05:00 UTC (before first slot at 06:00)
        mock_now = datetime(2026, 4, 20, 5, 0, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert
                assert result.hour == 6
                assert result.day == 20

        asyncio.run(run_test())

    def test_near_midnight_transition(self):
        """Test behavior near midnight when transitioning to next day."""
        # Arrange: Set current time to 23:45 UTC
        # All slots past, should go to next day's first slot
        mock_now = datetime(2026, 4, 20, 23, 45, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert
                assert result.hour == 6
                assert result.day == 21

        asyncio.run(run_test())

    def test_preserves_timezone_utc(self):
        """Test that result is always in UTC timezone."""
        mock_now = datetime(2026, 4, 20, 10, 30, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert
                assert result.tzinfo == timezone.utc

        asyncio.run(run_test())

    def test_at_exactly_slot_time(self):
        """Test when current time is exactly at a slot time."""
        # Arrange: Set current time to exactly 10:00 UTC
        # Should skip this one (needs to be > now + 1 minute) and return 14:00
        mock_now = datetime(2026, 4, 20, 10, 0, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert - Should skip 10:00 due to 1-minute buffer
                assert result.hour == 14
                assert result.day == 20

        asyncio.run(run_test())

    def test_one_minute_before_slot(self):
        """Test when current time is 1 minute before a slot."""
        # Arrange: Set current time to 13:59 UTC (1 minute before 14:00 slot)
        mock_now = datetime(2026, 4, 20, 13, 59, 0, tzinfo=timezone.utc)

        async def run_test():
            with patch("app.api.api.datetime") as mock_datetime:
                mock_datetime.now.return_value = mock_now
                mock_datetime.side_effect = lambda *args, **kw: (
                    datetime(*args, **kw) if args else mock_now
                )

                # Act
                result = await get_next_pull_time()

                # Assert - Should skip to 18:00 (14:00 doesn't satisfy > now + 1min)
                assert result.hour == 18
                assert result.day == 20

        asyncio.run(run_test())


class TestUpdateCronTime:
    """Test update_cron_time function for correct payload and formatting."""

    def test_sends_iso_format_cron_time(self):
        """Test that update_cron_time sends cron_time in ISO 8601 format."""
        mock_pull_time = datetime(2026, 4, 20, 14, 0, 0, tzinfo=timezone.utc)
        captured_payload = {}

        async def mock_put(url, json, timeout):
            captured_payload.update({"payload": json})
            return MagicMock(status_code=200)

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    with patch("app.api.api.logger") as mock_logger:
                        mock_get_next.return_value = mock_pull_time
                        mock_instance = MagicMock()
                        mock_instance.__aenter__.return_value.put = AsyncMock(
                            side_effect=mock_put
                        )
                        mock_client.return_value = mock_instance

                        # Act
                        await update_cron_time()

                        # Assert
                        assert "payload" in captured_payload
                        assert (
                            captured_payload["payload"]["cron_time"]
                            == "2026-04-20T14:00:00Z"
                        )
                        # Verify logging
                        mock_logger.info.assert_called_once()

        asyncio.run(run_test())

    def test_iso_format_includes_timezone_z(self):
        """Test that cron_time includes 'Z' suffix for UTC."""
        mock_pull_time = datetime(2026, 4, 21, 6, 0, 0, tzinfo=timezone.utc)
        captured_payload = {}

        async def mock_put(url, json, timeout):
            captured_payload.update({"payload": json})
            return MagicMock(status_code=200)

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    mock_get_next.return_value = mock_pull_time
                    mock_instance = MagicMock()
                    mock_instance.__aenter__.return_value.put = AsyncMock(
                        side_effect=mock_put
                    )
                    mock_client.return_value = mock_instance

                    # Act
                    await update_cron_time()

                    # Assert
                    cron_time = captured_payload["payload"]["cron_time"]
                    assert cron_time.endswith("Z")
                    assert cron_time == "2026-04-21T06:00:00Z"

        asyncio.run(run_test())

    def test_payload_includes_all_required_fields(self):
        """Test that the payload includes all required fields."""
        mock_pull_time = datetime(2026, 4, 20, 14, 0, 0, tzinfo=timezone.utc)
        captured_payload = {}

        async def mock_put(url, json, timeout):
            captured_payload.update({"payload": json})
            return MagicMock(status_code=200)

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    mock_get_next.return_value = mock_pull_time
                    mock_instance = MagicMock()
                    mock_instance.__aenter__.return_value.put = AsyncMock(
                        side_effect=mock_put
                    )
                    mock_client.return_value = mock_instance

                    # Act
                    await update_cron_time()

                    # Assert
                    payload = captured_payload["payload"]
                    assert payload["upstream_on"] is True
                    assert "upstream_url" in payload
                    assert "token" in payload
                    assert payload["cron_time"] == "2026-04-20T14:00:00Z"

        asyncio.run(run_test())

    def test_calls_bloomin8_with_put_request(self):
        """Test that the function sends a PUT request to the correct URL."""
        mock_pull_time = datetime(2026, 4, 20, 14, 0, 0, tzinfo=timezone.utc)
        captured_url = {}

        async def mock_put(url, json, timeout):
            captured_url.update({"url": url})
            return MagicMock(status_code=200)

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    mock_get_next.return_value = mock_pull_time
                    mock_instance = MagicMock()
                    mock_instance.__aenter__.return_value.put = AsyncMock(
                        side_effect=mock_put
                    )
                    mock_client.return_value = mock_instance

                    # Act
                    await update_cron_time()

                    # Assert
                    assert (
                        captured_url["url"]
                        == "http://192.168.86.241/upstream/pull_settings"
                    )

        asyncio.run(run_test())

    def test_handles_next_day_transition_in_payload(self):
        """Test that payload correctly handles day transition."""
        # When next slot is tomorrow
        mock_pull_time = datetime(2026, 4, 21, 6, 0, 0, tzinfo=timezone.utc)
        captured_payload = {}

        async def mock_put(url, json, timeout):
            captured_payload.update({"payload": json})
            return MagicMock(status_code=200)

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    mock_get_next.return_value = mock_pull_time
                    mock_instance = MagicMock()
                    mock_instance.__aenter__.return_value.put = AsyncMock(
                        side_effect=mock_put
                    )
                    mock_client.return_value = mock_instance

                    # Act
                    await update_cron_time()

                    # Assert
                    assert (
                        captured_payload["payload"]["cron_time"]
                        == "2026-04-21T06:00:00Z"
                    )

        asyncio.run(run_test())

    def test_exception_handling_on_network_failure(self):
        """Test that exceptions are caught and logged without raising."""
        mock_pull_time = datetime(2026, 4, 20, 14, 0, 0, tzinfo=timezone.utc)

        async def mock_put_error(url, json, timeout):
            raise ConnectionError("Network failed")

        async def run_test():
            with patch("app.api.api.get_next_pull_time") as mock_get_next:
                with patch("app.api.api.httpx.AsyncClient") as mock_client:
                    with patch("app.api.api.logger") as mock_logger:
                        mock_get_next.return_value = mock_pull_time
                        mock_instance = MagicMock()
                        mock_instance.__aenter__.return_value.put = AsyncMock(
                            side_effect=mock_put_error
                        )
                        mock_client.return_value = mock_instance

                        # Act - Should not raise
                        await update_cron_time()

                        # Assert - Should have logged error
                        mock_logger.error.assert_called_once()
                        call_args = str(mock_logger.error.call_args_list)
                        assert "Schedule Update Failed" in call_args

        asyncio.run(run_test())
