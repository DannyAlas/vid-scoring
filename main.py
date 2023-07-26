import configparser
import json
import os
from ctypes import create_unicode_buffer, windll
from tkinter import filedialog
from typing import Optional, Literal, Union, Tuple
import curses
from curses import wrapper
import sys
import cv2
import keyboard
import numpy as np
import requests

VERSION = "v0.0.2"

# GLOBALS
LAST_KEY = None
CURRENT_KEY = None
KEY_ITER = 0
KEY_REP_THRESH = 10

class Settings:

    def __init__(self, settings_path: str, screen):
        self.settings_path = settings_path
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.settings_path):
                self.settings_path = os.path.join(os.path.dirname(__file__), "settings.ini")
                if not os.path.exists(self.settings_path):
                    raise FileNotFoundError
        try:
            if not os.path.exists(self.settings_path):
                raise FileNotFoundError

            config = configparser.ConfigParser()
            config.read(self.settings_path)

            self.scoring_type = config["scoring"]["scoring_type"]
            self.save_frame_or_timestamp = config["scoring"]["save_frame_or_timestamp"]
            self.text_color = [int(x) for x in config["scoring"]["text_color"].split(",")]
            self.show_current_frame_number = config.getboolean(
                "scoring", "show_current_frame_number"
            )
            self.show_current_timestamp = config.getboolean("scoring", "show_current_timestamp")
            self.show_fps = config.getboolean("scoring", "show_fps")

            self.playback_settings = {
                "seek_small": int(config["playback_settings"]["seek_small"].strip()),
                "seek_medium": int(config["playback_settings"]["seek_medium"].strip()),
                "seek_large": int(config["playback_settings"]["seek_large"].strip()),
                "playback_speed_modulator": int(
                    config["playback_settings"]["playback_speed_modulator"].strip()
                ),
            }
            self.key_bindings = {
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
                "increment selected timestamp by seek small": config["key_bindings"][
                    "increment_selected_timestamp_by_seek_small"
                ].strip(),
                "decrement selected timestamp by seek small": config["key_bindings"][
                    "decrement_selected_timestamp_by_seek_small"
                ].strip(),
                "increment selected timestamp by seek medium": config["key_bindings"][
                    "increment_selected_timestamp_by_seek_medium"
                ].strip(),
                "decrement selected timestamp by seek medium": config["key_bindings"][
                    "decrement_selected_timestamp_by_seek_medium"
                ].strip(),
                "increment selected timestamp by seek large": config["key_bindings"][
                    "increment_selected_timestamp_by_seek_large"
                ].strip(),
                "decrement selected timestamp by seek large": config["key_bindings"][
                    "decrement_selected_timestamp_by_seek_large"
                ].strip(),
                "select onset timestamp": config["key_bindings"][
                    "select_onset_timestamp"
                ].strip(),
                "select offset timestamp": config["key_bindings"][
                    "select_offset_timestamp"
                ].strip(),
                "set player to selected timestamp": config["key_bindings"][
                    "set_player_to_selected_timestamp"
                ].strip(),
                "delete selected timestamp": config["key_bindings"][
                    "delete_selected_timestamp"
                ].strip(),
            }
        except Exception as e:
            print("Error reading settings file: ", e)
            print("\n\nUsing default settings\n\n")
            self.load_default_settings()

    def load_default_settings(self):
        self.scoring_type = "onset/offset"
        self.save_frame_or_timestamp = "frame"

        self.text_color = 255, 0, 0
        self.show_current_frame_number = True
        self.show_current_timestamp = False
        self.show_fps = False

        self.playback_settings = {
            "seek_small": 1,
            "seek_medium": 100,
            "seek_large": 1000,
            "playback_speed_modulator": 5,
        }

        self.key_bindings = {
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
            "increment selected timestamp by seek small": "down",
            "decrement selected timestamp by seek small": "up",
            "increment selected timestamp by seek medium": "shift+down",
            "decrement selected timestamp by seek medium": "shift+up",
            "increment selected timestamp by seek large": "ctrl+down",
            "decrement selected timestamp by seek large": "ctrl+up",
            "select onset timestamp": "left",
            "select offset timestamp": "right",
            "set player to selected timestamp": "enter",
            "delete selected timestamp": "delete",
        }

    @property
    def help_text(self):
        return f"""

Modify in {os.path.join(os.path.dirname(__file__), "settings.json")}
################

PLAYBACK SETTINGS:
{json.dumps(self.playback_settings, indent=4).replace('"', "").replace(",", "").replace("{", "").replace("}", "")}

KEY BINDINGS:
{json.dumps(self.key_bindings, indent=4).replace('"', "").replace(",", "").replace("{", "").replace("}", "")}
"""
    
