import json
import time


class Storage:
    def __init__(self, filename="history.json"):
        self.filename = filename

    def save_hrv_data(self):
        # import ntptime
        # ntptime.settime()

        # t = time.localtime()
        # timestamp = f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"

        data = {
            # random num
            "timestamp": "timestamp",
            "mean_ppi": 800.0,
            "mean_hr": 70,
            "rmssd": 35.0,
            "sdnn": 50.0,
            "sns": 1.234,
            "pns": -1.234
        }
        # read the old record
        try:
            with open(self.filename, "r") as file:
                history = json.load(file)
        except OSError as e:
            history = []
        # if no data, dict cannot append
        if type(history) is not list:
            history = []
        # add new one
        history.append(data)

        # keep only 5
        history = history[-5:]

        with open(self.filename, "w") as file:
            json.dump(history, file)
