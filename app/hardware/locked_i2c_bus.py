import threading
from _thread import LockType
from typing import Callable, TypeVar

import board

T = TypeVar("T")


class LockedI2CBus:
    """Shared I2C bus wrapper that serializes access with a lock.

    This is the key shared object for I2C safety: multiple sensor driver
    instances can coexist as long as they all use the same bus wrapper.
    """

    def __init__(self, bus=None, lock: LockType | None = None):
        self.raw_bus = bus if bus is not None else board.I2C()
        self._lock = lock or threading.Lock()

    def run(self, operation: Callable[[], T]) -> T:
        with self._lock:
            return operation()
