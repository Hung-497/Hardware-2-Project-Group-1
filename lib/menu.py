from history import HistoryManager
from user import UserSelect
import json
from config import Value
from Rotary import Encoder
from hardware import hw
import time
import micropython
micropython.alloc_emergency_exception_buf(200)


class Menu:
    def __init__(self, processor):
        self.measuring = False
        self.last_btn_press = 0
        hw.button.irq(handler=self.btn_handler,
                      trigger=hw.button.IRQ_FALLING, hard=True)

        self.last_ui_update = 0
        self.display_bpm = 0
        self.force_refresh = True
        self.anime_tick = 0

        # menu, measure = 1, data = 2, history n kubios should be 3 n 4 but will add later
        self.screen = "menu"
        self.menu_option = 1

        # time cho HRV
        self.hrv_start_time = 0

        self.cfg = Value()
        self.values = processor

        self.kubios_hr = None
        self.kubios_rmssd = None
        self.kubios_sns = None
        self.kubios_pns = None

        self.user_manager = UserSelect()
        self.history_manager = HistoryManager()
        self.needs_history_load = False

        # rotary encoder
        self.rotary_encoder = Encoder(
            self.cfg.ENCODER_A_PIN, self.cfg.ENCODER_B_PIN)

    def btn_handler(self, pin):
        now = time.ticks_ms()

        # debouncing
        if time.ticks_diff(now, self.last_btn_press) > 500:
            self.last_btn_press = now

            # menu screen
            if self.screen == "menu":
                if self.menu_option == 1:
                    self.screen = "basic_hr"
                    self.measuring = True
                elif self.menu_option == 2:
                    self.screen = "hrv_ready"
                    self.measuring = False
                elif self.menu_option == 3:
                    self.screen = "history"
                    self.measuring = False
                    self.needs_history_load = True
                elif self.menu_option == 4:
                    # can send to kubios now
                    self.screen = "hrv_ready"
                    self.measuring = False
                elif self.menu_option == 5:
                    self.screen = "user_select"
                    self.measuring = False

            # HR screen
            elif self.screen == "basic_ready":
                self.screen = "menu"
                self.measuring = False

            # HRV screen
            elif self.screen == "hrv_ready":
                self.screen = "hrv_collect"
                self.measuring = True
                self.hrv_start_time = time.ticks_ms()

            # History screen
            elif self.screen == "history":
                if self.history_manager.viewing_detail:
                    self.history_manager.back_to_list()
                elif self.history_manager.get_total_records() == 0:
                    self.screen = "menu"
                    self.measuring = False
                elif self.history_manager.get_index() >= self.history_manager.get_total_records():
                    # click back
                    self.screen = "menu"
                    self.measuring = False
                else:
                    self.history_manager.select_record()

            elif self.screen == "user_select":
                self.screen = "menu"
                self.user_manager.confirm_selection()
                self.measuring = False

            # Kubios screen
            elif self.screen == "kubios":
                self.screen = "menu"
                self.measuring = False

            # screen HRV result
            elif self.screen == "hrv_result":
                self.screen = "menu"
                self.measuring = False

            # collecting n sending screen if press can back to menu
            else:
                self.screen = "menu"
                self.measuring = False

            self.force_refresh = True

    def load_kubios_data(self):
        try:
            with open(self.cfg.OUTPUT_FILE, 'r') as f:
                data = json.load(f)
            self.kubios_hr = round(data["data"]["analysis"]["mean_hr_bpm"], 1)
            self.kubios_ppi = round(data["data"]["analysis"]["mean_rr_ms"], 1)
            self.kubios_rmssd = round(data["data"]["analysis"]["rmssd_ms"], 1)
            self.kubios_sdnn = round(data["data"]["analysis"]["sdnn_ms"], 1)
            self.kubios_sns = round(data["data"]["analysis"]["sns_index"], 2)
            self.kubios_pns = round(data["data"]["analysis"]["pns_index"], 2)
        except Exception as e:
            print("Error loading kubios data:", e)
            self.kubios_hr = None

    def read_encoder(self):
        steps = 0
        while self.rotary_encoder.fifo.has_data():
            steps += self.rotary_encoder.fifo.get()
        return steps

    def update_menu(self):
        if self.screen == "menu":
            steps = self.read_encoder()
            if steps != 0:
                self.menu_option += steps

                if self.menu_option < 1:
                    self.menu_option = 5
                elif self.menu_option > 5:
                    self.menu_option = 1

                self.force_refresh = True

        elif self.screen == "user_select":
            steps = self.read_encoder()
            if steps != 0:
                self.user_manager.scroll(steps)
                self.force_refresh = True

        elif self.screen == "history":
            steps = self.read_encoder()
            if steps != 0:
                self.history_manager.scroll(steps)
                self.force_refresh = True

    def update_hrv_state(self):
        now = time.ticks_ms()

        # demo time
        if self.screen == "hrv_collect":

            if time.ticks_diff(now, self.hrv_start_time) >= 30000:
                self.screen = "hrv_send"
                self.measuring = False
                self.hrv_start_time = now
                self.force_refresh = True

        elif self.screen == "hrv_send":
            if time.ticks_diff(now, self.hrv_start_time) >= 2000:
                if self.menu_option == 4:
                    self.screen = "kubios"
                    self.load_kubios_data()
                else:
                    self.screen = "hrv_result"
                self.measuring = False
                self.force_refresh = True

    def draw_menu(self):
        hw.oled.fill(0)
        hw.oled.text("MENU", 48, 0)

        options = ["1. MEASURE HR", "2. HRV ANALYSIS",
                   "3. History", "4. Kubios", "5. User"]
        for i, opt in enumerate(options):
            y = 12 + (i * 10)
            if self.menu_option == i + 1:
                hw.oled.text(f"> {opt}", 0, y)
            else:
                hw.oled.text(f"  {opt}", 0, y)

        hw.oled.show()

    def draw_user_select(self):
        hw.oled.fill(0)
        hw.oled.text("SELECT USER", 20, 0)

        names = self.user_manager.get_all_names()
        idx = self.user_manager.get_index()

        for i, name in enumerate(names):
            y = 20 + (i * 12)
            if idx == i:
                hw.oled.text(f"> {name}", 20, y)
            else:
                hw.oled.text(f"  {name}", 20, y)

        hw.oled.text("PRESS TO SELECT", 4, 54)
        hw.oled.show()

    def draw_basic_hr(self, current_bpm, disp):
        self.display_bpm = current_bpm
        self.anime_tick += 1
        frames = ["^_^", "-_-", "^_^", "^_-"]
        anime_char = frames[self.anime_tick % len(frames)]

        hw.oled.fill(0)

        if self.display_bpm > 0:
            hw.oled.text(str(self.display_bpm) + " BPM ", 0, 0)
        else:
            hw.oled.text("CALCULATING... ", 0, 0)

        if disp is not None:
            disp.draw_graph(0, 10, 128, 54)

        hw.oled.show()

    def draw_hrv_ready(self):
        hw.oled.fill(0)
        hw.oled.text("START MEASUREMENT", 0, 0)
        hw.oled.text("PLACE YOUR FINGER", 0, 14)
        hw.oled.text("ON THE SENSOR", 0, 26)
        hw.oled.text("PRESS BUTTON", 0, 40)
        hw.oled.text("TO START", 20, 54)
        hw.oled.show()

    def draw_hrv_collect(self):
        self.anime_tick += 1
        frames = [".", "..", "..."]
        dots = frames[self.anime_tick % len(frames)]

        hw.oled.fill(0)
        hw.oled.text("COLLECTING DATA", 0, 20)
        hw.oled.text(dots, 50, 36)
        hw.oled.show()

    def draw_hrv_send(self):
        self.anime_tick += 1
        frames = [".", "..", "..."]
        dots = frames[self.anime_tick % len(frames)]

        hw.oled.fill(0)
        hw.oled.text("SENDING DATA", 8, 20)
        hw.oled.text(dots, 50, 36)
        hw.oled.show()

    def draw_hrv_result(self):
        hw.oled.fill(0)
        hw.oled.text("MEAN HR: " + str(self.values.mean_hr), 0, 0)
        hw.oled.text("MEAN PPI: " + str(self.values.mean_interval), 0, 14)
        hw.oled.text("RMSSD: " + str(round(self.values.rmssd_val, 3)), 0, 28)
        hw.oled.text("SDNN: " + str(round(self.values.sdnn_val, 3)), 0, 42)
        hw.oled.show()

    def draw_history(self):
        hw.oled.fill(0)
        name = self.user_manager.get_current_name()
        total = self.history_manager.get_total_records()

        if total == 0:
            hw.oled.text(f"HIST: {name}", 0, 0)
            hw.oled.text("NO DATA YET", 20, 24)
            hw.oled.text("PRESS TO BACK", 12, 54)
        elif self.history_manager.viewing_detail:
            record = self.history_manager.get_current_record()
            idx = self.history_manager.get_index()
            ts = record.get("local_timestamp", "")
            hw.oled.text(f"REC {idx+1}: {ts}", 0, 0)
            hw.oled.text(f"HR: {int(record.get('mean_hr', 0))}", 0, 14)
            hw.oled.text(f"PPI:{int(record.get('mean_ppi', 0))}", 64, 14)
            hw.oled.text(f"RMS:{int(record.get('rmssd', 0))}", 0, 26)
            hw.oled.text(f"SDN:{int(record.get('sdnn', 0))}", 64, 26)
            hw.oled.text(f"SNS:{round(record.get('sns', 0), 3)}", 0, 38)
            hw.oled.text(f"PNS:{round(record.get('pns', 0), 3)}", 64, 38)
            hw.oled.text("PRESS TO BACK", 12, 54)
        else:
            hw.oled.text(f"HIST: {name}", 0, 0)
            idx = self.history_manager.get_index()
            # total + back
            items = total + 1
            # show 4 items
            start = max(0, idx - 1)
            end = min(items, start + 4)
            if end - start < 4:
                start = max(0, end - 4)
            for i in range(start, end):
                y = 12 + ((i - start) * 11)
                if i < total:
                    r = self.history_manager.history_records[i]
                    ts = r.get("local_timestamp", f"Rec {i+1}")
                else:
                    ts = "BACK"
                if i == idx:
                    hw.oled.text(f">{ts}", 0, y)
                else:
                    hw.oled.text(f" {ts}", 0, y)
            hw.oled.text("PRESS TO SELECT", 8, 54)
        hw.oled.show()

    def draw_kubios(self):
        hw.oled.fill(0)
        hw.oled.text("KUBIOS RESULT", 0, 0)

        if self.kubios_hr is not None:
            hw.oled.text(f"HR:{int(self.kubios_hr)}", 0, 14)
            hw.oled.text(f"PPI:{int(self.kubios_ppi)}", 0, 26)
            hw.oled.text(f"SNS:{self.kubios_sns}", 0, 38)

            hw.oled.text(f"RMS:{int(self.kubios_rmssd)}", 64, 14)
            hw.oled.text(f"SDN:{int(self.kubios_sdnn)}", 64, 26)
            hw.oled.text(f"PNS:{self.kubios_pns}", 64, 38)

            hw.oled.text("PRESS TO BACK", 12, 54)
        else:
            hw.oled.text("NO DATA YET", 12, 32)
            hw.oled.text("PRESS TO BACK", 12, 54)

        hw.oled.show()

    def update_display(self, current_bpm, disp=None):
        now = time.ticks_ms()

        if self.needs_history_load:
            self.history_manager.load_data(
                self.user_manager.get_current_name())
            self.needs_history_load = False

        self.update_menu()
        self.update_hrv_state()

        # update screen
        if time.ticks_diff(now, self.last_ui_update) >= 80 or self.force_refresh:
            self.last_ui_update = now
            self.force_refresh = False

            if self.screen == "menu":
                self.draw_menu()

            elif self.screen == "basic_hr":
                self.draw_basic_hr(current_bpm, disp)

            elif self.screen == "hrv_ready":
                self.draw_hrv_ready()

            elif self.screen == "hrv_collect":
                self.draw_hrv_collect()

            elif self.screen == "hrv_send":
                self.draw_hrv_send()

            elif self.screen == "hrv_result":
                self.draw_hrv_result()

            elif self.screen == "history":
                self.draw_history()

            elif self.screen == "kubios":
                self.draw_kubios()

            elif self.screen == "user_select":
                self.draw_user_select()
