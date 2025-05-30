import asyncio
from asyncio import Lock, Task, sleep, create_task, CancelledError

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
    ISensor, ISensorService, IRGBService, ICameraService
)


class PeripheralsService:
    def __init__(
            self,
            button_service: ISensorService,
            motion_service: ISensorService,
            rgb_service: IRGBService,
            camera_service: ICameraService,
            stop_motion_duration: int
    ):
        self._button_service = button_service
        self._motion_service = motion_service
        self._rgb_service = rgb_service
        self._camera_service = camera_service

        self._stop_event = asyncio.Event()
        self._state_lock = Lock()

        self._state = ControllerState.IDLE

        self._recording_task: Optional[Task] = None
        self._recording_duration_seconds = stop_motion_duration

        self._button_polling_task: Optional[Task] = None
        self._motion_polling_task: Optional[Task] = None

        self._was_streaming = False
        self._streaming_cooldown_task: Optional[Task] = None
        self._streaming_cooldown_seconds = 5.0

        self._logger = getLogger(__name__)

    async def on_streaming_started(self):
        self._logger.info("Streaming started - checking if recording needs to be stopped")
        async with self._state_lock:
            if self._state == ControllerState.RECORDING:
                self._logger.info("Stopping recording due to streaming start")
                await self._stop_recording_unsafe()
                await self._transition_to(ControllerState.STREAMING)
            elif self._state == ControllerState.IDLE:
                self._logger.info("Transitioning from IDLE to STREAMING")
                await self._transition_to(ControllerState.STREAMING)
        self._was_streaming = True

    async def on_streaming_stopped(self):
        self._logger.info("Streaming stopped - starting cooldown period")
        async with self._state_lock:
            if self._state == ControllerState.STREAMING:
                await self._transition_to(ControllerState.IDLE)

        if self._streaming_cooldown_task:
            self._streaming_cooldown_task.cancel()
        self._streaming_cooldown_task = create_task(self._streaming_cooldown(), name="StreamingCooldown")

    async def _streaming_cooldown(self):
        try:
            self._logger.info(f"Starting {self._streaming_cooldown_seconds}s cooldown after streaming")
            await asyncio.sleep(self._streaming_cooldown_seconds)
            self._was_streaming = False
            self._logger.info("Streaming cooldown completed - motion detection re-enabled")
        except CancelledError:
            self._logger.info("Streaming cooldown cancelled")

    async def should_suppress_motion_events(self) -> bool:
        return self._was_streaming or (self._streaming_cooldown_task and not self._streaming_cooldown_task.done())

    @property
    async def state(self) -> ControllerState:
        async with self._state_lock:
            return self._state

    async def _transition_to(self, new_state: ControllerState):
        old_state = self._state
        if old_state == new_state:
            return

        self._state = new_state
        self._logger.info(f"State transition: {old_state.value} -> {new_state.value}")

        try:
            if self._state in [ControllerState.STREAMING, ControllerState.RECORDING]:
                self._rgb_service.turn_on()
                self._logger.debug("RGB lights turned ON")
            else:
                self._rgb_service.turn_off()
                self._logger.debug("RGB lights turned OFF")
        except Exception as e:
            self._logger.error(f"Error controlling RGB during state transition: {e}", exc_info=True)

    async def handle_sensor_event(self, event: Event[SensorEvent]):
        self._logger.debug(f"Handling sensor event: {event.type.value}")

        if event.type == SensorEvent.MOTION_DETECTED:
            if await self.should_suppress_motion_events():
                self._logger.debug(f"Suppressing motion event {event.id} - streaming active or cooldown")
                return

        async with self._state_lock:
            current_state = self._state

            if event.type in [SensorEvent.BUTTON_PRESSED, SensorEvent.MOTION_DETECTED, SensorEvent.FACE_DETECTED]:
                if current_state == ControllerState.IDLE:
                    self._logger.info(
                        f"Sensor event ({event.type.value}, id: {event.id}) occurred in IDLE state. Starting recording.")
                    await self._begin_or_reset_recording_unsafe(event_id=event.id)
                elif current_state == ControllerState.RECORDING:
                    self._logger.info(
                        f"Sensor event ({event.type.value}, id: {event.id}) occurred during RECORDING. Resetting recording timer.")
                    await self._begin_or_reset_recording_unsafe(event_id=event.id)
                elif current_state == ControllerState.STREAMING:
                    self._logger.info(
                        f"Sensor event ({event.type.value}, id: {event.id}) occurred during STREAMING. No change to recording state.")

    async def handle_settings_event(self, event: Event[SettingsEvent]) -> Optional[Dict[str, Any]]:
        self._logger.info(f"Handling settings event: {event.type}")

        if event.type == SettingsEvent.CHANGE_SETTINGS:
            payload = event.payload
            if 'button' in payload:
                button_cfg = payload['button']
                if 'debounce_ms' in button_cfg:
                    debounce_s = float(button_cfg['debounce_ms']) / 1000.0
                    self._button_service.debounce = debounce_s
                if 'polling_rate_hz' in button_cfg:
                    polling_hz = float(button_cfg['polling_rate_hz'])
                    if polling_hz > 0:
                        self._button_service.polling_interval = 1.0 / polling_hz
                    else:
                        self._logger.warning("Invalid polling_rate_hz for button: must be > 0")

            if 'motion_sensor' in payload:
                motion_cfg = payload['motion_sensor']
                if 'debounce_ms' in motion_cfg:
                    debounce_s = float(motion_cfg['debounce_ms']) / 1000.0
                    self._motion_service.debounce = debounce_s
                if 'polling_rate_hz' in motion_cfg:
                    polling_hz = float(motion_cfg['polling_rate_hz'])
                    if polling_hz > 0:
                        self._motion_service.polling_interval = 1.0 / polling_hz
                    else:
                        self._logger.warning("Invalid polling_rate_hz for motion sensor: must be > 0")

            if 'camera' in payload and 'stop_motion' in payload['camera']:
                if 'interval' in payload['camera']['stop_motion']:
                    if hasattr(self._camera_service, 'set_stop_motion_interval'):
                        await self._camera_service.set_stop_motion_interval(
                            payload['camera']['stop_motion']['interval'])
                    else:
                        self._logger.warning("CameraService does not support dynamic interval setting via this path.")

                if 'duration' in payload['camera']['stop_motion']:
                    async with self._state_lock:
                        self._recording_duration_seconds = payload['camera']['stop_motion']['duration']
                    self._logger.info(f"Recording duration updated to {self._recording_duration_seconds}s.")

                if 'color' in payload and all(key in payload['color'] for key in ['r', 'g', 'b']):
                    self._rgb_service.change_color(
                        payload['color']['r'],
                        payload['color']['g'],
                        payload['color']['b']
                    )
                    async with self._state_lock:
                        if self._state in [ControllerState.RECORDING, ControllerState.STREAMING]:
                            self._rgb_service.turn_on()

                return {"status": "Settings change applied"}

        elif event.type == SettingsEvent.GET_SETTINGS:
            async with self._state_lock:
                rec_duration = self._recording_duration_seconds

            cam_interval = await self._camera_service.get_stop_motion_interval() if hasattr(
                self._camera_service, 'get_stop_motion_interval'
            ) else None

            button_settings = {}
            if hasattr(self._button_service, 'get_config_settings'):
                button_settings = await self._button_service.get_config_settings()

            motion_settings = {}
            if hasattr(self._motion_service, 'get_config_settings'):
                motion_settings = await self._motion_service.get_config_settings()

            return {
                'color': self._rgb_service.get_color(),
                'camera': {
                    'stop_motion': {
                        'interval_seconds': cam_interval,
                        'duration_seconds': rec_duration
                    }
                },
                'motion_sensor': motion_settings,
                'button': button_settings
            }
        return None

    async def _begin_or_reset_recording_unsafe(self, event_id: Optional[str] = None):
        if self._recording_task:
            self._recording_task.cancel()
            self._recording_task = None

        current_state_unsafe = self._state

        if current_state_unsafe == ControllerState.IDLE:
            self._logger.info("Starting stop motion recording (unsafe)...")
            if await self._camera_service.begin_stop_motion(event_id=event_id):
                await self._transition_to(ControllerState.RECORDING)
            else:
                self._logger.debug("Failed to begin stop motion recording - likely due to active streaming.")
                return

        elif current_state_unsafe == ControllerState.RECORDING:
            self._logger.info("Resetting stop motion recording timer (unsafe)...")
            pass

        elif current_state_unsafe == ControllerState.STREAMING:
            self._logger.info("Cannot start/reset recording while streaming (unsafe).")
            return

        if self._state == ControllerState.RECORDING:
            self._recording_task = create_task(self._recording_timer(), name="RecordingTimer")

    async def _recording_timer(self):
        try:
            await asyncio.sleep(self._recording_duration_seconds)
            self._logger.info("Recording timer expired. Stopping recording.")
            async with self._state_lock:
                if self._state == ControllerState.RECORDING:
                    await self._stop_recording_unsafe()
                else:
                    self._logger.info("Recording timer expired but no longer in RECORDING state - timer was superseded")
        except CancelledError:
            self._logger.info("Recording timer cancelled.")

    async def _stop_recording_unsafe(self):
        if self._recording_task:
            self._recording_task.cancel()
            self._recording_task = None

        if self._state == ControllerState.RECORDING:
            self._logger.info("Stopping stop motion capture (unsafe)...")
            await self._camera_service.end_stop_motion()
            await self._transition_to(ControllerState.IDLE)
        else:
            self._logger.debug(
                f"Stop recording called but not in RECORDING state (current: {self._state}). No action taken.")

    async def start(self):
        self._logger.info("Starting peripheral services...")
        self._stop_event.clear()

        await self._button_service.start()
        await self._motion_service.start()
        await self._camera_service.start()

        self._logger.info("All peripheral services started successfully.")

        async with self._state_lock:
            await self._transition_to(ControllerState.IDLE)

        self._logger.info("Peripheral services started and state set to IDLE.")

    async def stop(self):
        self._logger.info("Stopping peripheral services...")
        self._stop_event.set()

        async with self._state_lock:
            if self._recording_task:
                self._recording_task.cancel()
                try:
                    await self._recording_task
                except CancelledError:
                    pass
                self._recording_task = None

            if self._streaming_cooldown_task:
                self._streaming_cooldown_task.cancel()
                try:
                    await self._streaming_cooldown_task
                except CancelledError:
                    pass
                self._streaming_cooldown_task = None

            if self._state == ControllerState.RECORDING:
                await self._camera_service.end_stop_motion()

            await self._transition_to(ControllerState.IDLE)

        for task_name, task_ref in [("ButtonPolling", self._button_polling_task),
                                    ("MotionPolling", self._motion_polling_task)]:
            if task_ref and not task_ref.done():
                task_ref.cancel()
                try:
                    await task_ref
                except CancelledError:
                    self._logger.info(f"{task_name} task cancelled successfully.")
                except Exception as e:
                    self._logger.error(f"Error stopping {task_name} task: {e}", exc_info=True)
        self._button_polling_task = None
        self._motion_polling_task = None

        if hasattr(self._camera_service, 'cleanup'):
            await self._camera_service.cleanup()
        if hasattr(self._button_service, 'cleanup'):
            await self._button_service.cleanup()
        if hasattr(self._motion_service, 'cleanup'):
            await self._motion_service.cleanup()
        if hasattr(self._rgb_service, 'cleanup'):
            await self._rgb_service.cleanup()

        self._logger.info("Peripheral services stopped and cleaned up.")


__all__ = [
    "ButtonService",
    "MotionSensorService",
    "RGBService",
    "CameraService",
    "PeripheralsService"
]
