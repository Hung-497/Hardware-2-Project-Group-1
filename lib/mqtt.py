import json
import time
import network
import ubinascii
from storage import Storage
from umqtt.simple import MQTTClient

from config import Value


class KubiosExample:
    def __init__(self, bpm_data, ppi, current_bpm=0, patient_name="Hung"):
        self.cfg = Value()
        self.bpm_data = bpm_data
        self.current_bpm = current_bpm
        # This variable will store the latest valid MQTT response
        # that arrives from kubios/response.
        self.latest_response = None
        self.latest_db_response = None
        self.patient_id = None
        self.patient_name = patient_name
        self.local_time_db = None
        self.local_time_pico = None
        self.values = ppi

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
        t = time.localtime(time.time() + 3*3600)
        self.local_time_db = f"{t[1]:02d}_{t[2]:02d}_{t[3]:02d}_{t[4]:02d}"
        self.local_time_pico = f"{t[1]:02d}/{t[2]:02d}/{t[0]:04d} {t[3]:02d}:{t[4]:02d}"
        return {
            "mac": mac_address,
            "type": "RRI",
            "data": self.bpm_data,
            "analysis": {"type": "readiness"}
        }

    def build_db_payload(self, mac_address):
        # retrieve from processing
        print()
        # read the file
        with open(self.cfg.OUTPUT_FILE, 'r') as file:
            data = json.load(file)
        # note!!!! place the real data
        return {
            "mac": mac_address,
            "timestamp": int(self.local_time_db),
            "patient_name": self.patient_name,
            "patient_id": self.patient_id,
            "mean_ppi": self.values.mean_interval,
            "mean_hr": data["data"]["analysis"]["mean_hr_bpm"],
            "rmssd": data["data"]["analysis"]["rmssd_ms"],
            "sdnn": data["data"]["analysis"]["sdnn_ms"],
            "sns": data["data"]["analysis"]["sns_index"],
            "pns": data["data"]["analysis"]["pns_index"],
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
            "patient_name": self.patient_name
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

        # Publish to Kubios
        self.latest_response = None
        request_payload = self.build_request_payload(real_mac)
        print("Published to kubios/request", request_payload)
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
                # Publish payload
                db_topic = self.cfg.DB_TOPIC
                db_payload = self.build_db_payload(real_mac)
                if db_payload:
                    client.publish(db_topic, json.dumps(db_payload))
                    print("Published to database:", db_payload)
                    # add localtime only in local
                    db_payload["local_timestamp"] = self.local_time_pico
                    try:
                        Storage().save_hrv_data(db_payload)
                    except Exception as e:
                        print("Failed local:", e)
                break

            if time.ticks_diff(time.ticks_ms(), start) > self.cfg.TIMEOUT_MS:
                raise RuntimeError(
                    "Timed out while waiting for kubios/response")

        # Disconnect cleanly after the work is done.
        client.disconnect()
        print("Done.")
