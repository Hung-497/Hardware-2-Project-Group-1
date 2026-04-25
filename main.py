from sampling import Sampling
from processing import Processing
from menu import Menu
from hardware import hw
from display import Display
import micropython


micropython.alloc_emergency_exception_buf(200)


class Main:
    def main():
        sampler = Sampling()
        processor = Processing()
        menu = Menu(processor)
        disp = Display(processor)
        was_measuring = False

        sent = False

        while True:
            # Edge-detect the start of the measurement
            if menu.measuring and not was_measuring:
                sent = False
                processor.start_collection()
                disp.reset()
            was_measuring = menu.measuring

            if not menu.measuring:
                # clear
                while not sampler.empty():
                    sampler.get()
            else:
                while not sampler.empty():
                    val = sampler.get()
                    is_beat = processor.process_sample(val)
                    
                     # update graph only in basic HR screen
                    if menu.screen == "basic_hr":
                        disp.add_sample(processor.prev_val)

                    # update graph only in basic HR screen
                    if menu.screen == "basic_hr":
                        disp.add_sample(processor.prev_val)

                    # if heart beats, toggle led
                    if is_beat:
                        hw.led.toggle()

            # after collecting send to kubios
            if menu.screen == "hrv_send" and not sent:
                processor.calculate_hrv_metrics()
                if menu.menu_option == 4:
                    print("send to Kubios")
                    try:
                        from mqtt import KubiosExample
                        mqtt_client = KubiosExample(
                            bpm_data=processor.bpm_list, ppi=processor, current_bpm=processor.bpm, patient_name=menu.user_manager.get_current_name())
                        mqtt_client.run()
                    except Exception as error:
                        print("kubios failed:", error)
                sent = True

            # update measuring screen
            menu.update_display(processor.bpm, disp)


Main.main()
