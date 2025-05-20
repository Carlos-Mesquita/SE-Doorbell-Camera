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
            debounce_seconds: float,
            polling_interval_seconds: float
    ):
        self._event_queue = event_queue
        self._debounce_seconds = debounce_seconds
        self._polling_interval_seconds = polling_interval_seconds
        self._lock = Lock()
        self._running = False
        self._detection_task: Optional[Task] = None
        self._last_trigger_time: float = 0.0
        self._logger = getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    async def debounce(self) -> float:
        """Debounce time in seconds."""
        async with self._lock:
            return self._debounce_seconds

    @debounce.setter
    async def debounce(self, value_seconds: float):
        """Set debounce time in seconds."""
        async with self._lock:
            if value_seconds < 0:
                self._logger.warning(f"Attempted to set negative debounce time: {value_seconds}s")
                raise ValueError("Debounce time cannot be negative")
            self._debounce_seconds = value_seconds
            self._logger.info(f"Debounce time set to {self._debounce_seconds}s")

    @property
    async def polling_interval(self) -> float:
        """Polling interval in seconds."""
        async with self._lock:
            return self._polling_interval_seconds

    @polling_interval.setter
    async def polling_interval(self, value_seconds: float):
        """Set polling interval in seconds."""
        async with self._lock:
            if value_seconds <= 0:
                self._logger.warning(f"Attempted to set non-positive polling interval: {value_seconds}s")
                raise ValueError("Polling interval must be positive")
            self._polling_interval_seconds = value_seconds
            self._logger.info(f"Polling interval set to {self._polling_interval_seconds}s")

    async def start(self):
        async with self._lock:
            if self._running:
                self._logger.info("Start called but sensor is already running.")
                return
            self._running = True

            self._last_trigger_time = datetime.now().timestamp() - self._debounce_seconds
            self._detection_task = create_task(self._detection_loop(), name=f"{self.__class__.__name__}_DetectionLoop")
            self._logger.info("Sensor started.")

    async def stop(self):
        task_to_await: Optional[Task] = None
        async with self._lock:
            if not self._running and not self._detection_task:
                self._logger.info("Stop called but sensor is not running or no task exists.")
                return
            self._running = False
            if self._detection_task:
                task_to_await = self._detection_task
                self._detection_task = None

        if task_to_await and not task_to_await.done():
            task_to_await.cancel()
            try:
                await task_to_await
            except CancelledError:
                self._logger.info("Detection task cancelled successfully.")
            except Exception as e:
                self._logger.error(f"Error awaiting cancelled detection task: {e}", exc_info=True)
        self._logger.info("Sensor stopped.")

    async def _detection_loop(self):
        self._logger.debug("Detection loop started.")
        try:
            while True:
                _current_polling_interval_s: float
                _current_debounce_s: float
                _is_currently_running: bool

                async with self._lock:
                    _is_currently_running = self._running
                    _current_polling_interval_s = self._polling_interval_seconds
                    _current_debounce_s = self._debounce_seconds

                if not _is_currently_running:
                    self._logger.debug("Detection loop: running flag is false, exiting.")
                    break

                current_time_ts = datetime.now().timestamp()
                if self.triggered():
                    if (current_time_ts - self._last_trigger_time) >= _current_debounce_s:
                        event_type = self._event_type
                        self._logger.debug(f"Sensor triggered for event type: {event_type.value}. Debounce passed.")
                        await self._event_queue.put(Event(
                            type=event_type,
                            timestamp=datetime.now(),
                            source_device_id=f"{self.__class__.__name__}"
                        ))
                        self._last_trigger_time = current_time_ts
                await sleep(_current_polling_interval_s)
        except CancelledError:
            self._logger.info("Detection loop was cancelled.")
        except Exception as e:
            self._logger.error(f"Unexpected error in detection loop: {e}", exc_info=True)
        finally:
            self._logger.debug("Detection loop finished.")

    @abstractmethod
    def triggered(self) -> bool:
        """Return True if the sensor's condition is met, False otherwise."""
        pass

    @property
    @abstractmethod
    def _event_type(self) -> SensorEvent:
        """Return the SensorEvent type for this sensor."""
        pass

    @abstractmethod
    async def cleanup(self):
        """Perform any necessary cleanup for the sensor (e.g., GPIO)."""
        pass