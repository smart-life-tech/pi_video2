import subprocess
import time
import os
import sys
import psutil
import cv2
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"
BLACK_IMAGE = "/home/deg/pi_video2/black.png"
GPIO_INPUT = 22

STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBALS ===
current_state = None
mpv_video_proc = None
mpv_black_proc = None

# === GPIO Setup ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === FUNCTIONS ===
def kill_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and any(name in s for s in proc.info['cmdline']):
                proc.kill()
        except Exception:
            pass

def start_black_screen():
    global mpv_black_proc
    if mpv_black_proc is None or mpv_black_proc.poll() is not None:
        print("[INFO] Starting persistent black screen...")
        kill_process_by_name("black.png")  # Ensure no other black screen is active
        mpv_black_proc = subprocess.Popen([
            "mpv",
            "--fs", "--no-border", "--ontop", "--really-quiet",
            "--geometry=0:0",
            "--loop",
            "--image-display-duration=inf",
            BLACK_IMAGE
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_video():
    global mpv_video_proc
    print("[INFO] Playing video...")
    stop_video()
    mpv_video_proc = subprocess.Popen([
        "mpv",
        "--fs", "--no-border", "--ontop", "--really-quiet",
        "--geometry=0:0",
        "--loop",
        VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_video():
    global mpv_video_proc
    if mpv_video_proc and mpv_video_proc.poll() is None:
        mpv_video_proc.terminate()
        mpv_video_proc.wait()
        mpv_video_proc = None
    kill_process_by_name("mpv")

def show_webcam():
    print("[INFO] Showing webcam...")
    stop_video()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Webcam Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Give time to create the window then raise it
    time.sleep(0.5)
    subprocess.call(["wmctrl", "-r", "Webcam Feed", "-b", "add,above"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    while input_pin.value == 1:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    start_black_screen()  # Restore black background after webcam closes

# === MAIN ===
try:
    print("[BOOT] Starting system...")
    start_black_screen()

    while True:
        if input_pin.value == 0:  # Grounded -> Show video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                play_video()
        else:  # Ungrounded -> Show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                show_webcam()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("[EXIT] Cleaning up...")
    stop_video()
    if mpv_black_proc:
        mpv_black_proc.terminate()
    cv2.destroyAllWindows()
    sys.exit()
    
