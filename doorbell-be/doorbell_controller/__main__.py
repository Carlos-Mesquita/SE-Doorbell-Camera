import logging
import os
from asyncio import run

from dotenv import load_dotenv
from . import DoorbellController

async def main():
    load_dotenv()

    controller = DoorbellController(
        os.getenv("CAMERA_TOKEN"),
        os.getenv("WS_URL"),
        os.getenv("SIGNALING_SERVER_URL")
    )
    try:
        await controller.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt received, stopping...")
        await controller.stop()
    except Exception as e:
        logging.error(f"Error in main loop: {e}", exc_info=True) # Added exc_info for more details
        await controller.stop()
    finally:
        logging.info("Application shut down.")


if __name__ == "__main__":
    logging.basicConfig(
            level=logging.INFO, # Moved basicConfig here for earlier setup
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run(main())