import json
import time
import network
import ubinascii
from umqtt.simple import MQTTClient


# Wi-Fi and broker settings.
# Replace these with your own course/lab values before running the program.
SSID = "KME759_G1"
PASSWORD = "123456789"
BROKER_IP = "192.168.1.253"
BROKER_PORT = 21883

# MQTT topics used by the Kubios proxy.
# We publish the request to kubios/request
# and listen for the reply on kubios/response.
REQUEST_TOPIC = b"kubios/request"
RESPONSE_TOPIC = b"kubios/response"

# Name of the file where the latest Kubios response will be saved on the Pico.
# If the program is run again, this file will be overwritten with the new result.
OUTPUT_FILE = "kubios_response.json"

# Maximum waiting time for a Kubios reply, in milliseconds.
TIMEOUT_MS = 15000


class KubiosExample:
    def __init__(self, bpm_data):
        self.bpm_data = bpm_data
        # This variable will store the latest valid MQTT response
        # that arrives from kubios/response.
        self.latest_response = None

    def mqtt_callback(self, topic, msg):
        # This callback function is called automatically whenever
        # a subscribed MQTT message arrives.

        # Ignore messages from any topic other than kubios/response.
        if topic != RESPONSE_TOPIC:
            return

        try:
            # Try to convert the incoming JSON text into a Python object.
            self.latest_response = json.loads(msg)
        except ValueError:
            # If the incoming message is not valid JSON, store None instead.
            self.latest_response = None

    def connect_wifi(self):
        # Create the Pico W Wi-Fi interface in station mode.
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        # Connect only if not already connected.
        if not wlan.isconnected():
            print("Connecting to Wi-Fi...")
            wlan.connect(SSID, PASSWORD)

            # Keep waiting until the Pico successfully connects.
            while not wlan.isconnected():
                time.sleep_ms(250)

        # Show the Pico's local IP address after connection.
        print("Wi-Fi connected:", wlan.ifconfig()[0])
        return wlan

    def get_pico_mac(self, wlan):
        # Read the real hardware MAC address of this Pico from the Wi-Fi interface.
        # Convert it into uppercase hexadecimal format, for example AABBCCDDEEFF.
        mac_bytes = wlan.config("mac")
        return ubinascii.hexlify(mac_bytes).decode().upper()

    def build_request_payload(self, mac_address):
        # Build the JSON request payload that will be sent to the Kubios proxy.
        #
        # "mac" identifies this Pico device
        # "type": "RRI" means the data list contains RR interval / PPI values
        # "analysis": {"type": "readiness"} requests readiness analysis
        return {
            "mac": mac_address,
            "type": "RRI",
            "data": self.bpm_data,
            "analysis": {"type": "readiness"}
        }

    def save_json_to_pico(self, filename, data):
        # Save the Kubios result into a JSON file on the Pico filesystem.
        #
        # Note:
        # Opening with "w" means:
        # - create the file if it does not exist
        # - overwrite the old contents if it already exists
        with open(filename, "w") as file:
            json.dump(data, file)

    def run(self):
        # Step 1: Connect the Pico to Wi-Fi.
        wlan = self.connect_wifi()

        # Step 2: Read the real MAC address of this Pico.
        # This MAC is used in the request and also when checking
        # that the response belongs to this device.
        real_mac = self.get_pico_mac(wlan)

        # Step 3: Create the MQTT client and connect it to the broker.
        client = MQTTClient(client_id=real_mac, server=BROKER_IP, port=BROKER_PORT)

        # Register the callback function for incoming MQTT messages.
        client.set_callback(self.mqtt_callback)

        # Connect to the broker and subscribe to the Kubios response topic.
        client.connect()
        client.subscribe(RESPONSE_TOPIC)

        # Clear any old stored response before sending a new request.
        self.latest_response = None

        # Build the request JSON using the Pico's MAC address.
        request_payload = self.build_request_payload(real_mac)

        # Publish the request to kubios/request.
        print("Published to kubios/request")
        print(json.dumps(request_payload))
        client.publish(REQUEST_TOPIC, json.dumps(request_payload))

        # Save the current time so we can stop waiting after TIMEOUT_MS.
        start = time.ticks_ms()

        # Step 4: Keep checking for incoming MQTT messages.
        while True:
            client.check_msg()

            # If a valid response has arrived and its MAC matches this Pico,
            # print it in the console and save it to a file.
            if self.latest_response and self.latest_response.get("mac") == real_mac:
                print("Response received:")
                print(json.dumps(self.latest_response))

                self.save_json_to_pico(OUTPUT_FILE, self.latest_response)
                print("Saved to file:", OUTPUT_FILE)
                break

            # Stop waiting if the timeout is exceeded.
            if time.ticks_diff(time.ticks_ms(), start) > TIMEOUT_MS:
                raise RuntimeError("Timed out while waiting for kubios/response")

            # Small delay so the loop does not run too aggressively.
            time.sleep_ms(200)

        # Disconnect cleanly after the work is done.
        client.disconnect()
        print("Done.")


