from gpiozero import DigitalInputDevice
import cv2
import subprocess
import time
import psutil

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"
GPIO_INPUT = 22  # Connected to GND to play video
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None
mpv_process = None

# === SETUP GPIO INPUT (pull-up enabled) ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === UTILS ===
def kill_mpv():
    global mpv_process
    if mpv_process:
        mpv_process.terminate()
        mpv_process = None
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "mpv" in proc.info['name'].lower():
            try:
                proc.terminate()
            except Exception:
                pass

def play_video():
    global mpv_process
    print("[INFO] Playing video...")
    kill_mpv()
    mpv_process = subprocess.Popen([
        "mpv",
        "--fs",
        "--loop",
        VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def show_webcam():
    print("[INFO] Showing webcam...")
    kill_mpv()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Webcam Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        # Exit webcam mode if pin goes LOW (grounded)
        if input_pin.value == 0:
            break

        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam")
            break

        frame_resized = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame_resized)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to manually exit
            break

    cap.release()
    cv2.destroyAllWindows()

# === MAIN LOOP ===
try:
    print("[BOOT] Starting...")
    while True:
        if input_pin.value == 0:  # GPIO22 grounded → Play video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                play_video()
        else:  # GPIO22 not grounded → Show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                show_webcam()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    kill_mpv()
    cv2.destroyAllWindows()
    
