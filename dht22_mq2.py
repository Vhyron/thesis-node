import time
import board
import busio
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

DHT22_I2C_PAUSE = 5

# Initialized DHT22 sensor on GPIO4
dht = adafruit_dht.DHT22(board.D4, use_pulseio=False)

# Initialized I2C and ADS1115 for MQ2
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
mq2 = AnalogIn(ads, 0)

# 5-second initialization delay
print("DHT22 + MQ2")
print(f"Initializing sensors for 5 seconds...")

for i in range(5, 0, -1):
    time.sleep(1)

print("\nReadings:")

try:
    while True:
        # Read DHT22 with error handling
        temperature = None
        hunidity = None
        for _ in range(5):
            try:
                temprature = dht.temperature
                humidity = dht.humidity
                if temperature is not None and humidity is not None:
                    break
            except RuntimeError:
                time.sleep(0.5)
                continue
        
        # Small pause to let DHT22 settle before I2C starts
        time.sleep(DHT22_I2C_PAUSE)
        
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
        if temperature is not None and humidity is not None:
            print(f"Temperature: {temperature:.1f}°C")
            print(f"Humidity: {humidity:.1f}%")
        else:
            print(f"Temperature: -- (Reading Failed)")
            print(f"Humidity: -- (Reading Failed)")
            
        print(f"Gas Level: {ppm:4.0f} PPM ({gas_status})")
        print()
        
        time.sleep(2)
        
except KeyboardInterrupt:
    dht.exit()