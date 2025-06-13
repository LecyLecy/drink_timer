import time
import threading
import subprocess
import sys
import os
import tkinter as tk
from tkinter import Label, Entry, Button, Frame
import pystray
from pystray import MenuItem as Item
from PIL import Image, ImageDraw
import keyboard
import pygetwindow as gw
import win32gui
import win32con
import mouse
import ctypes
import win32api
import win32process
import pygame

# === CONFIG ===
DEFAULT_MINUTES = 30
SPOTIFY_VOL_LOW = 2
SPOTIFY_VOL_HIGH = 70
SOUND_FILE = "C:\\Users\\Ideapad Gaming 15\\Desktop\\mixkit-alarm-clock-beep-988.wav"
SOUND_VOLUME_VIEW_PATH = "C:\\Users\\Ideapad Gaming 15\\Desktop\\SoundVolumeView.exe"

# === STATE ===
timer_seconds = int(DEFAULT_MINUTES * 60)
timer_running = True
custom_minutes = DEFAULT_MINUTES
mode = "collapsed"  # collapsed, expanded, input, alarm
timer_window = None
tray_icon = None
last_window = None

root = tk.Tk()
root.withdraw()

# === NEW: Toggle always-on-top for currently focused window
def toggle_foreground_window_always_on_top():
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        # Check if already topmost
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        is_topmost = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOPMOST

        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_NOTOPMOST if is_topmost else win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )

# === FUNCTIONS ===
def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m:02}:{s:02}"

def play_sound():
    try:
        pygame.mixer.music.load(SOUND_FILE)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"[Sound Error] {e}")

def reset_timer():
    global timer_seconds, timer_running
    timer_seconds = int(custom_minutes * 60)
    timer_running = True
    show_collapsed_timer()

def countdown():
    global timer_seconds, timer_running
    while True:
        if timer_running:
            time.sleep(1)
            timer_seconds -= 1
            if timer_seconds <= 0:
                timer_running = False
                show_alarm()

def collapse_from_focus():
    if mode == "expanded":
        show_collapsed_timer()

def show_collapsed_timer():
    global timer_window, mode
    mode = "collapsed"

    if timer_window:
        try:
            timer_window.destroy()
        except:
            pass

    timer_window = tk.Toplevel(root)
    timer_window.overrideredirect(True)
    timer_window.attributes('-topmost', True)
    timer_window.configure(bg="#202020")
    screen_height = timer_window.winfo_screenheight()
    timer_window.geometry(f"+0+{screen_height - 112}")

    label = tk.Label(timer_window, text=format_time(timer_seconds), fg="white", bg="#202020", font=("Segoe UI", 12))
    label.pack(padx=10, pady=5)
    label.bind("<Button-1>", lambda e: show_expanded_timer())

    def update():
        if mode == "collapsed":
            label.config(text=format_time(timer_seconds))
            timer_window.after(1000, update)
    update()

    timer_window.bind("<FocusOut>", lambda e: collapse_from_focus())

def show_expanded_timer():
    global timer_window, mode
    mode = "expanded"
    if timer_window:
        try:
            timer_window.destroy()
        except:
            pass

    timer_window = tk.Toplevel(root)
    timer_window.overrideredirect(True)
    timer_window.attributes("-topmost", True)
    screen_height = timer_window.winfo_screenheight()
    timer_window.geometry(f"+0+{screen_height - 112}")
    timer_window.configure(bg="#202020")

    header = Frame(timer_window, bg="#404040", height=20)
    header.pack(fill="x")

    def start_move(event):
        timer_window.x = event.x
        timer_window.y = event.y

    def do_move(event):
        x = timer_window.winfo_pointerx() - timer_window.x
        y = timer_window.winfo_pointery() - timer_window.y
        timer_window.geometry(f"+{x}+{y}")

    header.bind("<ButtonPress-1>", start_move)
    header.bind("<B1-Motion>", do_move)

    frame = Frame(timer_window, bg="#202020")
    frame.pack(expand=True, fill="both", padx=8, pady=8)

    lbl = Label(frame, text=format_time(timer_seconds), fg="white", bg="#202020", font=("Segoe UI", 14))
    lbl.pack(side="left", padx=10)

    Button(frame, text="C", command=show_input_box, width=2).pack(side="left")
    Button(frame, text="R", command=reset_position, width=2).pack(side="left")

    def update():
        if mode == "expanded":
            lbl.config(text=format_time(timer_seconds))
            timer_window.after(1000, update)
    update()

    timer_window.bind("<FocusOut>", lambda e: show_collapsed_timer())

def monitor_outside_clicks():
    def on_mouse_event(event):
        global timer_window, mode
        if mode != "expanded" or not timer_window:
            return
        if not hasattr(event, "event_type") or event.event_type != "down":
            return
        try:
            root.after(200, check_click_position)
        except Exception as e:
            print("Click monitor error:", e)

    def check_click_position():
        global timer_window
        try:
            if not timer_window or not timer_window.winfo_exists():
                return

            x, y = mouse.get_position()
            win_x = timer_window.winfo_rootx()
            win_y = timer_window.winfo_rooty()
            win_w = timer_window.winfo_width()
            win_h = timer_window.winfo_height()

            if not (win_x <= x <= win_x + win_w and win_y <= y <= win_y + win_h):
                show_collapsed_timer()
        except tk.TclError as e:
            print("Window check skipped:", e)

    mouse.hook(on_mouse_event)

