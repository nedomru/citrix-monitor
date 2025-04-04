import time
import threading
import psutil
import winsound
import os
from pystray import Icon, MenuItem, Menu
from PIL import Image

PROCESS_NAME = "Citrix.DesktopViewer.App.exe"
MISSING_THRESHOLD = 180  # секунд
ALERT_INTERVAL = 5       # секунд
CHECK_INTERVAL = 0.3     # 300 мс (для мгновенной реакции)
CUSTOM_SOUND = "sounds/alert.wav"
ICON_GREEN = "icons/green.png"
ICON_RED = "icons/red.png"

stop_event = threading.Event()
alerting = threading.Event()
missing_seconds = 0

def load_icon(path):
    try:
        return Image.open(os.path.join(os.path.dirname(__file__), path))
    except Exception as e:
        print(f"Ошибка загрузки иконки {path}: {e}")
        return None

def process_running(name):
    """Проверяет, запущен ли процесс"""
    return any(proc.info['name'] == name for proc in psutil.process_iter(['name']))

def alert_loop():
    """Проигрывает звук, если процесс отсутствует более 3 минут"""
    while not stop_event.is_set():
        if alerting.is_set():
            sound_path = os.path.join(os.path.dirname(__file__), CUSTOM_SOUND)
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
            time.sleep(ALERT_INTERVAL)
        else:
            time.sleep(0.1)


def monitor_process(icon):
    """Мониторинг процесса с мгновенной реакцией"""
    global missing_seconds
    last_check_time = 0
    last_status = True  # Считаем, что процесс есть в начале

    if int(missing_seconds) >= MISSING_THRESHOLD:
        alerting.set()

    while not stop_event.is_set():
        now = time.time()
        if now - last_check_time >= CHECK_INTERVAL:
            current_status = process_running(PROCESS_NAME)
            last_check_time = now

            if current_status:
                if not last_status:
                    icon.icon = load_icon(ICON_GREEN)
                missing_seconds = 0
                alerting.clear()
            else:
                if last_status:
                    icon.icon = load_icon(ICON_RED)
                missing_seconds += CHECK_INTERVAL
                if missing_seconds >= MISSING_THRESHOLD:
                    alerting.set()

            last_status = current_status

        time.sleep(0.05)  # Микропауза, чтобы не грузить CPU

def on_exit(icon):
    """Закрытие программы"""
    stop_event.set()
    icon.stop()

def main():
    icon = Icon("Мониторинг Цитрикса")
    icon.icon = load_icon(ICON_GREEN)
    icon.menu = Menu(MenuItem("Выход", lambda _: on_exit(icon)))

    threading.Thread(target=alert_loop, daemon=True).start()
    threading.Thread(target=monitor_process, args=(icon,), daemon=True).start()

    icon.run()

if __name__ == "__main__":
    main()
