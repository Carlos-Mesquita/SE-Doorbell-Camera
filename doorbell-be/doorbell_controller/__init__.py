import base64
import json
import asyncio
import signal
import logging
import RPi.GPIO as GPIO  # type: ignore
from asyncio import wait_for, CancelledError, create_task, Queue, get_running_loop
from pathlib import Path

from doorbell_controller.models import Event, SensorEvent, Capture
from doorbell_shared.models import Message, MessageType
from doorbell_controller.services.impl import (
    ButtonService,
    MotionSensorService,
    RGBService,
    CameraService,
    PeripheralsService,
    WebSocketClient,
    FaceDetector
)

SCRIPT_DIR = Path(__file__).parent

class DoorbellController:
    def __init__(self, auth_token: str, ws_url: str, signaling_server_url: str):
        self._logger = logging.getLogger(__name__)

        settings_path = SCRIPT_DIR / 'settings.json'
        try:
            with open(settings_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self._logger.error(f"CRITICAL: settings.json not found at {settings_path}")
            raise
        except json.JSONDecodeError:
            self._logger.error(f"CRITICAL: Could not decode settings.json at {settings_path}")
            raise

        GPIO.setmode(GPIO.BCM)  # type: ignore
        GPIO.setwarnings(False)  # type: ignore

        self.event_queue: Queue[Event[SensorEvent]] = Queue()
        self.capture_queue: Queue[Capture] = Queue()
        self._auth_token = auth_token
        self._signaling_server_url = signaling_server_url

        self._init_services()

        self._ws_client = WebSocketClient(ws_url, "messages", auth_token)
        self._setup_ws_handlers()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = False
        self._shutdown_event = asyncio.Event()

    def _init_services(self):
        self.button_service = ButtonService(
            self.event_queue,
            self.config['button']
        )

        self.motion_service = MotionSensorService(
            self.event_queue,
            self.config['motion_sensor']
        )

        self.rgb_service = RGBService(self.config['rgb'])

        self.camera_service = CameraService(
            self.config['camera'], self.event_queue, self.capture_queue,
            FaceDetector(SCRIPT_DIR / 'haarcascade_frontalface_default.xml'),
            self._auth_token, self._signaling_server_url
        )

        self.peripherals = PeripheralsService(
            self.button_service,
            self.motion_service,
            self.rgb_service,
            self.camera_service,
            self.config['camera']['stop_motion']['duration']
        )

    def _setup_ws_handlers(self):
        self._ws_client.register_handler(
            MessageType.SETTINGS_REQUEST,
            self._handle_settings
        )

    async def _process_sensor_events(self):
        while self.running:
            try:
                try:
                    event = await wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                await self.peripherals.handle_sensor_event(event)

                if event.type == SensorEvent.BUTTON_PRESSED:
                    msg_type_val = MessageType.BUTTON_PRESSED.value
                elif event.type == SensorEvent.FACE_DETECTED:
                    msg_type_val = MessageType.FACE_DETECTED.value
                else:
                    msg_type_val = MessageType.MOTION_DETECTED.value

                await self._ws_client.send_message(Message(
                    msg_type=MessageType(msg_type_val),
                    msg_id=event.id
                ))
            except CancelledError:
                self._logger.info("Sensor event processing task cancelled.")
                break
            except Exception as e:
                if self.running:
                    self._logger.error(f'Error processing sensor event: {e}', exc_info=True)

    async def _process_capture_events(self):
        while self.running:
            try:
                capture_event = await wait_for(
                    self.capture_queue.get(),
                    timeout=1.0
                )

                if not capture_event.image_data:
                    self._logger.warning(f"Capture event for {capture_event.associated_to} has no image data. Skipping.")
                    continue

                encoded_image_data = base64.b64encode(capture_event.image_data).decode('utf-8')

                payload = {
                    "associated_to": capture_event.associated_to,
                    "timestamp": capture_event.timestamp.isoformat(),
                    "image_format": capture_event.image_format,
                    "image_data_b64": encoded_image_data,
                    "has_face": capture_event.has_face
                }

                await self._ws_client.send_message(Message(
                    msg_type=MessageType.CAPTURE,
                    msg_id=capture_event.id,
                    payload=payload
                ))
                self._logger.info(f"Sent capture event with {len(capture_event.image_data)} bytes (encoded) for {capture_event.associated_to}")

            except asyncio.TimeoutError:
                continue
            except CancelledError:
                self._logger.info("Capture event processing task cancelled.")
                break
            except Exception as e:
                if self.running:
                    self._logger.error(f'Error processing capture event: {e}', exc_info=True)

    async def _handle_settings(self, message: Message):
        try:
            if not message.payload or 'type' not in message.payload:
                raise ValueError("Missing 'type' in settings request payload")

            result = await self.peripherals.handle_settings_event(Event(
                type=message.payload['type'],
                payload=message.payload.get('data', {})
            ))

            if result is None:
                result = {}

            await self._ws_client.send_message(Message(
                msg_type=MessageType.SETTINGS_ACK,
                payload={**result},
                reply_to=message.msg_id
            ))

        except Exception as e:
            self._logger.error(f"Error handling settings: {e}", exc_info=True)
            await self._ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                payload={'error': str(e)},
                reply_to=message.msg_id
            ))

    def _signal_handler(self, signum, frame):
        self._logger.info(f'Received signal {signum}, initiating shutdown...')
        self._shutdown_event.set()
        if self.running:
            try:
                loop = get_running_loop()
                loop.create_task(self.stop())
            except RuntimeError:
                self._logger.warning("Asyncio loop not running, attempting synchronous cleanup if possible.")
                pass

    async def start(self):
        if self.running:
            self._logger.warning("Controller already started.")
            return

        self._logger.info('Starting doorbell controller...')
        self.running = True
        self._shutdown_event.clear()

        await self.peripherals.start()
        sensor_task = create_task(self._process_sensor_events(), name="SensorEventProcessor")
        capture_task = create_task(self._process_capture_events(), name="CaptureEventProcessor")
        ws_task = create_task(self._ws_client.connect(),
                              name="WebSocketClientConnect")

        try:
            await asyncio.gather(sensor_task, capture_task, ws_task)
        except Exception as e:
            self._logger.error(f"A critical task failed in controller start: {e}", exc_info=True)
            await self.stop()
        finally:
            self._logger.info("Doorbell controller main tasks finished or cancelled.")
            self.running = False

    async def stop(self):
        if not self.running and not self._shutdown_event.is_set():
            self._logger.info('Controller stop called, but already stopped or not running.')

        self._logger.info('Stopping doorbell controller...')
        self.running = False
        self._shutdown_event.set()


        if hasattr(self, 'peripherals'):
            await self.peripherals.stop()

        if hasattr(self, '_ws_client') and self._ws_client.connected:
            await self._ws_client.disconnect()

        await asyncio.sleep(0.1)

        self._logger.info("Doorbell controller stopped.")