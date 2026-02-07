import time
import board
import adafruit_dht

# Sensor Configuration
DHT_PIN = board.D4
READ_INTERVAL = 5

dht = adafruit_dht.DHT22(DHT_PIN)

print("Testing DHT22")
print(f"Data Pin: GPIO4")
print(f"Reading Interval: {READ_INTERVAL} seconds")
print()

# 5-second initialization
print("Initializing sensor...\n")

for i in range(5, 0, -1):
    print(f"Starting in {i} seconds...")
    time.sleep(1)

print("\nReadings:")

try:
    while True:
        try:
            # Read sensor
            temperature = dht.temperature
            humidity = dht.humidity
            
            # Dispaly output
            print(f"Temperature: {temperature:.1f}°C")
            print(f"Humidity: {humidity:.1f}%")
            print()
            
        except RuntimeError:
            print(f"Reading failed, retrying...\n")
            
        time.sleep(READ_INTERVAL)
        
except KeyboardInterrupt:
    print("\nStopped")
    dht.exit
