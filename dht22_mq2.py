import time
import board
import busio
import threading
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

dht_temperature = None
dht_humidity = None

def read_dht22_loop():
    global dht_temperature, dht_humidity
    
    dht = adafruit_dht.DHT22(board.D4, use_pulseio=False)
    
    while True:
        # Read DHT22 with error handling
        try:
            t = dht.temperature
            h = dht.humidity
            if t is not None and h is not None:
                dht_temperature = t
                dht_humidity = h
        except RuntimeError:
            pass # Ignore failed reads, keep trying
        time.sleep(2)
        
# Start DHT22 in background thread
dht_thread = threading.Thread(target=read_dht22_loop, daemon=True)
dht_thread.start()

# Initialized I2C and ADS1115 for MQ2
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
mq2 = AnalogIn(ads, 0)

# 5-second initialization delay
print("DHT22 + MQ2")
print(f"Reading Intervals: 2 (dev)")
print(f"Initializing sensors for 5 seconds...")

for i in range(5, 0, -1):
    time.sleep(1)

print("\nReadings:")

try:
    while True:
        # Read MQ2 with error handling
        voltage = mq2.voltage
        ppm = (voltage / 4.096) * 1000
        
        if ppm < 300:
            gas_status = "Clean"
        elif ppm < 600:
            gas_status = "Detected"
        else:
            gas_status = "High"
            
        # Display output
        if dht_temperature is not None and dht_humidity is not None:
            print(f"Temperature: {dht_temperature:.1f}°C")
            print(f"Humidity: {dht_humidity:.1f}%")
        else:
            print(f"Temperature: -- (Reading Failed)")
            print(f"Humidity: -- (Reading Failed)")
            
        print(f"Gas Level: {ppm:4.0f} PPM ({gas_status})")
        print()
        
        time.sleep(2)
        
except KeyboardInterrupt:
    dht.exit()