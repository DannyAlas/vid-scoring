# SIMPLE VIEDO SCORING APP

## Description
Allows you to score single (onset of behavior) or double (onset and offset of behavior) events in a video.

## Installation
1. Get the latest release from [here](https://github.com/DannyAlas/vid-scoring/releases/latest) and download the `vid-scoring.zip` file.
2. Unzip the file and run the vid-scoring.exe file.

## Usage
1. Run the vid-scoring.exe file.
2. Depending on how Windows is feeling that day, you may get a warning message. If so, click "More info" and then "Run anyway".
![image](https://github.com/DannyAlas/vid-scoring/assets/81212794/b5620628-329a-4f3d-9c19-48318c0f239f)
3. A command prompt Window will open up and prompt you to enter the path to the video you want to score. You can either type the path or drag and drop the video file into the command prompt window. Then press enter. (Quotation marks are not necessary)
![image](https://github.com/DannyAlas/vid-scoring/assets/81212794/4953603d-5598-4a5b-9f36-02b479162115)
4. You will then be prompted to enter the path to a `.sub` file. This is optional. If you are scoring a TDT tank file, you can enter the path to the `.sub` file in the block and the program will automatically load the timestamps for the video from TDT. If you are not scoring a TDT tank file, you can skip this step by pressing enter.
5. The video should then open up in a new window. Press 'h' to see the help menu. Score away!

## Settings
The settings file is located in the main folder within the folder containing the vid-scoring.exe file. It is called `settings.ini`. You can edit this file with any text editor. The default settings are as follows:

### Scoring Settings
| Setting Name    | Description                                                                                                                                                                            |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| scoring_type   | EITHER `onset/offset` OR `onset`. Determines how the data is saved                                                                                                              |
| save_frame_or_timestamp | EITHER `frame` OR `timestamp`. Determines wheather to save the current frame number or video timestamp  |
| text_color           |  The color of the text drawn over the video                                                                |
| show_current_frame_number           | EITHER `true` OR `false` Weather to show the current frame number in the top left corner of the video                |   
| show_current_timestamp           | EITHER `true` OR `false` Weather to show the current timestamp in the top left corner of the video                |
| show_fps           | EITHER `true` OR `false` Weather to show the current playback F.P.S. in the top left corner of the video                |

### Playback Settings
| Setting Name    | Description                                                                                                                                                                            |
|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| seek_small   | The number of frames to seek forward or backward when seeking a small amount                                                                                                              |
| seek_medium  | The number of frames to seek forward or backward when seeking a medium amount                                                                                                              |
| seek_large   | The number of frames to seek forward or backward when seeking a large amount                                                                |
| playback_speed_modulator           | The number of framed to increase/decrease the playback speed                |

### Key Bindings
| Setting Name    | Default Key | Description                                                                       |
|----------------|-------------|------------------------------------------------------------------------------------|
| exit           | `q`       | Exit the program                                                                     |
| help           | `h`       | Show the help menu                                                                   |
| show_stats     | `i`       | Show the current video stats                                                         |
| save_timestamp | `s`       | Save the current timestamp to the output file                                        |
| undo_last_timestamp_save | `ctrl+z`       | Undo the last timestamp save.                                         |
| pause          | `space`   | Play/Pause the video                                                                 |
| seek_forward_small_frames | `d`   | Seek forward a small amount of frames                                         |
| seek_back_small_frames | `a`   | Seek backward a small amount of frames                                           |
| seek_forward_medium_frames | `shift+D`   | Seek forward a medium amount of frames                                 |
| seek_back_medium_frames | `shift+A`   | Seek backward a medium amount of frames                                   |
| seek_forward_large_frames | `p`   | Seek forward a large amount of frames                                         |
| seek_back_large_frames | `o`   | Seek backward a large amount of frames                                           |
| seek_to_first_frame | `1`   | Seek to the first frame                                                             |
| seek_to_last_frame | `0`   | Seek to the last frame                                                               |
| increase_playback_speed | `x`   | Increase the playback speed by the amount specified in the settings             |
| decrease_playback_speed | `z`   | Decrease the playback speed by the `playback_speed_modulator` amount            | 