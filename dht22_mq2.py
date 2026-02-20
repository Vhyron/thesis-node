import time
import board
import busio
import threading
import adafruit_dht
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from supabase import create_client, Client
from datetime import datetime, timezone

# Supabase Config
SUPABASE_URL 		= "https://cfoxncdbzeiilexpylhx.supabase.co"
SUPABASE_ANON_KEY 	= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNmb3huY2RiemVpaWxleHB5bGh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkyOTgzMTYsImV4cCI6MjA3NDg3NDMxNn0.Iypm_fJCVji7AxHq-XNS_NyBlQz04dDbu3xBkXwBRAM"
NODE_ID 			= 1

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

#Servo Config
SERVO_ANGLES		= [30, 90, 150]
ANGLE_READING_TIME	= 10
current_servo_angle	= None

# DHT Globals
dht_temperature = None
dht_humidity 	= None

def read_dht22_loop():
    global dht_temperature, dht_humidity
    dht = adafruit_dht.DHT22(board.D4, use_pulseio=False)
    while True:	
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

# Risk Classification
RISK_RANK = {None: 0, "HIGH": 1, "CRITICAL": 2}

def classify_dht(temp, hum):
    if temp is None or hum is None:
        return None
    
    if temp >= 50 or hum <40:
        return "critical"
    elif 34 <= temp <= 49 and 40 <= hum <= 65:
        return "high"
    else:
        return None
    
def classify_gas(ppm):
    if ppm < 300:
        return None,		"Clean"
    elif ppm < 600:
        return None,		"Detected"
    elif ppm < 1000:
        return "HIGH",		"High"
    else:
        return "CRITICAL", "Critical"
    
def classify_combined(temp, hum, ppm):
    
    dht_risk			= classify_dht(temp,hum)
    gas_risk, gas_lbl 	= classify_gas(ppm)
    
    final_risk = dht_risk if RISK_RANK[dht_risk] >= RISK_RANK[gas_risk] else gas_risk
    return final_risk, gas_lbl
    

# Payload
def send_fire_event(risk: str, temp, hum, ppm: float, angle):
    payload = {
        "node":				NODE_ID,
        "risk":				risk,
        "temperature":		round(temp, 1) if temp is not None else None,
        "humidity":			round(hum,	1) if hum is not None else None,
        "smoke_gas":		round(ppm, 1),
        "servo_angle":		angle,
        "event_timestamp":	datetime.now(timezone.utc).isoformat(),
        "notified": 		False,
        "session_id":		None,
    }
    try:
        res = supabase.table("fire_events").insert(payload).execute()
        print(f"[Supabase] Event logged - risk={risk}, angle={angle},id={res.data[0].get('id', '?')}")
    except Exception as e:
        print(f"[Supabase] Failed to log event: {e}")

# Servo Movement
def move_to_angle(angle: int):
    global current_servo_angle
    current_servo_angle = angle
    print(f"\nScanning at {angle}°")

# Initialization
print("Detection Node")
print(f"Node ID: {NODE_ID}")
print(f"Initializing sensors for 30 seconds...")

for i in range(30, 0, -1):
    time.sleep(1)
print("\nReadings:")

#Main Loop
try:
    while True:
        for angle in SERVO_ANGLES:
            move_to_angle(angle)
            
            event_logged	= False
            best_risk		= None
            best_ppm		= 0
            best_temp		= None
            best_hum		= None
            angle_end_time	= time.time() + ANGLE_READING_TIME
            
            while time.time() < angle_end_time:
                voltage		= mq2.voltage
                ppm			= (voltage / 4.096) * 1000
                risk, gas_lbl = classify_combined(dht_temperature, dht_humidity, ppm)
                
                # Display
                temp_str 	= f"{dht_temperature:.1f}°C" if dht_temperature is not None else "--"
                hum_str 	= f"{dht_humidity:.1f}%" if dht_humidity is not None else "--"
                dht_risk 	= classify_dht(dht_temperature, dht_humidity)
                
                print(
                    f"Temp: {temp_str} [{dht_risk or 'Normal'}]"
                    f"Hum: {hum_str} [{dht_risk or 'Normal'}]"
                    f"Gas: {ppm:.0f} PPM ({gas_lbl})"
                    f"Combined Risk: {risk or 'Normal'}"
                )
                
                # Track the worst reading
                if RISK_RANK[risk] > RISK_RANK[best_risk]:
                    best_risk 	= risk
                    best_ppm	= ppm
                    best_temp	= dht_temperature
                    best_hum	= dht_humidity
                    
                time.sleep(2)
                
                
            # After 10 second, log the worst reading
            if best_risk is not None and not event_logged:
                if best_temp is not None and best_hum is not None:
                    send_fire_event(best_risk, best_temp, best_hum, best_ppm, current_servo_angle)
                    event_logged = True
                else:
                    print("[Supabase Skipped - waiting for DHT22 reading]")
                    
except KeyboardInterrupt:
    dht.exit()
    print("\nStopped")