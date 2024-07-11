import time
import threading
from pypresence import Presence
from pystray import MenuItem as item, Icon, Menu
from PIL import Image
import irsdk

interval = 10
stop_event = threading.Event()

# iRacing SDK
irsdk_obj = irsdk.IRSDK()
irsdk_obj.startup()

# Discord RPC setup
client_id = '1260920089486692413'
RPC = Presence(client_id)
RPC.connect()

# States and flags
def get_session_state(state_code):
    states = {
        0: "Idle",
        1: "Getting in car",
        2: "Warmup",
        3: "Parade Laps",
        4: "Racing",
        5: "Checkered Flag",
        6: "Cooldown"
    }
    return states.get(state_code, "Unknown")

def get_session_flags(flag_code):
    flags = {
        0: "Green Flag",
        1: "Yellow Flag",
        2: "Red Flag"
    }
    return flags.get(flag_code, "Green Flag") # Default to Green Flag if unknown

# Updating the RPC
def update_presence():
    while not stop_event.is_set():
        try:
            if irsdk_obj.is_initialized and irsdk_obj.is_connected:
                state_code = irsdk_obj['SessionState']
                state = get_session_state(state_code)
                lap_num = irsdk_obj['Lap']
                total_laps = irsdk_obj['SessionLaps']
                position = irsdk_obj['Position'] or "N/A"
                flags_code = int(irsdk_obj['SessionFlags'])
                flags = get_session_flags(flags_code)

                RPC.update(
                    state=f"{position} | {lap_num} of {total_laps} | {flags}",
                    details=state,
                    large_image="iracing",
                    large_text="iRacing"
                )
            else: # if iracing is not running, will display idle
                RPC.update(
                    details="Idle",
                    large_image="iracing",
                    large_text="iRacing"
                )
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

def set_interval(new_interval):
    global interval
    interval = new_interval

icon = Icon("iRacingRP", Image.open("main.ico"), "iRacing Discord Rich Presence")
icon.menu = Menu(
    item('Update intervals', Menu(
        item('1 second', lambda: set_interval(1)),
        item('5 seconds', lambda: set_interval(5)),
        item('10 seconds', lambda: set_interval(10)),
        item('15 seconds', lambda: set_interval(15))
    )),
    item('Quit', on_quit)
)

# Threads
presence_thread = threading.Thread(target=update_presence)
presence_thread.daemon = True
presence_thread.start()
status_thread = threading.Thread(target=iracing_status_check)
status_thread.daemon = True
status_thread.start()

# Run
icon.run()
