import time
import threading
import psutil
import winsound
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import os

PROCESS_NAME = "Citrix.DesktopViewer.App.exe"
MISSING_THRESHOLD = 3  # секунд
ALERT_INTERVAL = 15       # секунд
CUSTOM_SOUND = "alert.wav"  # должен лежать рядом с .exe

stop_event = threading.Event()
alerting = threading.Event()
missing_seconds = 0

def process_running(name):
    return any(proc.info['name'] == name for proc in psutil.process_iter(['name']))

def alert_loop():
    while not stop_event.is_set():
        if alerting.is_set():
            sound_path = os.path.join(os.path.dirname(__file__), CUSTOM_SOUND)
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME)
            else:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)
            time.sleep(ALERT_INTERVAL)
        else:
            time.sleep(1)

def monitor_process():
    global missing_seconds
    while not stop_event.is_set():
        if process_running(PROCESS_NAME):
            missing_seconds = 0
            alerting.clear()
        else:
            missing_seconds += 1
            if missing_seconds >= MISSING_THRESHOLD:
                alerting.set()
        time.sleep(1)

def create_image():
    img = Image.new('RGB', (64, 64), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((16, 16, 48, 48), fill="red")
    return img

def on_exit(icon):
    stop_event.set()
    icon.stop()

def main():
    icon = Icon("Citrix Monitor")
    icon.icon = create_image()
    icon.menu = Menu(MenuItem("Выход", lambda _: on_exit(icon)))

    threading.Thread(target=alert_loop, daemon=True).start()
    threading.Thread(target=monitor_process, daemon=True).start()

    icon.run()

if __name__ == "__main__":
    main()
