import RPi.GPIO as GPIO  # type: ignore
from asyncio import Queue
from typing import Dict, Any
import logging

from doorbell_controller.exceptions import ConfigException
from doorbell_controller.models import SensorEvent, Event
from doorbell_controller.services import ISensor
from doorbell_controller.services import IPeripheral

logger = logging.getLogger(__name__)


class MotionSensorService(ISensor, IPeripheral):

    def __init__(self,
                 event_queue: Queue[Event[SensorEvent]],
                 config: Dict[str, Any]
                 ):
        try:
            self._PIN = int(config['pin'])
            debounce_ms = int(config.get('debounce_ms', 1000))
            polling_rate_hz = int(config.get('polling_rate_hz', 2))

            if polling_rate_hz <= 0:
                raise ValueError("polling_rate_hz must be positive")

            debounce_seconds = debounce_ms / 1000.0
            polling_interval_seconds = 1.0 / polling_rate_hz

            GPIO.setup(self._PIN, GPIO.IN)  # type: ignore
            logger.info(
                f"MotionSensorService initialized on BCM pin {self._PIN}. Debounce: {debounce_seconds:.2f}s, Poll Interval: {polling_interval_seconds:.2f}s")
        except (ValueError, KeyError) as e:
            logger.error(f"Configuration error for MotionSensorService: {e}", exc_info=True)
            raise ConfigException(f"MotionSensorService config error: {e}")

        super().__init__(event_queue, debounce_seconds, polling_interval_seconds)

    def triggered(self) -> bool:
        return GPIO.input(self._PIN) == GPIO.HIGH  # type: ignore

    @property
    def _event_type(self) -> SensorEvent:
        return SensorEvent.MOTION_DETECTED

    async def cleanup(self):
        logger.info(f"Cleaning up GPIO for motion sensor pin {self._PIN}.")
        await self.stop()
        try:
            GPIO.cleanup(self._PIN)  # type: ignore
        except Exception as e:
            logger.warning(f"Exception during GPIO cleanup for motion sensor pin {self._PIN}: {e}")

    async def get_config_settings(self) -> Dict[str, Any]:
        """Returns settings in the units they are typically configured (ms, Hz)"""
        base_debounce_s = await self.debounce
        base_interval_s = await self.polling_interval
        return {
            "pin": self._PIN,
            "debounce_ms": int(base_debounce_s * 1000),
            "polling_rate_hz": 1.0 / base_interval_s if base_interval_s > 0 else 0,
        }
