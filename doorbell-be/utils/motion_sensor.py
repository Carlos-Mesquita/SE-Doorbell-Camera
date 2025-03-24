import RPi.GPIO as GPIO
import time
from datetime import datetime

PIR_PIN = 23
WARMUP_TIME = 10
POLLING_DELAY = 0.1
BETWEEN_DETECTION_DELAY = 2


def monitor_motion():
    while True:
        if GPIO.input(PIR_PIN):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now} - Motion detected!")
            time.sleep(BETWEEN_DETECTION_DELAY)
        time.sleep(POLLING_DELAY)

if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIR_PIN, GPIO.IN)
        print("Testing Motion Sensor (CTRL+C to exit)")
        print(f"Booting up ... ({WARMUP_TIME} secs)")
        time.sleep(WARMUP_TIME)
        print("Done")
        monitor_motion()

    except KeyboardInterrupt:
        print("Cleaning up ...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        GPIO.cleanup([PIR_PIN])
