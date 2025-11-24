import RPi.GPIO as GPIO
import time

DOOR1_PIN = 17  # Cam bien cua 1
DOOR2_PIN = 27  # Cam bien cua 2

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DOOR1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DOOR2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    print("Da khoi tao 2 cam bien tren GPIO {} va {}".format(DOOR1_PIN, DOOR2_PIN))
    print("Nhan Ctrl+C de dung chuong trinh.")

def loop():
    try:
        while True:
            state1 = GPIO.input(DOOR1_PIN)
            state2 = GPIO.input(DOOR2_PIN)
            
            if state1 == GPIO.HIGH:
                status1 = "MO (Open)"
            else:
                status1 = "DONG (Closed)"
                
            if state2 == GPIO.HIGH:
                status2 = "MO (Open)"
            else:
                status2 = "DONG (Closed)"

            print("Cua 1: {}  |  Cua 2: {}".format(status1, status2))
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDang dung chuong trinh...")
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    setup()
    loop()
