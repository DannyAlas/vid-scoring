import os
import cv2
import numpy


file_path = r"E:\D-E mice Recording Backup\FiPho-230208\d91\FiPho-230208_d91_Cam1.avi"
subs_path = r"E:\D-E mice Recording Backup\FiPho-230208\d91\FiPho-230208_d91_Cam1.sub"

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

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # add the subtitle to the frame
        try:
            sub = subtitles[frame_count]
        except IndexError:
            sub = max_frame
        cv2.putText(frame, sub, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        # if frozen:
        #     cv2.putText(frame, "Frozen", (frame.shape[1] - 150, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        key = cv2.waitKey(int(1000/fps))
        if key == ord('q'):
            break
        elif key == ord('s'):
            frozen = not frozen
            timestamps.append(sub)
            print(timestamps)
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
        elif key == ord(' '):
            paused = not paused
            frame = cap.read()[1]
        elif key == 26:
            try:
                timestamps.pop()
            except IndexError:
                pass
        if not paused:
            cv2.imshow('frame', frame)
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
    print(timestamps)