class Timestamps(list):
    # extends list but implements custom append and pop methods depending on scoring type
    def __init__(self, settings: Settings, save_dir, video_file_path,screen):
        self.settings = settings
        self.selected_type = None
        self.intermediary = []
        self.save_dir = save_dir
        self.video_file_path = video_file_path
        self.screen = screen
        self.selection = 0
        self.default_save_path = os.path.join(self.save_dir, os.path.splitext(os.path.basename(self.video_file_path))[0] + ".csv")
        self.save_path = self.default_save_path
        self.load()
        
    def curses_input(self, txt):
        curses.echo()
        self.screen.clear()
        self.screen.addstr(0, 0, txt)
        self.screen.refresh()
        inp = self.screen.getstr(1, 0).decode("utf-8")
        curses.noecho()
        return inp

    def get_new_save_path(self, overwrite=False):
        n = 1
        save_path = self.default_save_path
        while os.path.exists(save_path):
            save_path = os.path.join(
                self.save_dir,
                os.path.splitext(os.path.basename(self.video_file_path))[0]
                + f"({n})"
                + ".csv",
            )
            n += 1
        return save_path

    def load(self):
        """
        Tries to load timestamps from the default save path and sets the save path to the default, if the file does not exist or fails to load, a new save path is generated and nothing is loaded
        """
        if os.path.exists(self.default_save_path):
            try:
                if self.settings.scoring_type == "onset/offset":
                    # assert that there are two columns of equivalent length
                    with open(self.save_path, "r") as f:
                        lines = f.readlines()
                        lines = [tuple(line.strip().split(",")) for line in lines]
                        assert len(lines[0]) == 2
                        assert len(lines[0]) == len(lines[1])
                        self.extend(lines[1:])
                else:
                    with open(self.save_path, "r") as f:
                        lines = f.readlines()
                        lines = [line.strip().split(",") for line in lines]
                        assert len(lines[0]) == 1
                        self.extend(lines[1:])
                self.save_path = self.default_save_path
                self.update_line()
            except:
                self.save_path = self.get_new_save_path()
        else:
            self.save_path = self.get_new_save_path()

    def update_selection(self, amount: int):
        if self.selection + amount < 0:
            self.selection = 0
        elif self.selection + amount > len(self) - 1:
            self.selection = len(self) - 1
        else:
            self.selection += amount
        self.update_line()

    def append(self, val):
        if self.settings.scoring_type == "onset/offset":
            if len(self.intermediary) == 0:
                self.intermediary.append(val)
                super().append(tuple(self.intermediary))
            elif len(self.intermediary) == 1:
                self.intermediary.append(val)
                self.intermediary = [float(x) for x in self.intermediary]
                self.intermediary.sort()
                super().pop()
                super().append(tuple(self.intermediary))
                self.intermediary = []
        else:
            super().append(val)
            super().sort()
        self.selection = len(self) - 1
        self.update_line()
        self.save()

    def pop(self):
        if len(self) <= 1:
            return
        if self.settings.scoring_type == "onset/offset":
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
        self.selection = len(self) - 1
        self.update_line()
        self.save()

    def add_selected_ts(self, val):
        if self.selected_type == "line":
            self.append(val)
        elif self.selected_type == "onset":
            self[self.selection] = (val, self[self.selection][1])
        elif self.selected_type == "offset":
            self[self.selection] = (self[self.selection][0], val)
            
    def delete_selected_ts(self):
        if self.selected_type == "line":
            # delete the index of the selected t
            super().pop(self.selection)
        elif self.selected_type == "onset":
            # delete the onset of the selected t
            if self[self.selection][1] is None:
                super().pop(self.selection)
            else:
                self[self.selection] = (None,self[self.selection][1])
        elif self.selected_type == "offset":
            # delete the offset of the selected t
            if self[self.selection][0] is None:
                super().pop(self.selection)
            else:
                self[self.selection] = (self[self.selection][0],None)
        self.update_line()

    def show_ts_in_selection(self):
        # the selection is the index of the selected t in the ts list
        # the size of the section_window is the number of ts that can be displayed on the screen
        section_window = self.screen.getmaxyx()[0] - 2
        # clear the screen
        self.screen.clear()
        # the indexes to show are the selection minus the section_window divided by 2 and the selection plus the section_window divided by 2
        if self.selection - section_window//2 < 0:
            start = 0
            end = section_window
        elif self.selection + section_window//2 > len(self):
            start = len(self) - section_window
            end = len(self)
        else:
            start = self.selection - section_window//2
            end = self.selection + section_window//2
        self.selected_type = "line"
        for i, t in enumerate(self[start:end]):
            try:
                if len([val for val in t if val is not None]) == 1:
                    if t[0] is not None:
                        self.screen.addstr(i, 0, str(t[0])+ " | " + " ")
                        if i == self.selection - start:
                            self.screen.addstr(i, 0, str(t[0])+ " | " + " ", curses.A_REVERSE)
                    if t[1] is not None:
                        self.screen.addstr(i, 0, " " + " | " + str(t[1]))
                        if i == self.selection - start:
                            self.screen.addstr(i, 0, " " + " | " + str(t[1]), curses.A_REVERSE)
                elif len(t) == 2:
                    self.screen.addstr(i, 0, str(t[0])+ " | " + str(t[1]))
                    # if the current t is the selected t then highlight it
                    if i == self.selection - start:
                        self.screen.addstr(i, 0, str(t[0])+ " | " + str(t[1]), curses.A_REVERSE)
                else:
                    self.screen.addstr(i, 0, str(t))
            except:
                pass
    
        self.screen.refresh()
    
    def select_t_idx(self, l_or_r: Literal["l", "r"]):
        # the selection is the index of the selected t in the ts list
        section_window = self.screen.getmaxyx()[0] - 2
        # clear the screen
        self.screen.clear()
        # the indexes to show are the selection minus the section_window divided by 2 and the selection plus the section_window divided by 2
        if self.selection - section_window//2 < 0:
            start = 0
            end = section_window
        elif self.selection + section_window//2 > len(self):
            start = len(self) - section_window
            end = len(self)
        else:
            start = self.selection - section_window//2
            end = self.selection + section_window//2
        line_found = False
        for i, t in enumerate(self[start:end]):
            try:
                self.screen.addstr(i, 0, str(t[0])+ " | " + str(t[1]))
                if t == self[self.selection] and not line_found:
                    if l_or_r == "l":
                        self.selected_type = "onset"
                        if t[0] is not None:
                            # add the left side of the t to the screen reversed and the right side of the t to the screen normally
                            self.screen.addstr(i, 0, str(t[0]), curses.A_REVERSE)
                            self.screen.addstr(i, len(str(t[0])), " | ")
                            self.screen.addstr(i, len(str(t[0])) + 3, str(t[1]))
                            line_found = True
                        else:
                            self.screen.addstr(i, 0, " ", curses.A_REVERSE)
                            self.screen.addstr(i, 1, " | ")
                            self.screen.addstr(i, 4, str(t[1]))
                            line_found = True
                    elif l_or_r == "r" and not line_found:
                        self.selected_type = "offset"
                        if t[0] is not None:
                            # add the left side of the t to the screen normally and the right side of the t to the screen reversed
                            self.screen.addstr(i, 0, str(t[0]))
                            self.screen.addstr(i, len(str(t[0])), " | ")
                            self.screen.addstr(i, len(str(t[0])) + 3, str(t[1]), curses.A_REVERSE)
                            line_found = True
                        else:
                            # add the left side of the t to the screen normally and the right side of the t to the screen reversed
                            self.screen.addstr(i, 0, " ")
                            self.screen.addstr(i, 1, " | ")
                            self.screen.addstr(i, 4, str(t[1]), curses.A_REVERSE)
                            line_found = True
                else:
                    self.screen.addstr(i, 0, str(t[0])+ " | " + str(t[1]))
            except Exception as e:
                print("error", e)
        self.screen.refresh()

    def get_selected_t(self, selection) -> Union[str, Tuple[str,str]]:
        try:
            if self.selected_type == "line":
                return self[selection]
            elif self.selected_type == "onset":
                return self[selection][0]
            elif self.selected_type == "offset":
                return self[selection][1]
        except:
            return None

    def update_line(self):
        self.show_ts_in_selection()

    def __repr__(self):
        return super().__repr__()

    def __str__(self):
        return super().__str__()

    def as_array(self):
        if self.settings.save_frame_or_timestamp == "frame":
            if self.settings.scoring_type == "onset/offset":
                if len(self[-1]) == 1:
                    self[-1] = (self[-1][0], self[-1][0])
                if not self[0] == ("onset frame", "offset frame"):
                    self.insert(0, ("onset frame", "offset frame"))
            else:
                self.insert(0, ("frame"))
        elif self.settings.save_frame_or_timestamp == "timestamp":
            if self.settings.scoring_type == "onset/offset":
                if len(self[-1]) == 1:
                    self[-1] = (self[-1][0], self[-1][0])
                if not self[0] == ("onset timestamp", "offset timestamp"):
                    self.insert(0, ("onset timestamp", "offset timestamp"))
            else:
                self.insert(0, ("timestamp"))
        # assert that all tuples are of the same length
        if self.settings.scoring_type == "onset/offset":
            x = [(x[0], None) if len(x) == 1 else x for x in self]
            print(x)
            return x
        else:
            return self

    def save(self):
        if self != []:
            np.savetxt(
                self.save_path,
                self.as_array(),
                delimiter=",",
                fmt="%s",
            )

