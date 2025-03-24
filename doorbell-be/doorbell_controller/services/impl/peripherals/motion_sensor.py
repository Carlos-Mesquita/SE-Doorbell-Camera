import RPi.GPIO as GPIO

from queue import Queue
from typing import Dict, Any

from doorbell_controller.exceptions import ConfigException
from doorbell_controller.models import SensorEvent, Event
from doorbell_controller.services import IPeripheral, ISensor


class MotionSensorService(IPeripheral, ISensor):

    def __init__(self,
        event_queue: Queue[Event[SensorEvent]],
        config: Dict[str, Any]
    ):
        try:
            self._PIN = int(config['pin'])
            self._DEBOUNCE = int(config['debounce'])
            self._POLLING = int(config['polling_rate'])

            GPIO.setup(self._PIN, GPIO.IN) # type: ignore
        except ValueError:
            raise ConfigException("motion_sensor")

        super().__init__(event_queue, self._DEBOUNCE, self._POLLING)


    def triggered(self) -> bool:
        return GPIO.input(self._PIN) # type: ignore

    @property
    def _event_type(self) -> SensorEvent:
        return SensorEvent.MOTION_DETECTED

    def cleanup(self):
        GPIO.cleanup([self._PIN]) # type: ignore
