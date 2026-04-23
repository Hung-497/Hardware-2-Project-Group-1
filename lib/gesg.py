from machine import Pin
led = Pin(26,Pin.OUT)
while True:
    led.on()