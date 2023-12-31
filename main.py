import configparser
import json
import os
from ctypes import create_unicode_buffer, windll
from tkinter import filedialog
from typing import Optional

import cv2
import keyboard
import numpy
import requests

VERSION = "v0.0.2"

# try to get the latest version from the repo
try:
    response = requests.get(
        "https://api.github.com/repos/DannyAlas/vid-scoring/releases/latest"
    )
    release = response.json()
    latest_version = release["tag_name"]
    if latest_version != VERSION:
        print(f"\nNewer version available: {latest_version}")
        print(f"Download here: {release['html_url']}\n")
except Exception as e:
    pass


def getForegroundWindowTitle() -> Optional[str]:
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)

    # 1-liner alternative: return buf.value if buf.value else None
    if buf.value:
        return buf.value
    else:
        return None


file_path = input("\nEnter the path to the video file: ")
file_path = file_path.replace('"', "").strip()
file_name = os.path.basename(file_path)

SAVE_DIR = filedialog.askdirectory()


class Timestamps(list):
    # extends list but implements custom append and pop methods depending on scoring type
    def __init__(self, scoring_type, save_dir, file_path, csv_file):
        self.scoring_type = scoring_type
        self.intermediary = []
        self.save_dir = save_dir
        self.file_path = file_path
        self.csv_file = csv_file
        if csv_file:
            if os.path.exists(csv_file):
                self.load()

    def load(self):
        if self.scoring_type == "onset/offset":
            # assert that there are two columns of equivalent length
            with open(self.csv_file, "r") as f:
                lines = f.readlines()
                lines = [tuple(line.strip().split(",")) for line in lines]
                assert len(lines[0]) == 2
                assert len(lines[0]) == len(lines[1])
                self.extend(lines[1:])
        else:
            with open(self.csv_file, "r") as f:
                lines = f.readlines()
                lines = [line.strip().split(",") for line in lines]
                assert len(lines[0]) == 1
                self.extend(lines[1:])
        self.update_line()

    def append(self, val):
        if self.scoring_type == "onset/offset":
            if len(self.intermediary) == 0:
                self.intermediary.append(val)
                super().append(tuple(self.intermediary))
            elif len(self.intermediary) == 1:
                self.intermediary.append(val)
                super().pop()
                super().append(tuple(self.intermediary))
                self.intermediary = []
        else:
            super().append(val)
            super().sort()
        self.update_line()
        self.save()

    def pop(self):
        if self.scoring_type == "onset/offset":
            if len(self.intermediary) == 0:
                # the last item is a tuple, we only want to pop the last item in the tuple
                self.intermediary.append(self[-1][0])
                super().pop()
                super().append(
                    tuple(
                        self.intermediary,
                    )
                )
            elif len(self.intermediary) == 1:
                self.intermediary.pop()
                super().pop()
        else:
            super().pop()
            super().sort()
        self.update_line()
        self.save()

    def update_line(self):
        os.system("cls" if os.name == "nt" else "clear")
        print(self)

    def __repr__(self):
        return super().__repr__()

    def __str__(self):
        return super().__str__()

    def as_array(self):
        # the first value is either frame or timestamp
        if save_frame_or_timestamp == "frame":
            if self.scoring_type == "onset/offset":
                if len(self[-1]) == 1:
                    self[-1] = (self[-1][0], self[-1][0])
                if not self[0] == ("onset frame", "offset frame"):
                    self.insert(0, ("onset frame", "offset frame"))
            else:
                self.insert(0, ("frame"))
        elif save_frame_or_timestamp == "timestamp":
            if self.scoring_type == "onset/offset":
                if len(self[-1]) == 1:
                    self[-1] = (self[-1][0], self[-1][0])
                if not self[0] == ("onset timestamp", "offset timestamp"):
                    self.insert(0, ("onset timestamp", "offset timestamp"))
            else:
                self.insert(0, ("timestamp"))
        return self

    def save(self):
        if self != []:
            # if temp.csv exists, append to it
            csv_file_name = os.path.join(
                self.save_dir,
                os.path.splitext(os.path.basename(self.file_path))[0] + ".csv",
            )
            numpy.savetxt(
                os.path.join(SAVE_DIR, csv_file_name),
                self.as_array(),
                delimiter=",",
                fmt="%s",
            )


