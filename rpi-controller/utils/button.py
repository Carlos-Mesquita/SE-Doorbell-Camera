import RPi.GPIO as GPIO
import time

BUTTON_PIN = 26
DEBOUNCE_TIME = 1
POLLING_RATE = 0.1

def monitor_button():
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Button pressed!")
            time.sleep(DEBOUNCE_TIME)
        time.sleep(POLLING_RATE)

if __name__ == "__main__":
    print("Testing Push Button (CTRL+C to exit)")

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        monitor_button()

    except KeyboardInterrupt:
        print("Cleaning up ...")

    finally:
        GPIO.cleanup([BUTTON_PIN])
