import json
import asyncio
import signal
import logging
import os

import RPi.GPIO as GPIO

from dotenv import load_dotenv

from doorbell_controller.exceptions import InvalidEventPayload
from doorbell_controller.models import Event, SensorEvent
from doorbell_core.models import Message, MessageType
from doorbell_controller.services.impl import (
    ButtonService,
    MotionSensorService,
    RGBService,
    CameraService,
    PeripheralsService,
    WebSocketClient
)


class DoorbellController:
    def __init__(self, config_path: str, server_url: str, auth_token: str):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self._logger = logging.getLogger(__name__)

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        GPIO.setmode(GPIO.BCM) # type: ignore
        GPIO.setwarnings(False) # type: ignore

        self.event_queue: asyncio.Queue[Event[SensorEvent]] = asyncio.Queue()

        self._init_services()

        self.ws_client = WebSocketClient(server_url, auth_token)
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

        self.camera_service = CameraService(self.config['camera'])

        self.peripherals = PeripheralsService(
            self.button_service,
            self.motion_service,
            self.rgb_service,
            self.camera_service,
            self.config['camera']['stop_motion']['duration']
        )

    def _setup_ws_handlers(self):
        self.ws_client.register_handler(
            MessageType.STREAM_START,
            self._handle_start_stream
        )
        self.ws_client.register_handler(
            MessageType.STREAM_STOP,
            self._handle_stop_stream
        )
        self.ws_client.register_handler(
            MessageType.SETTINGS_REQUEST,
            self._handle_settings
        )

    async def _process_sensor_events(self):
        while self.running:
            try:
                try:
                    event = await asyncio.wait_for(
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

                await self.ws_client.send_message(Message(
                    msg_type=msg,
                ))

            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    self._logger.error(f'Error processing sensor event: {e}')

    async def _handle_start_stream(self, message: Message):
        stream_url = self.peripherals.start_stream()
        if stream_url:
            await self.ws_client.send_message(Message(
                msg_type=MessageType.STREAM_ACK,
                payload={'url': stream_url},
                reply_to=message.msg_id
            ))
        else:
            await self.ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                reply_to=message.msg_id
            ))

    async def _handle_stop_stream(self, message: Message):
        success = self.peripherals.stop_stream()
        if success:
            await self.ws_client.send_message(Message(
                msg_type=MessageType.STREAM_ACK,
                reply_to=message.msg_id
            ))
        else:
            await self.ws_client.send_message(Message(
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

            await self.ws_client.send_message(Message(
                msg_type=MessageType.SETTINGS_ACK,
                payload={**result},
                reply_to=message.msg_id
            ))

        except InvalidEventPayload as e:
            await self.ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                payload={'error': f'Expected field(s): {",".join(e.fields)}'},
                reply_to=message.msg_id
            ))

        except Exception as e:
            await self.ws_client.send_message(Message(
                msg_type=MessageType.ERROR,
                payload={'error': str(e)},
                reply_to=message.msg_id
            ))

    def _signal_handler(self, signum, frame):
        self._logger.info(f'Received signal {signum}')
        self.stop()

    async def start(self):
        self._logger.info('Starting doorbell controller...')
        self.running = True

        await self.ws_client.connect()
        await self.peripherals.start()
        await self._process_sensor_events()

    def stop(self):
        self._logger.info('Stopping doorbell controller...')
        self.running = False

        self.peripherals.stop()
        asyncio.create_task(self.ws_client.disconnect())


async def main():
    load_dotenv()

    controller = DoorbellController(
        'settings.json',
        os.getenv('WS_URL'),
        os.getenv('API_KEY')
    )

    try:
        await controller.start()
    except KeyboardInterrupt:
        controller.stop()
    except Exception as e:
        logging.error(f"Error in main loop: {e}")
        controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
