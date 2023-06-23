import os
import cv2
import numpy
file_path = input("Enter the path to the video file: ")
file_path = file_path.replace('"', '')
if not os.path.exists(file_path):
    raise FileNotFoundError("File not found")
try:
    # find a .sub in the same directory as the video file
    subs_path = [os.path.join(os.path.dirname(file_path), f) for f in os.listdir(os.path.dirname(file_path)) if os.path.splitext(f)[1] == ".sub"][0]
    subs_path = subs_path.replace('"', '')
except IndexError:
    # if there is no .sub, ask for the path
    subs_path = input("Enter the path to the .sub file: ")
    if not os.path.exists(subs_path):
        raise FileNotFoundError("File not found")

intro = ("""



██████╗  █████╗ ███╗   ██╗███╗   ██╗██╗   ██╗███████╗    ███████╗██╗  ██╗██╗████████╗████████╗██╗   ██╗    
██╔══██╗██╔══██╗████╗  ██║████╗  ██║╚██╗ ██╔╝██╔════╝    ██╔════╝██║  ██║██║╚══██╔══╝╚══██╔══╝╚██╗ ██╔╝    
██║  ██║███████║██╔██╗ ██║██╔██╗ ██║ ╚████╔╝ ███████╗    ███████╗███████║██║   ██║      ██║    ╚████╔╝     
██║  ██║██╔══██║██║╚██╗██║██║╚██╗██║  ╚██╔╝  ╚════██║    ╚════██║██╔══██║██║   ██║      ██║     ╚██╔╝      
██████╔╝██║  ██║██║ ╚████║██║ ╚████║   ██║   ███████║    ███████║██║  ██║██║   ██║      ██║      ██║       
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝      ╚═╝      ╚═╝       
                                                                                                           
██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███████╗ ██████╗ ██████╗ ██████╗ ██╗███╗   ██╗ ██████╗            
██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔═══██╗██╔══██╗██║████╗  ██║██╔════╝            
██║   ██║██║██║  ██║█████╗  ██║   ██║    ███████╗██║     ██║   ██║██████╔╝██║██╔██╗ ██║██║  ███╗           
╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ╚════██║██║     ██║   ██║██╔══██╗██║██║╚██╗██║██║   ██║           
 ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ███████║╚██████╗╚██████╔╝██║  ██║██║██║ ╚████║╚██████╔╝           
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝            
                                                                                                           
     
                                                                                                                                         
                                                                                                                                         
#############################################################################################################
#############################################################################################################
####################################    PRESS H FOR HELP    #################################################
#############################################################################################################
#############################################################################################################



      """)

help_text = """
################
KEY BINDINGS:
################

q: exit
s: save timestamp
ctrl+z: undo last timestamp save
space: pause
d: forward one frame
a: back a frame
shift+d: forward 100 frames
p: forward 1000 frames
shift+a: back 100 frames
o: back 1000 frames
1: seek to first frame
0: seek to last frame

"""

print(intro)

cap = cv2.VideoCapture(file_path)
subtitles = subs_path

with open(subtitles, 'r') as f:
    subtitles = f.read().splitlines()
    subtitles = [s.split('}')[-1] for s in subtitles]

fps = cap.get(cv2.CAP_PROP_FPS)
timestamps = []
saved_keys = []
frame_count = 0
max_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
frozen = False
paused = False

def update_line(line):
    # clear
    os.system('cls' if os.name == 'nt' else 'clear')
    print(line)

def append_timestamp(val):
    global timestamps
    timestamps.append(val)
    timestamps = sorted([float(t) for t in timestamps])
    update_line(timestamps)

# don't close the video window if we're at the end


while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # add the subtitle to the frame
        try:
            sub = subtitles[frame_count]
        except IndexError:
            sub = subtitles[-1]
        cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        # if frozen:
        #     cv2.putText(frame, "Frozen", (frame.shape[1] - 150, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        key = cv2.waitKey(int(1000/fps))
        if key == ord('h') or key == ord('H'):
            update_line(help_text)
        if key == ord('q'):
            break
        elif key == ord('s'):
            frozen = not frozen
            append_timestamp(sub)
        # modify the playback speed
        elif key == ord('x'):
            fps += 5
        elif key == ord('z'):
            if fps > 5:
                fps -= 5
        # seek forward or backward with z and x
        elif key == ord('d'):
            frame_count += 1
            if frame_count > max_frame:
                frame_count = max_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        elif key == ord('a'):
            frame_count -= 1
            if frame_count < 0:
                frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)      
        elif key == ord('A'):
            frame_count -= 100
            if frame_count < 0:
                frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)      
        elif key == ord('D'):
            frame_count += 100
            if frame_count > max_frame:
                frame_count = max_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        # ctrl_shift+d to seek forward 1000 frames
        elif key == ord('p'):
            frame_count += 1000
            if frame_count > max_frame:
                frame_count = max_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        # o to seek 1000 frames back
        elif key == ord('o'):
            frame_count -= 1000
            if frame_count < 0:
                frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        elif key == ord(' '):
            paused = not paused
            frame = cap.read()[1]
        elif key == 26:
            try:
                timestamps.pop()
                update_line(timestamps)
            except IndexError:
                pass
        elif key == ord('1'):
            frame_count = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        elif key == ord('0'):
            frame_count = max_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            if paused:
                frame = cap.read()[1]
                try:
                    sub = subtitles[frame_count]
                except IndexError:
                    sub = max_frame
                cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow('frame', frame)
        if not paused:
            cv2.imshow('frame', frame)
            if frame_count < max_frame-1:
                frame_count += 1
    else:
        break
if timestamps != []:
    # if temp.csv exists, append to it

    csv_file_name = os.path.splitext(os.path.basename(file_path))[0] + ".csv"
    num = 1
    while os.path.exists(csv_file_name):
        csv_file_name = os.path.splitext(os.path.basename(file_path))[0] + "(" + str(num) + ")" + ".csv"
        num += 1
    numpy.savetxt(csv_file_name, timestamps, delimiter=",", fmt="%s")
    print("SAVED!!")

