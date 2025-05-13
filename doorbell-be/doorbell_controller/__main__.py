import logging
import os
from asyncio import run

from dotenv import load_dotenv
from . import DoorbellController

async def main():
    load_dotenv()

    controller = DoorbellController(os.getenv("CAMERA_TOKEN"), os.getenv("WS_URL"))
    try:
        await controller.start()
    except KeyboardInterrupt:
        await controller.stop()
    except Exception as e:
        logging.error(f"Error in main loop: {e}")
        await controller.stop()


if __name__ == "__main__":
    run(main())
