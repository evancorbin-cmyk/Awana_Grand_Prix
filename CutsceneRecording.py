import subprocess
import time
import xlwings as xw
from datetime import datetime
import os
import signal
#import FinishLineCutScene

# -----------------------------
# CONFIGURATION
# -----------------------------
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"   # Path to ffmpeg.exe
CAMERA1_NAME = "4K Cam1"            # Use ffmpeg -list_devices true -f dshow -i dummy
CAMERA2_NAME = "UHD Camera"
CAMERA3_NAME = "Arducam-b0559-1080p-swift"
OUTPUT_FOLDER = r"C:\Recordings"            # Folder to save videos
EXCEL_FILE = r"C:\Users\evanc\OneDrive\Desktop\Awanas Grand Prix\Awana Timing Tracker.xlsm"
SHEET_NAME = "Results"
CELL = "B4"                         # Cell to monitor (1=start, 0=stop)
ffmpeg_process1 = None
ffmpeg_process2 = None 

# -----------------------------
# START RECORDING
# Excel trigger is "Race Started"
# -----------------------------
def start_recording():
    global ffmpeg_process1
    global ffmpeg_process2
    output_file1 = os.path.join(OUTPUT_FOLDER, f"recording1.mp4")
    output_file2 = os.path.join(OUTPUT_FOLDER, f"recording2.mp4")
    cmd1 = [
        FFMPEG_PATH,
        "-y", #Overwrites the output file
        "-f", "dshow",
        "-framerate", "100", # Set frame rate to 100 fps
        "-video_size", "1920x1080",
        "-rtbufsize", "2G",
        "-i", f"video={CAMERA3_NAME}",
        "-pix_fmt", "yuyv422",
        "-vcodec", "libx264",
        "-preset", "ultrafast",
        output_file1
    ]
    cmd2 = [
        FFMPEG_PATH,
        "-y", #Overwrites the output file
        "-f", "dshow",
        "-framerate", "30", # Set frame rate to 30 fps
        "-video_size", "2560x1440",
        "-rtbufsize", "2G",
        "-i", f"video={CAMERA2_NAME}",
        "-pix_fmt", "yuyv422",
        "-vcodec", "libx264",
        output_file2
    ]
    ffmpeg_process1 = subprocess.Popen(cmd1)
    ffmpeg_process2 = subprocess.Popen(cmd2)
    print(f"Recording started → {output_file1}")
    print(f"Recording started → {output_file2}")

# -----------------------------
# STOP RECORDING High Speed Camera
# for high speed camera, stop recording is for "2nd Car Finish"
# -----------------------------
def stop_recording1():
    global ffmpeg_process1
    if ffmpeg_process1:
        ffmpeg_process1.send_signal(signal.CTRL_C_EVENT)
        ffmpeg_process1 = None
        print("Recording1 stopped")

# -----------------------------
# STOP RECORDING 4k
# for 4k camera, stop recording is for "Race Finished"
# -----------------------------
def stop_recording2():
    global ffmpeg_process2
    if ffmpeg_process2:
        ffmpeg_process2.send_signal(signal.CTRL_C_EVENT)
        ffmpeg_process2 = None
        print("Recording2 stopped")


# -----------------------------
# MAIN LOOP
# -----------------------------
def main():
    wb = xw.Book(EXCEL_FILE)
    sheet = wb.sheets[SHEET_NAME]
    recording = False
    last_value = None
    RaceStartTrigger = "Race Started"
    SecCarFinishTrigger = "2nd Car Finish"
    FinishTrigger = "Race Finished"

    print("Monitoring Excel trigger...")

    while True:
        value = sheet.range(CELL).value

        if value != last_value:
            if value == RaceStartTrigger:
                start_recording()
                recording = True
            elif value == SecCarFinishTrigger:
                stop_recording1()
                return
            elif value == FinishTrigger:
                stop_recording2()
                return
            last_value = value

        time.sleep(0.2)


if __name__ == "__main__":
    main()
