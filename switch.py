import pygame
import cv2
import subprocess
import time
import psutil
import os
import sys
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"
BLACK_IMAGE = "/home/deg/pi_video2/black.png"
GPIO_INPUT = 22  # Connected to GND to trigger webcam
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None
mpv_process = None

# === SETUP GPIO INPUT ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === INIT PYGAME FOR BLACK SCREEN ===
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
black_image = pygame.image.load(BLACK_IMAGE)
black_image = pygame.transform.scale(black_image, (screen_width, screen_height))

def show_black_screen():
    screen.blit(black_image, (0, 0))
    pygame.display.flip()

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
    print("[INFO] Playing stored video...")
    kill_mpv()
    mpv_process = subprocess.Popen([
        "mpv", "--fs", "--loop", "--ontop", VIDEO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def show_webcam():
    print("[INFO] Showing webcam...")
    kill_mpv()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    window_name = "Webcam Feed"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Use wmctrl to force window on top (after a short delay)
    subprocess.Popen(["wmctrl", "-r", window_name, "-b", "add,above"])

    while True:
        # If pin is grounded (0), stop showing webcam
        if input_pin.value == 0:
            break

        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam")
            break

        frame_resized = cv2.resize(frame, (screen_width, screen_height))
        cv2.imshow(window_name, frame_resized)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            break

    cap.release()
    cv2.destroyAllWindows()

# === MAIN LOOP ===
try:
    print("[BOOT] Starting...")
    show_black_screen()

    while True:
        # When GPIO22 is grounded (value=0) → show webcam
        if input_pin.value == 0:
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                show_black_screen()
                show_webcam()
                show_black_screen()

        # When GPIO22 is ungrounded (value=1) → play video
        else:
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                show_black_screen()
                play_video()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    kill_mpv()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()
