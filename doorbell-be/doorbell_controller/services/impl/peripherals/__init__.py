import asyncio

from logging import getLogger
from typing import Optional, Dict, Any

from .button import ButtonService
from .motion_sensor import MotionSensorService
from .rbg import RGBService
from .camera import CameraService

from doorbell_controller.models import (
    Event, SensorEvent, SettingsEvent, ControllerState
)
from doorbell_controller.services import (
    ISensor, SensorService, RGBService, CameraService
)


class PeripheralsService:
    def __init__(
        self,
        button_service: SensorService,
        motion_service: SensorService,
        rgb_service: RGBService,
        camera_service: CameraService,
        stop_motion_duration: int
    ):
        self._button_service = button_service
        self._motion_service = motion_service
        self._rgb_service = rgb_service
        self._camera_service = camera_service

        self._stop_event = asyncio.Event()
        self._state_lock = asyncio.Lock()

        self._state = ControllerState.IDLE

        self._recording_task: Optional[asyncio.Task] = None
        self._recording_duration = stop_motion_duration

        self._button_task: Optional[asyncio.Task] = None
        self._motion_task: Optional[asyncio.Task] = None

        self._logger = getLogger(__name__)

    @property
    async def state(self) -> ControllerState:
        async with self._state_lock:
            return self._state

    async def _transition_to(self, new_state: ControllerState):
        async with self._state_lock:
            old_state = self._state
            self._state = new_state

            if old_state != new_state:
                self._logger.debug(f"State transition: {old_state.value} -> {new_state.value}")
                if self._state in [ControllerState.STREAMING, ControllerState.RECORDING]:
                    await self._rgb_service.turn_on()
                else:
                    await self._rgb_service.turn_off()

    async def _run_sensor(self, service: ISensor, name: str):
        while not self._stop_event.is_set():
            try:
                await service.start()
            except Exception as e:
                self._logger.error(f"{name} service error: {e}")
                await asyncio.sleep(5)

    async def handle_sensor_event(self, event: Event[SensorEvent]):
        if isinstance(event.type, SensorEvent):
            async with self._state_lock:
                if self._state == ControllerState.IDLE:
                    await self._begin_or_reset_recording()

    async def handle_settings_event(self, event: Event[SettingsEvent]) -> Optional[Dict[str, Any]]:
        if isinstance(event.type, SettingsEvent):
            if event.type == SettingsEvent.CHANGE_SETTINGS:
                if 'button' in event.payload:
                    if 'debounce' in event.payload['button']:
                        self._button_service.debounce = event.payload['button']['debounce']
                    if 'polling_rate' in event.payload['button']:
                        self._button_service.polling_rate = event.payload['button']['polling_rate']

                if 'motion_sensor' in event.payload:
                    if 'debounce' in event.payload['motion_sensor']:
                        self._motion_service.debounce = event.payload['motion_sensor']['debounce']
                    if 'polling_rate' in event.payload['motion_sensor']:
                        self._motion_service.polling_rate = event.payload['motion_sensor']['polling_rate']

                if 'camera' in event.payload:
                    if 'bitrate' in event.payload['camera']:
                        self._camera_service.bitrate = event.payload['camera']['bitrate']
                    if 'stop_motion' in event.payload['camera']:
                        if 'interval' in event.payload['camera']['stop_motion']:
                            self._camera_service.interval = event.payload['camera']['stop_motion']['interval']
                        if 'duration' in event.payload['camera']['stop_motion']:
                            self._recording_duration = event.payload['camera']['stop_motion']['duration']

                if 'color' in event.payload and all(key in event.payload['color'] for key in ['r', 'g', 'b']):
                    self._rgb_service.change_color(
                        event.payload['color']['r'],
                        event.payload['color']['g'],
                        event.payload['color']['b']
                    )

            elif event.type == SettingsEvent.GET_SETTINGS:
                return {
                    'color': self._rgb_service.get_color(),
                    'camera': {
                        'bitrate': self._camera_service.bitrate,
                        'stop_motion': {
                            'interval': self._camera_service.interval,
                            'duration': self._recording_duration
                        }
                    },
                    'motion_sensor': {
                        'debounce': self._motion_service.debounce,
                        'polling_rate': self._motion_service.polling_rate
                    },
                    'button': {
                        'debounce': self._button_service.debounce,
                        'polling_rate': self._button_service.polling_rate
                    }
                }

    async def _begin_or_reset_recording(self):
        if self._recording_task:
            self._recording_task.cancel()
            try:
                await self._recording_task
            except asyncio.CancelledError:
                pass
            self._recording_task = None

        current_state = await self.state

        # Start recording if not already recording or streaming
        if current_state == ControllerState.IDLE:
            await self._camera_service.begin_stop_motion()
            await self._transition_to(ControllerState.RECORDING)

        # Already recording, just reset the timer
        elif current_state == ControllerState.RECORDING:
            pass

        # Cannot record while streaming
        elif current_state == ControllerState.STREAMING:
            return

        # Begin or reset timer
        if current_state == ControllerState.RECORDING:
            self._recording_task = asyncio.create_task(self._recording_timer())

    async def _recording_timer(self):
        try:
            await asyncio.sleep(self._recording_duration)
            await self._stop_recording()
        except asyncio.CancelledError:
            pass

    async def _stop_recording(self):
        async with self._state_lock:
            self._recording_task = None
            if self._state == ControllerState.RECORDING:
                await self._camera_service.end_stop_motion()
                await self._transition_to(ControllerState.IDLE)

    async def start_stream(self):
        async with self._state_lock:
            if self._state == ControllerState.IDLE or self._state == ControllerState.STREAMING:
                stream_url = await self._camera_service.start_stream()
                if stream_url and self._state == ControllerState.IDLE:
                    await self._transition_to(ControllerState.STREAMING)
                return stream_url

            elif self._state == ControllerState.RECORDING:
                if self._recording_task:
                    self._recording_task.cancel()
                    try:
                        await self._recording_task
                    except asyncio.CancelledError:
                        pass
                    self._recording_task = None
                await self._camera_service.end_stop_motion()

                stream_url = await self._camera_service.start_stream()
                if stream_url:
                    await self._transition_to(ControllerState.STREAMING)
                else:
                    await self._transition_to(ControllerState.IDLE)
                return stream_url

    async def stop_stream(self):
        async with self._state_lock:
            if self._state == ControllerState.STREAMING:
                await self._camera_service.stop_stream()
                await self._transition_to(ControllerState.IDLE)
                return True
        return False

    async def start(self):
        self._button_task = asyncio.create_task(
            self._run_sensor(self._button_service, "Button")
        )
        self._motion_task = asyncio.create_task(
            self._run_sensor(self._motion_service, "Motion")
        )

    async def stop(self):
        async with self._state_lock:
            self._stop_event.set()

            if self._recording_task:
                self._recording_task.cancel()
                try:
                    await self._recording_task
                except asyncio.CancelledError:
                    pass
                self._recording_task = None

            if self._state == ControllerState.RECORDING:
                await self._camera_service.end_stop_motion()

            if self._state == ControllerState.STREAMING:
                await self._camera_service.stop_stream()

            if self._button_task:
                self._button_task.cancel()
                try:
                    await self._button_task
                except asyncio.CancelledError:
                    pass

            if self._motion_task:
                self._motion_task.cancel()
                try:
                    await self._motion_task
                except asyncio.CancelledError:
                    pass

        self._button_service.cleanup()
        self._motion_service.cleanup()
        self._rgb_service.cleanup()
        self._camera_service.cleanup()

__all__ = [
    "ButtonService",
    "MotionSensorService",
    "RGBService",
    "CameraService",
    "PeripheralsService"
]