class Subtitles(list):
    def __init__(self, video_file_path, subs_path: str = None):
        self.video_file_path = video_file_path
        self.subs_path = subs_path

    def load_from_video_path(self):
        """
        Loads the subtitles from the video file path, if multiple subtitles files are found in the same directory as the video file, the first one found is used

        Raises
        ------
            IndexError: If there are no subtitles files in the same directory as the video file
        """
        try:
            self.subs_path = [
                    os.path.join(os.path.dirname(self.video_file_path), f)
                    for f in os.listdir(os.path.dirname(self.video_file_path))
                    if os.path.splitext(f)[1] == ".sub"
                ][0].replace('"', "").replace("'", "")
            self.load_from_subs_path()
        except:
            raise IndexError(
                "No subtitles file found in the same directory as the video file"
            )

    def load_from_subs_path(self):
        """
        Loads the subtitles from the subtitles file path
        """
        with open(self.subs_path, "r") as f:
            self.clear()
            self.extend(
            [s.split("}")[-1] for s in f.read().splitlines()]
            )

    def load_from_video_frames(self, max_frame: int, fps: int):
        """
        Loads the subtitles from the video max frames, converts the frames to milliseconds

        Parameters
        ----------
        max_frame : int
            The maximum number of frames in the video
        """
        self.clear()
        super().extend(
            [str(int((i / fps) * 1000)) for i in range(max_frame)]
        )

