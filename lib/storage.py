import json
import time
from config import Value


class Storage:
    def __init__(self):
        self.cfg = Value()

    def save_hrv_data(self, data):
        # read the old record
        try:
            with open(self.cfg.HISTORY_FILE, "r") as file:
                history = json.load(file)
        except OSError as e:
            history = []
            
        # if no data, dict cannot append
        if type(history) is not list:
            history = []
            
        # add new one
        history.append(data)

        # keep only 5 per patient
        new_history = []
        patient_counts = {}
        
        # iterate backwards to get most recent
        for record in reversed(history):
            patient_name = record.get("patient_name")
            if patient_name not in patient_counts:
                patient_counts[patient_name] = 0
                
            if patient_counts[patient_name] < 5:
                new_history.append(record)
                patient_counts[patient_name] += 1
                
        # reverse to chronological order
        history = list(reversed(new_history))

        with open(self.cfg.HISTORY_FILE, "w") as file:
            json.dump(history, file)
