import time
import threading
from pypresence import Presence
from pystray import MenuItem as item, Icon, Menu
from PIL import Image
import tkinter as tk
from notifypy import Notify
from tkinter import ttk
import json
import irsdk

# Initialize default settings
interval = 1
display_idle = True
display_github = True

# Settings
try:
    settings_file = "settings.json"
    with open(settings_file, "r") as json_file:
        settings = json.load(json_file)
    interval = settings.get("updateInterval", interval)
    display_idle = settings.get("displayIdle", display_idle)
    display_github = settings.get("displayGithub", display_github)
except FileNotFoundError:  # create new settings.json
    with open(settings_file, "w") as json_file:
        settings = {
            "updateInterval": interval,
            "displayIdle": display_idle,
            "displayGithub": display_github,
        }
        json.dump(settings, json_file, indent=4)
        print(
            "Settings file not found, creating new settings file with default settings."
        )
except Exception as e:
    print(f"Error loading settings: {e}, resorting to default settings")

stop_event = threading.Event()

# iRacing SDK
irsdk_obj = irsdk.IRSDK()
irsdk_obj.startup()

# Discord RPC setup
client_id = "1260920089486692413"  # Don't change this unless you have your own application set up
RPC = Presence(client_id)
RPC.connect()

initial_total_time = None


# Updating the RPC
def update_presence():
    global initial_total_time

    while not stop_event.is_set():
        try:
            if irsdk_obj.is_initialized and irsdk_obj.is_connected:
                state = irsdk_obj["WeekendInfo"]["EventType"]
                lap_num = irsdk_obj["Lap"]
                car_idx = irsdk_obj["DriverInfo"]["DriverCarIdx"]
                carname = irsdk_obj["DriverInfo"]["Drivers"][car_idx][
                    "CarScreenNameShort"
                ]
                session_num = irsdk_obj["SessionNum"]
                session_info = irsdk_obj["SessionInfo"]["Sessions"][session_num]
                sessiontype = session_info["SessionType"]
                total_laps = session_info["SessionLaps"]
                if total_laps in ["unlimited", None, "None", 0]:
                    total_laps = None
                elapsed_time = irsdk_obj["SessionTime"]
                total_time = irsdk_obj["SessionTimeRemain"]

                if total_time:
                    initial_total_time = total_time + elapsed_time

                display_total_time = (
                    initial_total_time if initial_total_time else total_time
                )
                position = irsdk_obj["PlayerCarPosition"] or "--"
                track = irsdk_obj["WeekendInfo"]["TrackDisplayName"]

                if total_laps is None:
                    if total_time in [None, "None", 604800] or state in [
                        "Test",
                        "Practice",
                    ]:
                        elapsed_time = time.strftime(
                            "%H:%M:%S", time.gmtime(elapsed_time)
                        )
                        statetext = f"{elapsed_time} | {lap_num} laps | {carname}"
                    else:
                        elapsed_time = time.strftime(
                            "%H:%M:%S", time.gmtime(elapsed_time)
                        )
                        display_total_time = time.strftime(
                            "%H:%M:%S", time.gmtime(display_total_time)
                        )
                        statetext = f"P{position} | {elapsed_time} of {display_total_time} | {carname}"
                else:
                    statetext = f"P{position} | {lap_num} of {total_laps} | {carname}"

                if display_github:
                    largetexttext = "https://github.com/OutdatedDev/iRacingRPC"
                else:
                    largetexttext = "iRacing"

                if sessiontype == state:
                    details = f"{state} | {track}"
                else:
                    details = f"{state} - {sessiontype} | {track}"

                RPC.update(
                    state=statetext,
                    details=details,
                    large_image="iracing",
                    large_text=largetexttext,
                )
            elif display_idle:
                if display_github:
                    largetexttext = "https://github.com/OutdatedDev/iRacingRPC"
                else:
                    largetexttext = "iRacing"
                RPC.update(
                    details="Idle",
                    large_image="iracing",
                    buttons=[
                        {
                            "label": "View on GitHub",
                            "url": "https://github.com/Outdateddev/iRacingRPC",
                        }
                    ],
                )

            else:
                RPC.clear()
        except KeyError as e:
            print(f"Data not available from iRacing: {e}")
        except Exception as e:
            print(f"Error updating presence: {e}")

        stop_event.wait(interval)


# iRacing Status check
def iracing_status_check():
    while not stop_event.is_set():
        if not irsdk_obj.is_initialized or not irsdk_obj.is_connected:
            irsdk_obj.shutdown()
            irsdk_obj.startup()
        time.sleep(5)


# Tray Icons
def on_quit(icon):
    stop_event.set()
    RPC.close()
    icon.stop()
    print("RPC Closing")


def set_interval(new_interval):
    global interval
    interval = new_interval


def settings_window():
    def settings_thread():
        settings = tk.Tk()
        settings.title("iRacing RPC Settings")
        settings.iconbitmap("main.ico")
        settings.geometry("400x300")
        settings.resizable(False, False)

        # Styling
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("TCheckbutton", font=("Segoe UI", 10))

        settings_frame = ttk.Frame(settings, padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        interval_label = ttk.Label(settings_frame, text="Update interval (seconds):")
        interval_label.pack(pady=5)
        interval_entry = ttk.Entry(settings_frame)
        interval_entry.insert(0, interval)
        interval_entry.pack(pady=5)

        display_idle_var = tk.BooleanVar(value=display_idle)
        display_github_var = tk.BooleanVar(value=display_github)

        display_idle_checkbutton = ttk.Checkbutton(
            settings_frame, text="Display even when idle", variable=display_idle_var
        )
        display_idle_checkbutton.pack(pady=5)

        display_github_checkbutton = ttk.Checkbutton(
            settings_frame, text="Display GitHub Link", variable=display_github_var
        )
        display_github_checkbutton.pack(pady=5)

        def save_settings():
            try:
                global interval, display_idle, display_github
                interval = int(interval_entry.get())
                display_idle = display_idle_var.get()
                display_github = display_github_var.get()
                new_settings = {
                    "updateInterval": interval,
                    "displayIdle": display_idle,
                    "displayGithub": display_github,
                }
                with open(settings_file, "w") as json_file:
                    json.dump(new_settings, json_file, indent=4)
                tk.messagebox.showinfo("Success", "Settings saved successfully!")
            except Exception as e:
                tk.messagebox.showerror("Error", f"Error saving settings: {e}")

        save_button = ttk.Button(settings_frame, text="Save", command=save_settings)
        save_button.pack(pady=20)
        settings.mainloop()

    threading.Thread(target=settings_thread).start()


icon = Icon("iRacingRP", Image.open("main.ico"), "iRacing Discord Rich Presence")
menu_items = [item("Settings", lambda: settings_window()), item("Quit", on_quit)]

icon.menu = Menu(*menu_items)

# Threads
presence_thread = threading.Thread(target=update_presence)
presence_thread.daemon = True
presence_thread.start()
status_thread = threading.Thread(target=iracing_status_check)
status_thread.daemon = True
status_thread.start()

# Run
notification = Notify()
notification.title = "iRacing Rich Presence"
notification.message = "Running in system tray, right click to access settings."
notification.icon = "assets/logo.png"

notification.send()
print("iRacing Discord Rich Presence is running")
icon.run()