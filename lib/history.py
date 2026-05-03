import json
from config import Value


class HistoryManager:
    def __init__(self):
        self.history_records = []
        self.history_index = 0
        self.viewing_detail = False
        self.cfg = Value()

    def load_data(self, patient_name):
        self.history_records = []
        self.history_index = 0
        self.viewing_detail = False
        with open(self.cfg.HISTORY_FILE, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                for record in data:
                    if record.get("patient_name") == patient_name:
                        self.history_records.append(record)
                self.history_records.reverse()

    def scroll(self, steps):
        if steps != 0 and len(self.history_records) > 0 and not self.viewing_detail:
            self.history_index -= steps
            if self.history_index < 0:
                self.history_index = 0
            # back option
            elif self.history_index > len(self.history_records):
                self.history_index = len(self.history_records)

    def select_record(self):
        if len(self.history_records) > 0:
            self.viewing_detail = True

    def back_to_list(self):
        self.viewing_detail = False

    def get_current_record(self):
        if len(self.history_records) == 0:
            return None
        return self.history_records[self.history_index]

    def get_total_records(self):
        return len(self.history_records)

    def get_index(self):
        return self.history_index
