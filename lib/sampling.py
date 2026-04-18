from machine import ADC
from piotimer import Piotimer
from fifo import Fifo
from config import Value

class Sampling(Fifo):
    def __init__(self):
        super().__init__(Value().pico_size)
        # initialize heart rate sensor
        self.adc = ADC(Value().ADC_PIN)
        # sampling
        self.timer = Piotimer(mode=Piotimer.PERIODIC, freq=Value().sample_rate, callback=self.handler)
        
    def handler(self, tid):
        self.put(self.adc.read_u16())
