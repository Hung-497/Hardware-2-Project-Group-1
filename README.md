# Hardware-2-Project-Group-1
## iMuha
iMuha is a health prototype that measures heart rate and performs Heart Rate Variability (HRV) analysis using Raspberry Pi Pico W and Kubios Cloud.

## Installation 

### Hardware Components
- Crowntail Pulse sensor
- Raspberry Pi Pico W
- OLED display (SSD1306 128x64 pixels)
- Grove connector
- USB connector
- Rotary encoder

### Hardware setup
1. Connect the Crowntail Pulse sensor to GP26 of the board using a Grove connector.
2. Connect the OLED display to GP14 (SCL) and GP15 (SDA).
3. Connect the Rotary Encoder to GP10 (Rot_A), GP11 (Rot_B), and GP9 (SW).
4. Connect the Raspberry Pi Pico W to your computer using the USB connector.

### Software setup
1. Install `mpremote` in your terminal in case you haven't installed it yet.
   ```
   pip install mpremote
   ```
2. Clone the repository.
   ```
   git clone https://github.com/Hung-497/Hardware-2-Project-Group-1.git
   ```
3. Check your Pico device name and upload the project to the Pico.
   ```
   mpremote connect list
   python -m mpremote connect <device_name> cp -r ./lib :/lib cp main.py :main.py
   ```
4. Reset the Raspberry Pi Pico W and it should be ready to use.
