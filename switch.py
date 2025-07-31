from gpiozero import DigitalInputDevice
import cv2
import subprocess
import time
import psutil

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"
GPIO_INPUT = 22  # Connected to GND to switch
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None

# === SETUP GPIO INPUT (pull-up enabled) ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === UTILS ===
def kill_mpv():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "mpv" in proc.info['name'].lower():
            try:
                proc.terminate()
            except Exception:
                pass

def play_video():
    print("[INFO] Playing video...")
    kill_mpv()
    return subprocess.Popen([
        "mpv",
        "--fs",
        "--loop",
        VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def show_webcam():
    print("[INFO] Showing webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    while input_pin.value == 0:  # Still grounded
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame_resized)
        if cv2.waitKey(1) == 27:  # Esc to quit manually
            break

    cap.release()
    cv2.destroyAllWindows()

# === MAIN LOOP ===
try:
    print("[BOOT] Starting...")
    while True:
        if input_pin.value == 0:  # Not grounded
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                play_video()
        else:  # Grounded
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                kill_mpv()
                show_webcam()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")
    kill_mpv()
    cv2.destroyAllWindows()
    
