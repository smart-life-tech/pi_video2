import pygame
import sys
import time
import os
import subprocess
import psutil
import cv2
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/deg/pi_video2/test.mp4"  # Change to your MP4 path
IMAGE_PATH = "/home/deg/pi_video2/black.png"  # Fullscreen black image
GPIO_INPUT = 22  # Connected to GND to trigger webcam
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None
mpv_process = None

# === SETUP GPIO INPUT (pull-up enabled) ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)

# === SETUP PYGAME BLACK SCREEN ===
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
image = pygame.image.load(IMAGE_PATH)
image = pygame.transform.scale(image, (screen_width, screen_height))
pygame.mouse.set_visible(False)

# === FUNCTIONS ===
def draw_black_screen():
    screen.fill((0, 0, 0))
    screen.blit(image, (0, 0))
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
    print("[INFO] Playing video...")
    kill_mpv()
    mpv_process = subprocess.Popen([
        "mpv",
        "--fs",
        "--loop",
        "--ontop",
        "--no-border",
        "--geometry=0:0",
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
    subprocess.call(["wmctrl", "-r", "Webcam Feed", "-b", "add,above"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    while True:
        if input_pin.value == 1:
            break
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam")
            break

        frame_resized = cv2.resize(frame, (1280, 720))
        cv2.imshow('Webcam Feed', frame_resized)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# === MAIN LOOP ===
try:
    print("[BOOT] Starting...")
    while True:
        draw_black_screen()  # Always show black background

        if input_pin.value == 1:  # NOT grounded -> Play video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                play_video()

        else:  # GROUNDED -> Show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                show_webcam()

        pygame.event.pump()  # Keep Pygame window responsive
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    kill_mpv()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()
    