class Video:

    def __init__(self, path: str, settings: Settings, subtitles: Subtitles):
        self.path = path
        self.file_name = os.path.basename(self.path).split(".")[0]
        self.settings = settings
        self.subtitles = subtitles
        self.init_cv2()
        
    def init_cv2(self):
        self.cap = cv2.VideoCapture(self.path)
        self.frame: np.ndarray = None
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.max_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self._frame_count = 0
        self.frozen = False
        self.paused = False
        self.last_frame = None

    @property
    def props(self):
        return {"Current position in ms    ":self.cap.get(cv2.CAP_PROP_POS_MSEC),
                 "Index of next Frame    ":self.cap.get(cv2.CAP_PROP_POS_FRAMES),
                 "Current position in video    ":self.cap.get(cv2.CAP_PROP_POS_AVI_RATIO),
                 "Frame width    ":self.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                 "Frame height    ":self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                 "Frame rate    ":self.cap.get(cv2.CAP_PROP_FPS),
                 "Codec    ":self.cap.get(cv2.CAP_PROP_FOURCC),
                 "Video Frame Length    ":self.cap.get(cv2.CAP_PROP_FRAME_COUNT),
                 "Format of the Mat objects    ":self.cap.get(cv2.CAP_PROP_FORMAT),
                 "Current capture mode    ":self.cap.get(cv2.CAP_PROP_MODE),
                 "Convert RGB    ":self.cap.get(cv2.CAP_PROP_CONVERT_RGB),
                 "Aspect ratio: num/den (num)    ":self.cap.get(cv2.CAP_PROP_SAR_NUM),
                 "Aspect ratio: num/den (den)    ":self.cap.get(cv2.CAP_PROP_SAR_DEN),
                 "Current backend    ":self.cap.get(cv2.CAP_PROP_BACKEND),
                 "Codec's pixel format    ":self.cap.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT),
                 "Video bitrate in kbits/s    ":self.cap.get(cv2.CAP_PROP_BITRATE),
        }

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @frame_count.setter
    def frame_count(self, value: int):
        if value < 0:
            value = 0
        elif value > self.max_frame:
            value = self.max_frame - 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(value))
        self._frame_count = int(value)

    def imshow(self, frame):
        cv2.imshow(f"video-scoring: {self.file_name}", frame)
        self.last_frame = frame
        
    def get_frame(self):
        """Get the current frame. INCREMENTS THE FRAME COUNT!"""
        ret, frame = self.cap.read()
        return frame

    # def display_next_frame(self):
    #     self.frame = self.get_frame()
    #     if self.paused:
    #         try:
    #             sub = self.subtitles[self.__frame_inc]
    #         except IndexError:
    #             sub = self.subtitles[-1]

    #     if self.settings.show_current_timestamp:
    #         cv2.putText(
    #             self.frame,
    #             "ts: " + str(sub),
    #             (50, 50),
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             1,
    #             tuple(self.settings.text_color),
    #             2,
    #         )

    #     if self.settings.show_current_frame_number == True:
    #         cv2.putText(
    #             self.frame,
    #             "f: " + str(self.frame_count),
    #             (self.frame.shape[1] - 150, 50),
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             1,
    #             tuple(self.settings.text_color),
    #             2,
    #         )
    #     self.imshow(self.frame)
    #     return self.frame

    def display_current_frame(self):
        if self._frame_count >= self.max_frame:
            self._frame_count = self.max_frame - 1
        elif self._frame_count < 0:
            self._frame_count = 0
        # because get_frame increments the frame count, we need to decrement it here
        self.frame_count = self._frame_count
        self.frame = self.get_frame()
        if self.paused:
            try:
                sub = self.subtitles[self.frame_count]
            except IndexError:
                sub = self.subtitles[-1]

        if self.settings.show_current_timestamp:
            cv2.putText(
                self.frame,
                "ts: " + str(sub),
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                tuple(self.settings.text_color),
                2,
            )

        if self.settings.show_current_frame_number == True:
            cv2.putText(
                self.frame,
                "f: " + str(self.frame_count),
                (self.frame.shape[1] - 150, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                tuple(self.settings.text_color),
                2,
            )
        self.imshow(self.frame)
        return self.frame


def getForegroundWindowTitle() -> Optional[str]:
    hWnd = windll.user32.GetForegroundWindow()
    length = windll.user32.GetWindowTextLengthW(hWnd)
    buf = create_unicode_buffer(length + 1)
    windll.user32.GetWindowTextW(hWnd, buf, length + 1)
    # 1-liner alternative: return buf.value if buf.value else None
    if buf.value:
        return buf.value
    else:
        return ''

def update_line(lines, screen):
    # clear
    screen.clear()
    lines = lines.split("\n")
    for i, line in enumerate(lines):
        try:
            screen.addstr(i, 0, line)
        except:
            break
    screen.refresh()

def curses_input(txt: str, screen) -> str:
    curses.echo()
    screen.clear()
    line_num = 0
    for i, line in enumerate(txt.split("\n")):
        screen.addstr(i, 0, line)
        line_num = i
    screen.addstr(line_num + 1, 0, ">>> ")  
    screen.refresh()
    inp = screen.getstr(line_num + 1, 4).decode("utf-8")
    screen.move(screen.getmaxyx()[0]-1, 0)
    curses.noecho()
    return inp

def show_intro(screen, settings: Settings):
    curses.echo()
    screen.clear()
    screen.refresh()
    intro = f"""

                                                                                          
██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗            
██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║██╔════╝            
██║   ██║██║██║  ██║█████╗  ██║   ██║    ███████╗██║     ██║   ██║██████╔╝██║██╔██╗ ██║██║  ███╗           
╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ╚════██║██║     ██║   ██║██╔══██╗██║██║╚██╗██║██║   ██║           
 ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ███████║╚██████╗╚██████╔╝██║  ██║██║██║ ╚████║╚██████╔╝           
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝            



#############################################################################################################
#############################################################################################################
                                    PRESS {settings.key_bindings["help"]} FOR HELP    
#############################################################################################################
#############################################################################################################



"""
    try:
        screen.addstr(0, 0, intro.encode("utf-8"))
    except:
        screen.addstr(0, 0, f"PRESS '{settings.key_bindings['help']}' FOR HELP")
    screen.refresh()

def get_keypress_name():
    """Will return the name of the current key or an empty string. If will account for repitions of the same key"""
    global LAST_KEY
    global CURRENT_KEY
    global KEY_ITER
    global KEY_REP_THRESH
    CURRENT_KEY = keyboard.get_hotkey_name()
    is_win = any([getForegroundWindowTitle().__contains__("video-scoring:"), getForegroundWindowTitle().__contains__("cmd")])
    if CURRENT_KEY == LAST_KEY and CURRENT_KEY != "":
        if (
            KEY_ITER >= KEY_REP_THRESH
            and is_win
        ):
            return CURRENT_KEY
        if (
            KEY_ITER <= KEY_REP_THRESH and
            is_win
        ):
            KEY_ITER += 1
            return ""
    elif is_win:
        KEY_ITER = 0
        LAST_KEY = CURRENT_KEY
        return CURRENT_KEY
    else:
        return ""

def check_if_latest_version():
    """
    Checks if the current version is the latest version, if not then it will prompt the user to download the latest version
    """
    global VERSION
    try:
        response = requests.get(
            "https://api.github.com/repos/DannyAlas/vid-scoring/releases/latest"
        )
        release = response.json()
        latest_version = release["tag_name"]
        if latest_version != VERSION:
            print(f"\nNewer version available: {latest_version}")
            print(f"Download here: {release['html_url']}\n")
            # print the changelog
            print(release["body"])
    except Exception as e:
        pass

def main(screen):

    check_if_latest_version()
    settings = Settings(os.path.join(os.path.dirname(__file__), "settings.ini"), screen)
    video_file_path = filedialog.askopenfilename(
        title="Select video file",
        filetypes=(("video files", ["*.mp4", "*.avi", "*.mkv"]), ("all files", "*.*")),
    )
    while not os.path.exists(video_file_path):
        video_file_path = filedialog.askopenfilename(
            title="Select video file",
            filetypes=(("video files", ["*.mp4", "*.avi", "*.mkv"]), ("all files", "*.*")),
        )

    save_dir = filedialog.askdirectory(title="Select save directory")
    while not os.path.exists(save_dir):
        save_dir = filedialog.askdirectory(title="Select save directory")

    timestamps = Timestamps(settings, save_dir, video_file_path, screen)

    try:
        subtitles = Subtitles(video_file_path=video_file_path).load_from_video_path()
    except IndexError:
        subtitles = Subtitles(video_file_path=video_file_path)

    video = Video(video_file_path, settings, subtitles)

    if len(subtitles) == 0:
        inp = curses_input("OPTIONAL!\nEnter the path to a subtitles file or press enter to continue without subtitles:\n", screen)
        while inp != "":
            inp = inp.replace('"', "").replace("'", "")
            if os.path.exists(inp):
                try:
                    subtitles.subs_path = inp
                    subtitles.load_from_subs_path()
                    break
                except:
                    pass
            else:
                inp = curses_input("INVALID PATH!\nEnter the path to a subtitles file or press enter to continue without subtitles:\n", screen)
        if inp == "":
            subtitles.load_from_video_frames(video.max_frame, video.fps)
            video.subtitles = subtitles
    show_intro(screen, settings)

    sys.stdout = open(os.devnull, "w")
    curses.noecho()
    while video.cap.isOpened():
        try:
            sub = subtitles[video.frame_count]
        except Exception as e:
            sub = subtitles[-1]

        key = cv2.waitKey(int(1000 / video.fps))
        if key:
            keypress = get_keypress_name()
        if keypress == settings.key_bindings["help"]:
            update_line(settings.help_text, screen)
        if keypress == settings.key_bindings["exit"]:
            break
        if keypress == settings.key_bindings["save timestamp"]:
            video.frozen = not video.frozen
            if settings.save_frame_or_timestamp == "frame":
                timestamps.append(video.frame_count)
            elif settings.save_frame_or_timestamp == "timestamp":
                timestamps.add_selected_ts(sub)
        if keypress == settings.key_bindings["show stats"]:
            update_line(
                f"""\n{json.dumps(video.props, indent=4).replace('"', "").replace(",", "").replace("{", "").replace("}", "")}\n""", screen
            )
        # modify the playback speed
        if keypress == settings.key_bindings["increase playback speed"]:
            video.fps += settings.playback_settings["playback_speed_modulator"]
        if keypress == settings.key_bindings["decrease playback speed"]:
            if video.fps > settings.playback_settings["playback_speed_modulator"]:
                video.fps -= settings.playback_settings["playback_speed_modulator"]
        # seek forward or backward with z and x
        if keypress == settings.key_bindings["seek forward small frames"]:
            video.frame_count += settings.playback_settings["seek_small"]
            video.display_current_frame()
        if keypress == settings.key_bindings["seek back small frames"]:
            video.frame_count -= settings.playback_settings["seek_small"]
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["seek forward medium frames"]:
            video.frame_count += settings.playback_settings["seek_medium"]
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["seek back medium frames"]:
            video.frame_count -= settings.playback_settings["seek_medium"]
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["seek forward large frames"]:
            video.frame_count += settings.playback_settings["seek_large"]
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["seek back large frames"]:
            video.frame_count -= settings.playback_settings["seek_large"]
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["pause"]:
            video.paused = not video.paused
            if video.paused:
                video.last_frame = frame
            else:
                video.frame = video.last_frame
                video.imshow(frame)
        if keypress == settings.key_bindings["undo last timestamp save"]:
            try:
                timestamps.pop()
            except IndexError:
                pass
        if keypress == settings.key_bindings["seek to first frame"]:
            video.frame_count = 0
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["seek to last frame"]:
            video.frame_count = video.max_frame - 1
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["increment selected timestamp by seek small"]:
            timestamps.update_selection(settings.playback_settings["seek_small"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["decrement selected timestamp by seek small"]:
            timestamps.update_selection(-settings.playback_settings["seek_small"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["increment selected timestamp by seek medium"]:
            timestamps.update_selection(settings.playback_settings["seek_medium"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["decrement selected timestamp by seek medium"]:
            timestamps.update_selection(-settings.playback_settings["seek_medium"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["increment selected timestamp by seek large"]:
            timestamps.update_selection(settings.playback_settings["seek_large"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["decrement selected timestamp by seek large"]:
            timestamps.update_selection(-settings.playback_settings["seek_large"])
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["select onset timestamp"]:
            timestamps.select_t_idx("l")
        if keypress == settings.key_bindings["select offset timestamp"]:
            timestamps.select_t_idx("r")
        if keypress == settings.key_bindings["set player to selected timestamp"]:
            timestamps.show_ts_in_selection()
            line = timestamps.get_selected_t(timestamps.selection)
            if timestamps.selected_type == "line":
                video.frame_count = int(line[0])
            elif timestamps.selected_type == "onset":
                video.frame_count = int(line)
            elif timestamps.selected_type == "offset":
                video.frame_count = int(line)
            frame = video.display_current_frame()
        if keypress == settings.key_bindings["delete selected timestamp"]:
            timestamps.delete_selected_ts()
        if not video.paused:
            # frame = video.display_current_frame()
            if video.frame_count < video.max_frame - 1:
                frame = video.display_current_frame()
                video.frame_count += 1

    # end curses
    curses.endwin()    
    timestamps.save()

if __name__ == "__main__":
    import cProfile
    import pstats

    with cProfile.Profile() as pr:
        wrapper(main)


    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename="profile.prof")