if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

if os.path.exists(
    os.path.join(SAVE_DIR, os.path.splitext(os.path.basename(file_path))[0] + ".csv")
):
    csv_file_name = os.path.join(
        SAVE_DIR, os.path.splitext(os.path.basename(file_path))[0] + ".csv"
    )
    try:
        timestamps = Timestamps("onset/offset", SAVE_DIR, file_path, csv_file_name)
    except Exception as e:
        input(
            f"WARNING - found existing csv file but could not load it. OVERWRITE the file? (y/n)"
        )
        if input == "y":
            timestamps = Timestamps("onset/offset", SAVE_DIR, file_path, csv_file_name)
        else:
            csv_file_name = os.path.join(
                SAVE_DIR, os.path.splitext(os.path.basename(file_path))[0] + ".csv"
            )
            n = 1
            while os.path.exists(csv_file_name):
                csv_file_name = os.path.join(
                    SAVE_DIR,
                    os.path.splitext(os.path.basename(file_path))[0]
                    + f"({n})"
                    + ".csv",
                )
                n += 1

        timestamps = Timestamps("onset/offset", SAVE_DIR, file_path, csv_file_name)
else:
    timestamps = Timestamps("onset/offset", SAVE_DIR, file_path, None)

######### SETTINGS #########
scoring_type = "onset/offset"
save_frame_or_timestamp = "frame"

text_color = 255, 0, 0
show_current_frame_number = True
show_current_timestamp = False
show_fps = False

playback_settings = {
    "seek_small": 1,
    "seek_medium": 100,
    "seek_large": 1000,
    "playback_speed_modulator": 5,
}

key_bindings = {
    "exit": "q",
    "help": "h",
    "save timestamp": "s",
    "show stats": "t",
    "undo last timestamp save": "ctrl+z",
    "pause": "space",
    "seek forward small frames": "d",
    "seek back small frames": "a",
    "seek forward medium frames": "shift+D",
    "seek back medium frames": "shift+A",
    "seek forward large frames": "p",
    "seek back large frames": "o",
    "seek to first frame": "1",
    "seek to last frame": "0",
    "increase playback speed": "x",
    "decrease playback speed": "z",
}

try:
    settings_file = os.path.join(os.path.dirname(__file__), "settings.ini")
    if not os.path.exists(settings_file):
        raise FileNotFoundError

    config = configparser.ConfigParser()
    config.read(settings_file)

    scoring_type = config["scoring"]["scoring_type"]
    save_frame_or_timestamp = config["scoring"]["save_frame_or_timestamp"]
    text_color = [int(x) for x in config["scoring"]["text_color"].split(",")]
    show_current_frame_number = config.getboolean(
        "scoring", "show_current_frame_number"
    )
    show_current_timestamp = config.getboolean("scoring", "show_current_timestamp")
    show_fps = config.getboolean("scoring", "show_fps")
    playback_settings = {
        "seek_small": int(config["playback_settings"]["seek_small"].strip()),
        "seek_medium": int(config["playback_settings"]["seek_medium"].strip()),
        "seek_large": int(config["playback_settings"]["seek_large"].strip()),
        "playback_speed_modulator": int(
            config["playback_settings"]["playback_speed_modulator"].strip()
        ),
    }
    key_bindings = {
        "exit": config["key_bindings"]["exit"].strip(),
        "help": config["key_bindings"]["help"].strip(),
        "save timestamp": config["key_bindings"]["save_timestamp"].strip(),
        "show stats": config["key_bindings"]["show_stats"].strip(),
        "undo last timestamp save": config["key_bindings"][
            "undo_last_timestamp_save"
        ].strip(),
        "pause": config["key_bindings"]["pause"].strip(),
        "seek forward small frames": config["key_bindings"][
            "seek_forward_small_frames"
        ].strip(),
        "seek back small frames": config["key_bindings"][
            "seek_back_small_frames"
        ].strip(),
        "seek forward medium frames": config["key_bindings"][
            "seek_forward_medium_frames"
        ].strip(),
        "seek back medium frames": config["key_bindings"][
            "seek_back_medium_frames"
        ].strip(),
        "seek forward large frames": config["key_bindings"][
            "seek_forward_large_frames"
        ].strip(),
        "seek back large frames": config["key_bindings"][
            "seek_back_large_frames"
        ].strip(),
        "seek to first frame": config["key_bindings"]["seek_to_first_frame"].strip(),
        "seek to last frame": config["key_bindings"]["seek_to_last_frame"].strip(),
        "increase playback speed": config["key_bindings"][
            "increase_playback_speed"
        ].strip(),
        "decrease playback speed": config["key_bindings"][
            "decrease_playback_speed"
        ].strip(),
    }