def reset_position():
    show_collapsed_timer()

def show_input_box():
    global mode
    mode = "input"
    if timer_window:
        try:
            timer_window.destroy()
        except:
            pass

    input_win = tk.Toplevel(root)
    input_win.overrideredirect(True)
    input_win.attributes('-topmost', True)
    screen_height = input_win.winfo_screenheight()
    input_win.geometry(f"200x70+0+{screen_height - 112}")
    input_win.configure(bg="#202020")

    entry = Entry(input_win, font=("Segoe UI", 14))
    entry.insert(0, str(custom_minutes))
    entry.pack(padx=10, pady=10)
    entry.focus()

    def apply():
        global custom_minutes, timer_seconds
        try:
            val = float(entry.get())
            if val > 0:
                custom_minutes = val
                timer_seconds = int(val * 60)
        except:
            pass
        input_win.destroy()
        show_collapsed_timer()

    def cancel(event=None):
        input_win.destroy()
        show_collapsed_timer()

    entry.bind("<Return>", lambda e: apply())
    entry.bind("<Escape>", cancel)

def show_alarm():
    global mode, timer_window
    mode = "alarm"
    if timer_window:
        try:
            timer_window.destroy()
        except:
            pass

    timer_window = tk.Toplevel(root)
    timer_window.overrideredirect(True)
    timer_window.attributes("-topmost", True)
    screen_height = timer_window.winfo_screenheight()
    timer_window.geometry(f"120x40+0+{screen_height - 112}")
    timer_window.configure(bg="#202020")

    label = Label(timer_window, text="DRINK!", fg="red", bg="#202020", font=("Segoe UI", 14, "bold"))
    label.pack(padx=10, pady=5)

    threading.Thread(target=alarm_countdown, daemon=True).start()

def alarm_countdown():
    play_sound()
    time.sleep(10)
    pygame.mixer.music.stop()
    reset_timer()

def update_spotify_volume():
    current = getattr(update_spotify_volume, 'state', False)
    vol = SPOTIFY_VOL_HIGH if not current else SPOTIFY_VOL_LOW
    update_spotify_volume.state = not current
    subprocess.Popen([SOUND_VOLUME_VIEW_PATH, '/SetVolume', 'Spotify', str(vol), '/Hide'])

def force_focus(hwnd):
    try:
        fg_win = win32gui.GetForegroundWindow()
        current_thread = win32api.GetCurrentThreadId()
        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        fg_thread = win32process.GetWindowThreadProcessId(fg_win)[0]
        ctypes.windll.user32.AttachThreadInput(fg_thread, target_thread, True)
        ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, True)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        ctypes.windll.user32.AttachThreadInput(fg_thread, target_thread, False)
        ctypes.windll.user32.AttachThreadInput(current_thread, target_thread, False)
    except Exception as e:
        print("Focus workaround failed:", e)

def get_foreground_hwnd():
    return win32gui.GetForegroundWindow()

def toggle_chrome_netflix():
    global last_window
    try:
        chrome_windows = gw.getWindowsWithTitle('Netflix') or gw.getWindowsWithTitle('Chrome')
        if not chrome_windows:
            return

        chrome_win = chrome_windows[0]
        hwnd = chrome_win._hWnd
        is_minimized = chrome_win.isMinimized
        foreground = get_foreground_hwnd()

        if is_minimized:
            force_focus(hwnd)
            time.sleep(0.3)
            keyboard.send('space')
            last_window = foreground
            return

        if hwnd != foreground:
            force_focus(hwnd)
            time.sleep(0.3)
            keyboard.send('space')
            last_window = foreground
            return

        keyboard.send('space')
        time.sleep(0.3)
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        return

    except Exception as e:
        print("Chrome/Netflix toggle failed:", e)

def restart_script():
    python = sys.executable
    os.execl(python, f'"{python}"', f'"{os.path.abspath(sys.argv[0])}"', *sys.argv[1:])

def exit_script():
    if tray_icon:
        tray_icon.stop()
    sys.exit()

def create_image():
    image = Image.new('RGB', (64, 64), (32, 32, 32))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(255, 0, 0))
    return image

def setup_tray():
    global tray_icon
    icon = create_image()
    menu = (
        Item('Restart Script', restart_script),
        Item('Exit', exit_script)
    )
    tray_icon = pystray.Icon("drink_timer", icon, "Drink Timer", menu)
    tray_icon.run()

def setup_hotkeys():
    keyboard.add_hotkey('f3', update_spotify_volume)
    keyboard.add_hotkey('f4', toggle_chrome_netflix)
    keyboard.add_hotkey('alt+2', toggle_foreground_window_always_on_top)  # ⬅️ Added here

# === MAIN ===
if __name__ == "__main__":
    print("Script started")
    pygame.mixer.init()
    threading.Thread(target=countdown, daemon=True).start()
    threading.Thread(target=setup_tray, daemon=True).start()
    setup_hotkeys()
    monitor_outside_clicks()
    show_collapsed_timer()
    root.mainloop()
