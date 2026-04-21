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

        while True:
            # Edge-detect the start of the measurement
            if menu.measuring and not was_measuring:
                processor.start_collection()
            was_measuring = menu.measuring
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

                    # trigger wifi after 30 sec
                    if processor.collection_complete:
                        print(
                            f"sent")
                        processor.collection_complete = False

                        try:
                            from mqtt import KubiosExample
                            mqtt_client = KubiosExample(processor.bpm_list)
                            mqtt_client.run()
                        except Exception as e:
                            print("kubios failed:", e)

                # update measuring screen
                menu.update_display(processor.bpm)


Main.main()
