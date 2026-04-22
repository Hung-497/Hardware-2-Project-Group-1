import json
import time
import network
import ubinascii
from umqtt.simple import MQTTClient

from config import Value


class KubiosExample:
    def __init__(self, bpm_data, current_bpm=0):
        self.cfg = Value()
        self.bpm_data = bpm_data
        self.current_bpm = current_bpm
        # This variable will store the latest valid MQTT response
        # that arrives from kubios/response.
        self.latest_response = None
        self.latest_db_response = None
        self.patient_id = None

    def mqtt_callback(self, topic, msg):
        if topic == self.cfg.RESPONSE_TOPIC:
            self.latest_response = json.loads(msg)
        elif topic == self.cfg.DB_RESPONSE_TOPIC:
            self.latest_db_response = json.loads(msg)

    def connect_wifi(self):
        # Create the Pico W Wi-Fi interface in station mode.
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # Connect only if not already connected.
        if not wlan.isconnected():
            print("Connecting to Wi-Fi...")
            wlan.connect(self.cfg.SSID, self.cfg.PASSWORD)

            # Keep waiting until the Pico successfully connects.
            while not wlan.isconnected():
                pass

        # Show the Pico's local IP address after connection.
        print("Wi-Fi connected:", wlan.ifconfig()[0])
        return wlan

    def get_pico_mac(self, wlan):
        # Read the real hardware MAC address of this Pico from the Wi-Fi interface.
        # Convert it into uppercase hexadecimal format, for example AABBCCDDEEFF.
        mac_bytes = wlan.config("mac")
        return ubinascii.hexlify(mac_bytes).decode().upper()

    def build_request_payload(self, mac_address):
        return {
            "mac": mac_address,
            "type": "RRI",
            "data": self.bpm_data,
            "analysis": {"type": "readiness"}
        }

    def build_db_payload(self, mac_address):
        # note!!!! place the real data
        return {
            "mac": mac_address,
            "timestamp": time.time(),
            "patient_id": getattr(self, "patient_id", 1),
            "mean_ppi": 800.0,
            "mean_hr": 70,
            "rmssd": 35.0,
            "sdnn": 50.0,
            "sns": 1.234,
            "pns": -1.234,
        }

    def save_json_to_pico(self, filename, data):
        with open(filename, "w") as file:
            json.dump(data, file)

    def run(self):
        # Step 1: Connect the Pico to Wi-Fi.
        wlan = self.connect_wifi()

        # Step 1b: sync time
        try:
            import ntptime
            ntptime.settime()
            print("Time synchronized via NTP.")
        except Exception as e:
            print("NTP sync failed:", e)

        # Step 2: Read the real MAC address of this Pico.
        real_mac = self.get_pico_mac(wlan)

        # Step 3: Create the MQTT client and connect it to the broker.
        client = MQTTClient(
            client_id=real_mac, server=self.cfg.BROKER_IP, port=self.cfg.BROKER_PORT)

        # Register the callback function for incoming MQTT messages.
        client.set_callback(self.mqtt_callback)
        client.connect()

        # Subscribe to both Kubios and Database response topics
        client.subscribe(self.cfg.RESPONSE_TOPIC)
        client.subscribe(self.cfg.DB_RESPONSE_TOPIC)

        # Register Patient
        patient_payload = {
            "mac": real_mac,
            "patient_name": self.cfg.PATIENT_NAME
        }

        register_topic = self.cfg.PATIENT_REGISTER_TOPIC
        print("Registering patient to:", register_topic)
        client.publish(register_topic, json.dumps(patient_payload))

        start = time.ticks_ms()
        while True:
            client.check_msg()
            if self.latest_db_response and self.latest_db_response.get("mac") == real_mac:
                if self.latest_db_response.get("message") == "OK":
                    self.patient_id = self.latest_db_response.get("data", 1)
                else:
                    self.patient_id = 1
                print("Patient registered, ID:", self.patient_id)
                break

        # Publish payload
        db_topic = self.cfg.DB_TOPIC
        db_payload = self.build_db_payload(real_mac)
        if db_payload:
            client.publish(db_topic, json.dumps(db_payload))
            print("Published to database:", db_payload)

        # Publish to Kubios
        self.latest_response = None
        request_payload = self.build_request_payload(real_mac)
        print("Published to kubios/request")
        client.publish(self.cfg.REQUEST_TOPIC, json.dumps(request_payload))

        start = time.ticks_ms()
        while True:
            client.check_msg()

            if self.latest_response and self.latest_response.get("mac") == real_mac:
                print("Response received:")
                print(json.dumps(self.latest_response))
                self.save_json_to_pico(
                    self.cfg.OUTPUT_FILE, self.latest_response)
                print("Saved to file:", self.cfg.OUTPUT_FILE)
                break

            if time.ticks_diff(time.ticks_ms(), start) > self.cfg.TIMEOUT_MS:
                raise RuntimeError(
                    "Timed out while waiting for kubios/response")

        # Disconnect cleanly after the work is done.
        client.disconnect()
        print("Done.")
