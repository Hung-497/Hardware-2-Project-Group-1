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
        was_measuring = False

        sent = False

        while True:
            # Edge-detect the start of the measurement
            if menu.measuring and not was_measuring:
                processor.start_collection()
            was_measuring = menu.measuring

            if not menu.measuring:
                # clear
                while not sampler.empty():
                    sampler.get()
            else:
                while not sampler.empty():
                    val = sampler.get()
                    is_beat = processor.process_sample(val)

                    # if heart beats, toggle led
                    if is_beat:
                        hw.led.toggle()

            # Handle the network dispatch directly matched to the menu screen state
            if getattr(menu, 'screen', '') == "hrv_send":
                if not sent:
                    try:
                        from mqtt import KubiosExample
                        mqtt_client = KubiosExample(
                            processor.bpm_list, processor.bpm)
                        mqtt_client.run()
                    except Exception as error:
                        print("kubios failed:", error)
                    sent = True
            else:
                sent = False

            # update measuring screen
            menu.update_display(processor.bpm)


Main.main()
