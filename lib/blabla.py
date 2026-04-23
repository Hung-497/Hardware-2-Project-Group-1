from machine import Pin, I2C
from filefifo import Filefifo
from fifo import Fifo
from ssd1306 import SSD1306_I2C
import time
import micropython
micropython.alloc_emergency_exception_buf(200)

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128,64,i2c)

class task_2:
    def __init__(self):
        self.data = Filefifo(10, name='hr_capture02_250Hz.txt')
        self.min_val = None
        self.max_val = None
        self.scaled_val = 0
        self.SF = 250
        self.samples_to_read = 250

    def run(self):
        prev_block = []
        for _ in range(self.samples_to_read):
            prev_block.append(self.data.get())
        
        for _ in range(50):
            self.min_val = min(prev_block)
            self.max_val = max(prev_block)

            next_block = []
            new_values = []
            cols_in_this_block = 128  

            for _ in range(cols_in_this_block):
                total = 0
                for _ in range(5):
                    v = self.data.get()
                    next_block.append(v)
                    total += v

                avg_val = total / 5
                if self.max_val == self.min_val:
                    self.scaled_val = 31
                else:
                    self.scaled_val = int((avg_val-self.min_val)*63/(self.max_val-self.min_val))
                    if self.scaled_val < 0:
                        self.scaled_val = 0
                    if self.scaled_val > 63:
                        self.scaled_val = 63

                y = 63 - self.scaled_val
                new_values.append(y)

            oled.fill(0)
            prev_y = None
            for x in range(len(new_values)):
                y = int(new_values[x])

                if prev_y is None:
                    oled.pixel(x, y, 1)
                else:
                    oled.line(x - 1, int(prev_y), x, y, 1)
                prev_y = y
                oled.show()

            time.sleep_ms(150)
            prev_block = next_block[-250:]

task_2().run()