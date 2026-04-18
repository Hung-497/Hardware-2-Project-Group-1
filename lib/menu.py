from hardware import hw
import time
import micropython
micropython.alloc_emergency_exception_buf(200)


class Menu:
    def __init__(self):
        self.measuring = False
        self.last_btn_press = 0
        hw.button.irq(handler=self.btn_handler, trigger=hw.button.IRQ_FALLING, hard=True)
        self.last_ui_update = 0
        self.display_bpm = 0
        self.force_refresh = False
        self.anime_tick = 0

    def btn_handler(self, pin):
        now = time.ticks_ms()
        # debouncing
        if time.ticks_diff(now, self.last_btn_press) > 600:
            self.measuring = not self.measuring
            self.last_btn_press = now
            self.force_refresh = not self.force_refresh

    def update_display(self, current_bpm):
        now = time.ticks_ms()
        # idle screen
        if not self.measuring:
            if not self.force_refresh:
                hw.oled.fill(0)
                hw.oled.text("START MEASUREMENT", 0, 10)
                hw.oled.text("BY PRESSING", 0, 25)
                hw.oled.text("THE BUTTON", 0, 40)
                hw.oled.show()
                print("")
        else:
            # measuring screen update every 1 sec
            if time.ticks_diff(now, self.last_ui_update) >= 1000 or self.force_refresh:
                self.display_bpm = current_bpm
                self.last_ui_update = now

                # Setup a tiny 4-frame animation loop
                self.anime_tick += 1
                frames = ["-", "\\", "|", "/"]
                anime_char = frames[self.anime_tick % len(frames)]

                hw.oled.fill(0)
                # if it has computed
                if self.display_bpm > 0:
                    hw.oled.text(
                        f"{self.display_bpm} BPM  {anime_char}", 30, 20)
                else:
                    hw.oled.text(f"CALCULATING. {anime_char}", 10, 20)

                hw.oled.text("PRESS THE BUTTON", 0, 40)
                hw.oled.text("TO STOP", 30, 50)
                hw.oled.show()
