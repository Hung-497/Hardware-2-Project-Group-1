from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
from led import Led
from config import Value


class Hardware:
    def __init__(self):
        self.i2c = I2C(Value().I2C_ID, scl=Pin(Value().I2C_SCL_PIN),
                       sda=Pin(Value().I2C_SDA_PIN), freq=400000)
        self.oled = SSD1306_I2C(Value().OLED_WIDTH, Value().OLED_HIGHT, self.i2c)
        self.led = Led(Value().LED_PIN)
        self.button = Pin(Value().BUTTON_PIN, Pin.IN, Pin.PULL_UP)


hw = Hardware()
