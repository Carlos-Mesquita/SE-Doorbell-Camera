import json
import asyncio
import signal
import logging
import RPi.GPIO as GPIO # type: ignore
from asyncio import wait_for, CancelledError, create_task, Queue, run_coroutine_threadsafe, get_running_loop

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


class DoorbellController:
    def __init__(self, auth_token: str, ws_url: str):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._logger = logging.getLogger(__name__)

        with open('./doorbell_controller/settings.json', 'r') as f:
            self.config = json.load(f)

        GPIO.setmode(GPIO.BCM) # type: ignore
        GPIO.setwarnings(False) # type: ignore

        self.event_queue: Queue[Event[SensorEvent]] = Queue()
        self.capture_queue: Queue[Capture] = Queue()
        self._auth_token = auth_token

        self._init_services()

        self._ws_client = WebSocketClient(ws_url, "messages", auth_token)
        self._webrtc_client = WebSocketClient()
        self._setup_ws_handlers()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = False

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
            self.config['camera'], self.event_queue, self.capture_queue, FaceDetector(),
            self._auth_token, self._signaling_server, self._ws_client
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
            MessageType.STREAM_START,
            self._handle_start_stream
        )
        self._ws_client.register_handler(
            MessageType.STREAM_STOP,
            self._handle_stop_stream
        )
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
                    msg = MessageType.BUTTON_PRESSED.value
                elif event.type == SensorEvent.FACE_DETECTED:
                    msg = MessageType.FACE_DETECTED.value
                else:
                    msg = MessageType.MOTION_DETECTED.value

                await self._ws_client.send_message(Message(
                    msg_type=msg,
                ))
            except CancelledError:
                break
            except Exception as e:
                if self.running:
                    self._logger.error(f'Error processing sensor event: {e}')

    async def _process_capture_events(self):
        while self.running:
            try:
                capture = await wait_for(
                    self.capture_queue.get(),
                    timeout=1.0
                )
                await self._ws_client.send_message(Message(
                    msg_type=MessageType.CAPTURE,
                    payload=capture.model_dump()
                ))
            except CancelledError:
                break
            except Exception as e:
                if self.running:
                    self._logger.error(f'Error processing capture event: {e}')

    async def _handle_start_stream(self, message: Message):
        stream_url = self.peripherals.start_stream()
        if stream_url:
            await self._ws_client.send_message(Message(
                msg_type=MessageType.STREAM_ACK,
                payload={'url': stream_url},
                reply_to=message.msg_id
            ))
        else:
            await self._ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                reply_to=message.msg_id
            ))

    async def _handle_stop_stream(self, message: Message):
        success = self.peripherals.stop_stream()
        if success:
            await self._ws_client.send_message(Message(
                msg_type=MessageType.STREAM_ACK,
                reply_to=message.msg_id
            ))
        else:
            await self._ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                reply_to=message.msg_id
            ))

    async def _handle_settings(self, message: Message):
        try:
            result = self.peripherals.handle_settings_event(Event(
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
            await self._ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                payload={'error': str(e)},
                reply_to=message.msg_id
            ))

    def _signal_handler(self, signum, frame):
        self._logger.info(f'Received signal {signum}')
        try:
            loop = get_running_loop()
            loop.create_task(self.stop())
        except RuntimeError:
            run_coroutine_threadsafe(self.stop(), asyncio.new_event_loop())

    async def start(self):
        self._logger.info('Starting doorbell controller...')
        self.running = True

        await self.peripherals.start()
        sensor_task = create_task(self._process_sensor_events())
        capture_task = create_task(self._process_capture_events())
        ws_task = self._ws_client.connect()
        await asyncio.gather(sensor_task, capture_task, ws_task)

    async def stop(self):
        self._logger.info('Stopping doorbell controller...')
        self.running = False

        await self.peripherals.stop()
        await self._ws_client.disconnect()
