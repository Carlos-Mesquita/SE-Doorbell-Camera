import RPi.GPIO as GPIO
import time
import random
import sys

# Ported to py from the C example on http://www.pzsmocn.wiki/index.php/LED_RGB
class RGBController:
    def __init__(self):
        self.PIN_R = 27  # Red on GPIO 27
        self.PIN_G = 17  # Green on GPIO 17
        self.PIN_B = 22  # Blue on GPIO 22
        self.FREQ = 100  # PWM frequency

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.PIN_R, GPIO.OUT)
        GPIO.setup(self.PIN_G, GPIO.OUT)
        GPIO.setup(self.PIN_B, GPIO.OUT)

        self.pwm_r = GPIO.PWM(self.PIN_R, self.FREQ)
        self.pwm_g = GPIO.PWM(self.PIN_G, self.FREQ)
        self.pwm_b = GPIO.PWM(self.PIN_B, self.FREQ)

        self.pwm_r.start(0)
        self.pwm_g.start(0)
        self.pwm_b.start(0)

    def set_color(self, red, green, blue):
        self.pwm_r.ChangeDutyCycle(red)
        self.pwm_g.ChangeDutyCycle(green)
        self.pwm_b.ChangeDutyCycle(blue)

    def random_color(self, duration):
        end_time = time.time() + duration
        while time.time() < end_time:
            red = random.randint(0, 100)
            green = random.randint(0, 100)
            blue = random.randint(0, 100)

            self.set_color(red, green, blue)
            time.sleep(0.1)

    def display_color(self, r, g, b, duration):
        self.set_color(r, g, b)
        time.sleep(duration)

    def cleanup(self):
        self.pwm_r.stop()
        self.pwm_g.stop()
        self.pwm_b.stop()
        GPIO.cleanup([self.PIN_R, self.PIN_G, self.PIN_B])


if __name__ == "__main__":
    rgb = RGBController()

    option = sys.argv[1].lower() if len(sys.argv) > 1 else "red"

    try:
        secs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    except ValueError:
        secs = 5

    options = {
        "rng": lambda: rgb.random_color(secs),
        "red": lambda: rgb.display_color(100, 0, 0, secs),
        "green": lambda: rgb.display_color(0, 100, 0, secs),
        "blue": lambda: rgb.display_color(0, 0, 100, secs),
    }

    try:
        color = "random colors" if option == "rng" else option
        print(f"Displaying {color} for {secs} seconds ...")
        options[option]()

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        rgb.cleanup()
