from config import Value

class UserSelect:
    def __init__(self):
        self.cfg = Value()
        self.patient_names = self.cfg.PATIENT_NAMES
        self.patient_index = 0
        self.patient_name = self.patient_names[self.patient_index]

    def scroll(self, steps):
        if steps != 0:
            self.patient_index += steps
            self.patient_index = self.patient_index % len(self.patient_names)

    def confirm_selection(self):
        self.patient_name = self.patient_names[self.patient_index]
        self.cfg.current_patient = self.patient_name

    def get_current_name(self):
        return self.patient_name

    def get_all_names(self):
        return self.patient_names

    def get_index(self):
        return self.patient_index
