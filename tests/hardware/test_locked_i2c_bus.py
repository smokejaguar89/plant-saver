import threading
import time
from unittest.mock import patch

from app.hardware.locked_i2c_bus import LockedI2CBus


@patch("app.hardware.locked_i2c_bus.board.I2C")
def test_default_constructor_creates_board_i2c_bus(mock_board_i2c):
    # Arrange
    mock_bus = object()
    mock_board_i2c.return_value = mock_bus

    # Act
    i2c_bus = LockedI2CBus()

    # Assert
    assert i2c_bus.raw_bus is mock_bus
    mock_board_i2c.assert_called_once_with()


def test_run_serializes_concurrent_operations():
    # Arrange
    i2c_bus = LockedI2CBus(bus=object())
    # Set when the first operation has entered the critical section.
    first_operation_entered = threading.Event()
    # Set when the second operation actually starts running.
    second_operation_entered = threading.Event()
    # Controls when the first operation is allowed to finish.
    release_first_operation = threading.Event()

    def first_operation():
        # Signal that the first operation now holds the lock via run().
        first_operation_entered.set()
        # Stay inside the critical section until the test allows us out.
        release_first_operation.wait(timeout=1)
        return "first"

    def second_operation():
        # If this is set too early, the lock did not serialize access.
        second_operation_entered.set()
        return "second"

    # Act
    # Start one thread that enters run() and holds the lock open.
    first_thread = threading.Thread(
        target=lambda: i2c_bus.run(first_operation),
    )
    # Start a second thread that should block on the same lock.
    second_thread = threading.Thread(
        target=lambda: i2c_bus.run(second_operation),
    )
    first_thread.start()
    # Wait until the first operation is definitely inside run().
    assert first_operation_entered.wait(timeout=1)
    second_thread.start()
    # Give the second thread a brief chance to run if locking is broken.
    time.sleep(0.05)

    # Assert the second operation has not started yet because it should
    # still be blocked waiting for the first thread to release the lock.
    assert not second_operation_entered.is_set()

    # Allow the first operation to complete, which releases the lock.
    release_first_operation.set()
    first_thread.join(timeout=1)
    second_thread.join(timeout=1)

    # Now the second operation should have been allowed to run.
    assert second_operation_entered.is_set()


def test_run_releases_lock_when_operation_raises():
    # Arrange
    i2c_bus = LockedI2CBus(bus=object())

    def failing_operation():
        raise RuntimeError("boom")

    # Act / Assert
    try:
        i2c_bus.run(failing_operation)
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass

    # If lock was not released, this call would deadlock.
    result = i2c_bus.run(lambda: 42)
    assert result == 42