except Exception as e:
    print("Error reading settings file: ", e)
    print("\n\nUsing default settings\n\n")

if not os.path.exists(file_path):
    raise FileNotFoundError("File not found")
try:
    # find a .sub in the same directory as the video file
    subs_path = [
        os.path.join(os.path.dirname(file_path), f)
        for f in os.listdir(os.path.dirname(file_path))
        if os.path.splitext(f)[1] == ".sub"
    ][0]
    subtitles = subs_path.replace('"', "")
except IndexError:
    # if there is no .sub, ask for the path
    subs_path = input("[OPTIONAL] Enter the path to the .sub file: ")
    if not os.path.exists(subs_path):
        print("File not found, Using video timestamps instead")
        # subtitles is the ms of each frame, video is 30 fps
        subtitles = None

intro = f"""

                                                                                          
██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗            
██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║██╔════╝            
██║   ██║██║██║  ██║█████╗  ██║   ██║    ███████╗██║     ██║   ██║██████╔╝██║██╔██╗ ██║██║  ███╗           
╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ╚════██║██║     ██║   ██║██╔══██╗██║██║╚██╗██║██║   ██║           
 ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ███████║╚██████╗╚██████╔╝██║  ██║██║██║ ╚████║╚██████╔╝           
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝            



#############################################################################################################
#############################################################################################################
                                    PRESS {key_bindings["help"]} FOR HELP    
#############################################################################################################
#############################################################################################################



"""

help_text = f"""
################
SETTINGS: modify in {os.path.join(os.path.dirname(__file__), "settings.json")}
################

PLAYBACK SETTINGS:
{json.dumps(playback_settings, indent=4).replace('"', "").replace(",", "").replace("{", "").replace("}", "")}

KEY BINDINGS:
{json.dumps(key_bindings, indent=4).replace('"', "").replace(",", "").replace("{", "").replace("}", "")}

"""

print(intro)

cap = cv2.VideoCapture(file_path)
timestamps.scoring_type = scoring_type
if not subtitles:
    # get the number of frames in the video
    max_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if max_frame == 0:
        print("Error reading video file")
        exit()
    subtitles = [int(i * 1000) for i in range(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))]
else:
    with open(subtitles, "r") as f:
        subtitles = f.read().splitlines()
        subtitles = [s.split("}")[-1] for s in subtitles]


fps = cap.get(cv2.CAP_PROP_FPS)
saved_keys = []
frame_count = 0
max_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
frozen = False
paused = False

last_key = None
current_key = None
key_iter = 0
key_rep_thresh = 10


def update_line(line):
    # clear
    os.system("cls" if os.name == "nt" else "clear")
    print(line)


def imshow(frame):
    cv2.imshow(f"video-scoring: {file_name}", frame)


