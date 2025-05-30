import RPi.GPIO as GPIO  # type: ignore
from typing import Dict, Any
import logging

from doorbell_controller.exceptions import ConfigException
from doorbell_controller.services import IPeripheral, IRGB

logger = logging.getLogger(__name__)


class RGBService(IPeripheral, IRGB):

    def __init__(self, config: Dict[str, Any]):
        try:
            pins_config = config['pins']
            self._PIN_R = int(pins_config['R'])
            self._PIN_G = int(pins_config['G'])
            self._PIN_B = int(pins_config['B'])

            self._FREQ = int(config.get('freq', 100))

            color_config = config['color']


            self._r_duty = int(color_config.get('R', color_config.get('r', 0)))
            self._g_duty = int(color_config.get('G', color_config.get('g', 0)))
            self._b_duty = int(color_config.get('B', color_config.get('b', 0)))
            self._validate_duty_cycles()

        except (KeyError, ValueError) as e:
            logger.error(f"Configuration error for RGBService: {e}", exc_info=True)
            raise ConfigException(f"rgb config: {e}")

        GPIO.setup(self._PIN_R, GPIO.OUT)
        GPIO.setup(self._PIN_G, GPIO.OUT)
        GPIO.setup(self._PIN_B, GPIO.OUT)

        self._pwm_r = GPIO.PWM(self._PIN_R, self._FREQ)
        self._pwm_g = GPIO.PWM(self._PIN_G, self._FREQ)
        self._pwm_b = GPIO.PWM(self._PIN_B, self._FREQ)

        self._pwm_r.start(0)
        self._pwm_g.start(0)
        self._pwm_b.start(0)
        self._is_on = False
        logger.info(
            f"RGBService initialized on R:{self._PIN_R}, G:{self._PIN_G}, B:{self._PIN_B}. Initial color (duty): R={self._r_duty} G={self._g_duty} B={self._b_duty}")

    def _validate_duty_cycles(self):
        self._r_duty = max(0, min(100, self._r_duty))
        self._g_duty = max(0, min(100, self._g_duty))
        self._b_duty = max(0, min(100, self._b_duty))

    def _set_hardware_color(self, r_duty: int, g_duty: int, b_duty: int):

        self._pwm_r.ChangeDutyCycle(r_duty)
        self._pwm_g.ChangeDutyCycle(g_duty)
        self._pwm_b.ChangeDutyCycle(b_duty)

    def change_color(self, r: int, g: int, b: int):
        """Changes the configured color (0-100 for duty cycle). Applies immediately if LED is on."""
        self._r_duty = r
        self._g_duty = g
        self._b_duty = b
        self._validate_duty_cycles()
        logger.info(f"RGB color changed to (duty %): R={self._r_duty}, G={self._g_duty}, B={self._b_duty}")
        if self._is_on:
            self.turn_on()

    def get_color(self) -> Dict[str, int]:
        return {
            'r': self._r_duty,
            'g': self._g_duty,
            'b': self._b_duty
        }

    def turn_on(self):
        """Turns the LED on with the currently configured color."""
        if not self._is_on:
            logger.debug(f"Turning RGB LED on with color R={self._r_duty}, G={self._g_duty}, B={self._b_duty}")
        self._set_hardware_color(self._r_duty, self._g_duty, self._b_duty)
        self._is_on = True

    def turn_off(self):
        """Turns the LED off (sets color to black)."""
        if self._is_on:
            logger.debug("Turning RGB LED off.")
        self._set_hardware_color(0, 0, 0)
        self._is_on = False

    async def cleanup(self):
        logger.info("Cleaning up GPIO for RGB LED.")
        self.turn_off()
        self._pwm_r.stop()
        self._pwm_g.stop()
        self._pwm_b.stop()
        try:
            GPIO.cleanup([self._PIN_R, self._PIN_G, self._PIN_B])
        except Exception as e:
            logger.warning(f"Exception during GPIO cleanup for RGB pins: {e}")
