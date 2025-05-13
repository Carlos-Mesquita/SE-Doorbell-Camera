from abc import ABC, abstractmethod
from asyncio import Queue, Lock, Task, CancelledError, sleep, create_task
from datetime import datetime
from logging import getLogger
from typing import Optional

from doorbell_controller.models import Event, SensorEvent


class ISensor(ABC):

    def __init__(
        self,
        event_queue: Queue[Event[SensorEvent]],
        debounce: float,
        polling_rate: float
    ):
        self._event_queue = event_queue
        self._debounce = debounce
        self._polling = polling_rate
        self._lock = Lock()
        self._running = False
        self._detection_task: Optional[Task] = None
        self._last_trigger_time = 0.0
        self._logger = getLogger(__name__)

    @property
    async def debounce(self) -> float:
        async with self._lock:
            return self._debounce

    @debounce.setter
    async def debounce(self, value: float):
        async with self._lock:
            if value < 0:
                raise ValueError("Debounce time cannot be negative")
            self._debounce = value

    @property
    async def polling_rate(self) -> float:
        async with self._lock:
            return self._polling

    @polling_rate.setter
    async def polling_rate(self, value: float):
        async with self._lock:
            if value <= 0:
                raise ValueError("Polling rate must be positive")
            self._polling = value

    async def start(self):
        async with self._lock:
            if not self._running:
                self._running = True
                self._detection_task = create_task(self._detection_loop())

    async def stop(self):
        async with self._lock:
            self._running = False
        if self._detection_task:
            self._detection_task.cancel()
            try:
                await self._detection_task
            except CancelledError:
                pass
            self._detection_task = None

    async def _detection_loop(self):
        while True:
            try:
                async with self._lock:
                    if not self._running:
                        break

                    current_polling = self._polling
                    current_debounce = self._debounce

                current_time = datetime.now().timestamp()

                if self.triggered():
                    # Only place a new alert if debounce period has passed
                    if current_time - self._last_trigger_time >= current_debounce:
                        await self._event_queue.put(Event(
                            type=self._event_type,
                            timestamp=datetime.now()
                        ))

                        self._last_trigger_time = current_time
                await sleep(current_polling)
            except CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in detection loop: {e}")

    @abstractmethod
    def triggered(self) -> bool:
        pass

    @property
    @abstractmethod
    def _event_type(self) -> SensorEvent:
        pass

    @abstractmethod
    def cleanup(self):
        pass
