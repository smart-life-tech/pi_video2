import cv2
import pygame
import subprocess
import time
import threading
import psutil
from gpiozero import DigitalInputDevice

# === CONFIG ===
VIDEO_FILE = "/home/pi/pi_video2/test.mp4"  # Change to your MP4 path
IMAGE_PATH = "/home/pi/pi_video2/black.png"  # Black screen or logo
GPIO_INPUT = 22  # Connect to GND to play video
STATE_VIDEO = 0
STATE_CAMERA = 1

# === GLOBAL STATE ===
current_state = None
mpv_process = None


# === Black Screen / Logo Display Using Pygame ===
class PygameDisplay:
    def __init__(self, image_path):
        self.image_path = image_path
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run_display)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        pygame.quit()

    def _run_display(self):
        pygame.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        screen_width, screen_height = screen.get_size()

        try:
            image = pygame.image.load(self.image_path)
            image = pygame.transform.scale(image, (screen_width, screen_height))
        except Exception as e:
            print(f"[ERROR] Loading image: {e}")
            image = None

        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            screen.fill((0, 0, 0))
            if image:
                screen.blit(image, (0, 0))
            pygame.display.flip()
            clock.tick(30)


# === GPIO Setup ===
input_pin = DigitalInputDevice(GPIO_INPUT, pull_up=True)
black_screen = PygameDisplay(IMAGE_PATH)


# === Utils ===
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
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera")
        return

    cv2.namedWindow("Webcam Feed", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Webcam Feed", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        # If grounded again, stop showing webcam
        if input_pin.value == 0:
            break
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam")
            break
        frame_resized = cv2.resize(frame, (1280, 720))
        cv2.imshow("Webcam Feed", frame_resized)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# === MAIN LOOP ===
try:
    print("[BOOT] System started")
    while True:
        if input_pin.value == 0:  # GPIO22 grounded → Play video
            if current_state != STATE_VIDEO:
                current_state = STATE_VIDEO
                print("[STATE] VIDEO mode")
                black_screen.stop()
                kill_mpv()
                play_video()
                black_screen.start()

        else:  # GPIO22 not grounded → Show webcam
            if current_state != STATE_CAMERA:
                current_state = STATE_CAMERA
                print("[STATE] CAMERA mode")
                black_screen.stop()
                kill_mpv()
                show_webcam()
                black_screen.start()

        time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    kill_mpv()
    black_screen.stop()
    cv2.destroyAllWindows()
        
