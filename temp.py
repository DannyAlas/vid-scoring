import json
import os

import cv2
import numpy as np

b1_start_frame = 536
files = [
r"I:\PAVS\vids\E124_BOX1_d6faaec1-ae34-4347-86ab-450031bbd9ab.avi",
r"I:\PAVS\vids\D149_BOX2_d9af41f6-2cea-466e-858a-0e24611b79f7.avi",
r"I:\PAVS\vids\Q359_BOX4_ccd1ffae-36a1-41f0-a4e8-ef8ff315c4fa.avi",
r"I:\PAVS\vids\A676_BOX5_ebdd28de-d269-42ef-9690-e926522d149f.avi",
r"I:\PAVS\vids\A677_BOX6_ea10f602-ec91-4e1c-a53d-58f437a4e58d.avi",
]
data_file = r"I:\PAVS\med-pc data\2023-07-08_11h03m_Subject E124.txt"
# .21 = laser on
# .6 = cs+ on
# .13 = cs- on
# .19 shock on

med_pc_arr_dict = {}
with open(data_file, 'r') as f:
    lines = [line.strip() for line in f.readlines()]
    # arr = everything after C:
    arr = lines[lines.index('C:')+1:]
    # remove the first 'number:' from each line and split on spaces
    arr = [line.split(' ')[1:] for line in arr]
    # remove empty strings
    arr = [[s for s in line if s != ''] for line in arr]
    # join the arrays
    arr = [s for line in arr for s in line]

for i in arr:
    ts = int(i.split('.')[0])
    val = i.split('.')[1]
    frame = int((ts/1000)*30 + b1_start_frame) + 2
    val_name = ["laser" if val == "210" else "cs+" if val == "600" else "cs-" if val == "130" else "shock" if val == "190" else "shock" if val == "190" else val][0]

    if frame not in med_pc_arr_dict:
        med_pc_arr_dict[frame] = val_name
    else:
        med_pc_arr_dict[frame].append(val_name)

b1_frame_len = 0
b1 = [file for file in files if file.__contains__("BOX1")][0]
cap = cv2.VideoCapture(b1)
b1_frame_len = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
cap.release()
final_dict = {b1:med_pc_arr_dict}
for file in files:
    if file.__contains__("BOX1"):
        continue
    cap = cv2.VideoCapture(file)
    frame_offset = b1_frame_len - int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # for each frame in the medpc dict add the offset then add to the final dict
    file_dict = {}
    for frame, val in med_pc_arr_dict.items():
        idx = int(frame - frame_offset)
        file_dict[idx] = val
    final_dict[file] = file_dict

data = final_dict
# save the data to a local json file
with open(os.path.join(os.path.dirname(__file__), os.path.basename(data_file).split(".")[0] + ".json"), 'w') as f:
    json.dump(data, f)


vid_dir = r"\\TRUENAS\prox-share\media\Media\Other\lab\shock videos"
video_pool = []
for vid_path in data:
    # check if the file exists in the vid dir
    video = os.path.join(vid_dir, os.path.basename(vid_path).split(".")[0] + ".mp4")
    if not os.path.exists(video):
        print(f"{video} does not exist")
        continue

    # add text to the video corresponding to the medpc data
    cap = cv2.VideoCapture(video)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object for mp4
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        video.split(".")[0] + "_annotated.mp4", fourcc, fps, (width, height)
    )

    # if the val is cs+ or cs- then the next 9.5 seconds need to be marked as well
    for i in range(frame_count):
        ret, img = cap.read()
        frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
        print(frame_num)
        if i in [x for x in data[vid_path]]:
            if (
                data[vid_path][frame_num] == "cs+"
                or data[vid_path][frame_num] == "cs-"
            ):
                print(f"frame {frame_num} is {data[vid_path][frame_num]}")
                for j in range(int(fps * 9.5)):
                    img = cv2.putText(
                        img,
                        data[vid_path][frame_num],
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA,
                    )
                    ret, img = cap.read()
                    out.write(img)
            else:
                img = cv2.putText(
                    img,
                    data[vid_path][frame_num],
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA,
                )
        out.write(img)


    cap.release()
    out.release()
