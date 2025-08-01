import subprocess
import time
import sys
import psutil
import cv2
import threading
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"
GPIO_INPUT = 22

STATE_VIDEO = 0
STATE_CAMERA = 1

# === GPIO Setup ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === GLOBAL STATE ===
current_state = None
webcam_thread_running = True

# === FUNCTIONS ===

def kill_existing_mpv():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and any("mpv" in s for s in proc.info['cmdline']):
            try:
                proc.kill()
            except Exception:
                pass

def start_video_loop():
    print("[INIT] Starting mpv video...")
    kill_existing_mpv()
    subprocess.Popen([
        "mpv",
        "--fs", "--no-border", "--ontop",
        "--loop", "--geometry=0:0",
        "--title=VideoPlayer",  # Custom window title
        "--no-osc", "--no-input-default-bindings", "--quiet",
        VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)  # Allow mpv to launch

def webcam_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Webcam Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while webcam_thread_running:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

def raise_window(title):
    subprocess.call(["wmctrl", "-a", title])

def minimize_window(title):
    subprocess.call(["wmctrl", "-r", title, "-b", "add,hidden"])

def restore_window(title):
    subprocess.call(["wmctrl", "-r", title, "-b", "remove,hidden"])
    subprocess.call(["wmctrl", "-a", title])

# === MAIN ===

try:
    print("[BOOT] Starting video and webcam...")
    webcam_loop()

    # Start video thread in background
    webcam_thread = threading.Thread(target=start_video_loop)
    webcam_thread.start()

    time.sleep(2)
    minimize_window("VideoPlayer")  # Initially minimize video player 

    while True:
        if input_pin.value == 1:  # Grounded -> Show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                print("[SWITCH] Showing webcam")
                minimize_window("VideoPlayer")
                restore_window("Webcam Feed")
        else:  # Ungrounded -> Show video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                print("[SWITCH] Showing video")
                minimize_window("Webcam Feed")
                restore_window("VideoPlayer")
        time.sleep(0.2)

except KeyboardInterrupt:
    print("[EXIT] Cleaning up...")
    webcam_thread_running = False
    webcam_thread.join()
    kill_existing_mpv()
    cv2.destroyAllWindows()
    sys.exit()
    