def show_current_frame():
    global cap
    global frame
    global frame_count
    global subtitles
    global max_frame
    global paused
    global frozen
    global fps
    global timestamps
    global sub
    frame_count = int(frame_count)
    if frame_count >= max_frame:
        frame_count = max_frame - 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
    if paused:
        frame = cap.read()[1]
        try:
            sub = subtitles[int(frame_count)]
        except IndexError:
            sub = max_frame
    else:
        frame = cap.read()[1]
    if frame is None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = cap.read()[1]
    if show_current_timestamp:
        cv2.putText(
            frame,
            "ts: " + str(sub),
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            tuple(text_color),
            2,
        )

    if show_current_frame_number == True:
        cv2.putText(
            frame,
            "f: " + str(frame_count),
            (frame.shape[1] - 150, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            tuple(text_color),
            2,
        )
    imshow(frame)
    return frame


def get_keypress_name():
    """Will return the name of the current key or an empty string. If will account for repitions of the same key"""
    global last_key
    global current_key
    global key_iter
    global key_rep_thresh
    current_key = keyboard.get_hotkey_name()
    if current_key == last_key:
        if (
            key_iter >= key_rep_thresh
            and getForegroundWindowTitle() == f"video-scoring: {file_name}"
        ):
            return current_key
        if (
            key_iter <= key_rep_thresh
            and getForegroundWindowTitle() == f"video-scoring: {file_name}"
        ):
            key_iter += 1
            return ""
    elif getForegroundWindowTitle() == f"video-scoring: {file_name}":
        key_iter = 0
        last_key = current_key
        return current_key
    else:
        return ""


while cap.isOpened():
    frame_count = int(frame_count)
    try:
        sub = subtitles[frame_count]
    except Exception as e:
        sub = subtitles[-1]

    key = cv2.waitKey(int(1000 / fps))
    # frame = show_current_frame()
    if key:
        keypress = get_keypress_name()
    if keypress == key_bindings["help"]:
        update_line(help_text)
    if keypress == key_bindings["exit"]:
        break
    elif keypress == key_bindings["save timestamp"]:
        frozen = not frozen
        if save_frame_or_timestamp == "frame":
            timestamps.append(frame_count)
        elif save_frame_or_timestamp == "timestamp":
            timestamps.append(sub)
    elif keypress == key_bindings["show stats"]:
        update_line(
            f"""
        fps: {fps}
        max_frame: {max_frame}
        curent_frame: {frame_count}
        timestamp: {sub}
        timestamps: {timestamps}
        """
        )
    # modify the playback speed
    elif keypress == key_bindings["increase playback speed"]:
        fps += playback_settings["playback_speed_modulator"]
    elif keypress == key_bindings["decrease playback speed"]:
        if fps > playback_settings["playback_speed_modulator"]:
            fps -= playback_settings["playback_speed_modulator"]
    # seek forward or backward with z and x
    elif keypress == key_bindings["seek forward small frames"]:
        frame_count += playback_settings["seek_small"]
        if frame_count > max_frame:
            frame_count = max_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek back small frames"]:
        frame_count -= playback_settings["seek_small"]
        if frame_count < 0:
            frame_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek back medium frames"]:
        frame_count -= playback_settings["seek_medium"]
        if frame_count < 0:
            frame_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek forward medium frames"]:
        frame_count += 100
        if frame_count > max_frame:
            frame_count = max_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek forward large frames"]:
        frame_count += playback_settings["seek_large"]
        if frame_count > max_frame:
            frame_count = max_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek back large frames"]:
        frame_count -= playback_settings["seek_large"]
        if frame_count < 0:
            frame_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["pause"]:
        paused = not paused
        if paused:
            last_frame = frame
        else:
            frame = last_frame
            imshow(frame)
    elif keypress == key_bindings["undo last timestamp save"]:
        try:
            timestamps.pop()
            update_line(timestamps)
        except IndexError:
            pass
    elif keypress == key_bindings["seek to first frame"]:
        frame_count = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    elif keypress == key_bindings["seek to last frame"]:
        frame_count = max_frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
        frame = show_current_frame()
    if not paused:
        frame = show_current_frame()
        if frame_count < max_frame - 1:
            frame_count += 1

timestamps.save()
