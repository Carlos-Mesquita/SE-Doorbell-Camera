import RPi.GPIO as GPIO # type: ignore
from typing import Dict

from doorbell_controller.exceptions import ConfigException
from doorbell_controller.services import IPeripheral, IRGB


class RGBService(IPeripheral, IRGB):

    def __init__(self, config: Dict[str, any]):
        try:
            self._PIN_R = int(config['pins']['R'])
            self._PIN_G = int(config['pins']['G'])
            self._PIN_B = int(config['pins']['B'])
            self._FREQ = int(config['freq'])

            self._r = int(config['color']['R'])
            self._g = int(config['color']['G'])
            self._b = int(config['color']['B'])
        except Exception:
            raise ConfigException("rgb")

        GPIO.setup(self._PIN_R, GPIO.OUT) # type: ignore
        GPIO.setup(self._PIN_G, GPIO.OUT) # type: ignore
        GPIO.setup(self._PIN_B, GPIO.OUT) # type: ignore

        self._pwm_r = GPIO.PWM(self._PIN_R, self._FREQ) # type: ignore
        self._pwm_g = GPIO.PWM(self._PIN_G, self._FREQ) # type: ignore
        self._pwm_b = GPIO.PWM(self._PIN_B, self._FREQ) # type: ignore

        self._pwm_r.start(0)
        self._pwm_g.start(0)
        self._pwm_b.start(0)

    def _set_color(self, red, green, blue):
        self._pwm_r.ChangeDutyCycle(red)
        self._pwm_g.ChangeDutyCycle(green)
        self._pwm_b.ChangeDutyCycle(blue)

    def change_color(self, r: int, g: int, b: int):
        self._r = r
        self._g = g
        self._b = b

    def get_color(self):
         return {
             'r': self._r,
             'g': self._g,
             'b': self._b
         }

    def turn_on(self):
        self._set_color(self._r, self._g, self._b)

    def turn_off(self):
        self._set_color(0, 0, 0)

    async def cleanup(self):
        self._pwm_r.stop()
        self._pwm_g.stop()
        self._pwm_b.stop()
        GPIO.cleanup([self._PIN_R, self._PIN_G, self._PIN_B]) # type: ignore
