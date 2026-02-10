import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initializing I2C
i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)

mq2 = AnalogIn(ads, 0)


# 20-Second initialization
print("Testing MQ2")
print(f"Initializing sensor for 20 seconds...")

for i in range(20, 0, -1):
    time.sleep(1)

print("\nReadings:")

try:
    while True:
        # Read voltage from ADS1115 adn convert to PPM estimate
        voltage = mq2.voltage
        
        # Single linear mapping
        ppm = (voltage / 4.096) * 1000 # Rough estimate
        
        # Threshold-based detection
        if ppm < 300:
            status = "Clean"
        elif ppm < 600:
            status = "Gas/Smoke Detected"
        else:
            status = "High Gas/Smoke"
            
        # Display Output
        print(f"Gas Level: {ppm:4.0f} PPM | {status}")
        
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\nStopped")

