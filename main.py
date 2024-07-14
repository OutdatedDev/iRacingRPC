import time
import threading
from pypresence import Presence
from pystray import MenuItem as item, Icon, Menu
from PIL import Image
import tkinter as tk
import json
import irsdk

# Settings
with open("settings.json", "r") as json_file:
    settings = json.load(json_file)
interval = settings.get("updateInterval", 10)
display_idle = settings.get("displayIdle", True)
display_github = settings.get("displayGithub", True)
stop_event = threading.Event()

# iRacing SDK
irsdk_obj = irsdk.IRSDK()
irsdk_obj.startup()

# Discord RPC setup
client_id = '1260920089486692413' # Don't change this unless you have your own application set up
RPC = Presence(client_id)
RPC.connect()

# Updating the RPC
def update_presence():
    while not stop_event.is_set():
        try:
            if irsdk_obj.is_initialized and irsdk_obj.is_connected:
                state = irsdk_obj['WeekendInfo']['EventType']
                lap_num = irsdk_obj['Lap']
                car_idx = irsdk_obj['DriverInfo']['DriverCarIdx']
                carname = irsdk_obj['DriverInfo']['Drivers'][car_idx]['CarScreenNameShort']
                
                session_num = irsdk_obj['SessionNum']
                session_info = irsdk_obj['SessionInfo']['Sessions'][session_num]
                sessiontype = session_info['SessionType']
                total_laps = session_info['SessionLaps']
                if total_laps in ["unlimited", None, "None", 0]:
                    total_laps = None
                elapsed_time = irsdk_obj['SessionTime']
                total_time = irsdk_obj['SessionTimeRemain']
                position = irsdk_obj['PlayerCarPosition'] or "--"
                track = irsdk_obj['WeekendInfo']['TrackDisplayName']
                
                if total_laps is None:
                    if total_time in [None, "None", 604800] or state in ["Test", "Practice"]:
                        elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
                        statetext = f"{elapsed_time} | {lap_num} laps | {carname}"
                    else:
                        elapsed_time = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
                        total_time = time.strftime('%H:%M:%S', time.gmtime(total_time))
                        statetext = f"P{position} | {elapsed_time} of {total_time} | {carname}"
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
                    large_text=largetexttext
                )
            elif display_idle:
                RPC.update(
                     details="Idle",
                    large_image="iracing",
                    large_text=largetexttext,
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
def on_quit(icon, item):
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
        settings.geometry("300x200")
        settings.resizable(False, False)
        
        interval_label = tk.Label(settings, text="Update interval (seconds):")
        interval_label.pack()
        interval_entry = tk.Entry(settings)
        interval_entry.insert(0, interval)
        interval_entry.pack()

        display_idle_var = tk.BooleanVar(value=display_idle)
        display_github_var = tk.BooleanVar(value=display_github)

        display_idle_checkbutton = tk.Checkbutton(settings, text="Display even when idle", variable=display_idle_var)
        display_idle_checkbutton.pack()

        display_github_checkbutton = tk.Checkbutton(settings, text="Display GitHub Link", variable=display_github_var)
        display_github_checkbutton.pack()

        def save_settings():
            global interval, display_idle, display_github
            interval = int(interval_entry.get())
            display_idle = display_idle_var.get()
            display_github = display_github_var.get()

        save_button = tk.Button(settings, text="Save", command=save_settings)
        save_button.pack()

        settings.mainloop()

    threading.Thread(target=settings_thread).start()

icon = Icon("iRacingRP", Image.open("main.ico"), "iRacing Discord Rich Presence")
menu_items = [
    item('Settings', lambda: settings_window()),
    item('Quit', on_quit)
]

icon.menu = Menu(*menu_items)

# Threads
presence_thread = threading.Thread(target=update_presence)
presence_thread.daemon = True
presence_thread.start()
status_thread = threading.Thread(target=iracing_status_check)
status_thread.daemon = True
status_thread.start()

# Run
print("iRacing Discord Rich Presence is running")
icon.run()
