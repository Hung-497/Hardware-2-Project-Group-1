from sampling import Sampling
from processing import Processing
from menu import Menu
from hardware import hw
import micropython

micropython.alloc_emergency_exception_buf(200)


class Main:
    def main():
        sampler = Sampling()
        processor = Processing()
        menu = Menu()

        while True:
            if not menu.measuring:
                # clear
                while not sampler.empty():
                    sampler.get()

                # Show the idle screen
                menu.update_display(0)
            else:
                while not sampler.empty():
                    val = sampler.get()
                    is_beat = processor.process_sample(val)

                    # if heart beats, toggle led
                    if is_beat:
                        hw.led.toggle()

                # update measuring screen
                menu.update_display(processor.bpm)


Main.main()
