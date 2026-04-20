from machine import Pin
from fifo import Fifo
import micropython
import time

micropython.alloc_emergency_exception_buf(200)   # For hard interrupts


class Encoder:
    def __init__(self, rot_a, rot_b):
        self.a = Pin(rot_a, Pin.IN)               # Channel A
        self.b = Pin(rot_b, Pin.IN)               # Channel B
        self.fifo = Fifo(30, typecode='i')        # FIFO for +1 / -1 steps
        # Interrupt on A, falling edge, hard IRQ
        self.a.irq(
            handler=self.handler,
            trigger=Pin.IRQ_FALLING,
            hard=True
        )
        self.press = False

    def handler(self, pin):
        # Runs on each falling edge of A
        if self.b():                 # If B == 1
            self.fifo.put(1)         # One direction
        else:                        # If B == 0
            self.fifo.put(-1)   # Other direction

    def btn_handler(self, pin):
        last_time = 0
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_time) >= 250:
            self.press = True
            last_time = current_time
