class Value:
    def __init__(self):
        self.pico_size = 500
        self.sample_rate = 250
        self.I2C_ID = 1
        self.I2C_SCL_PIN = 15
        self.I2C_SDA_PIN = 14
        self.ADC_PIN = 26
        self.LED_PIN = 20
        self.BUTTON_PIN = 12
        self.OLED_WIDTH = 128
        self.OLED_HIGHT = 64
        self.SSID = "KME759_G1"
        self.PASSWORD = "123456789"
        self.BROKER_IP = "192.168.1.253"
        self.BROKER_PORT = 21883
        self.REQUEST_TOPIC = b"kubios/request"
        self.RESPONSE_TOPIC = b"kubios/response"
        self.OUTPUT_FILE = "kubios_response.json"
        self.TIMEOUT_MS = 15000
        self.DB_TOPIC = b"database/records/add"
        self.PATIENT_NAME = "Patient1"
        self.PATIENT_REGISTER_TOPIC = b"database/patients/add"
        self.DB_RESPONSE_TOPIC = b"database/response"
