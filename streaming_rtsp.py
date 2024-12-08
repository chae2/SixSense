import os
import subprocess
from threading import Thread
import time

# Define RTSP streaming class
class RTSPStreaming:
    def __init__(self, width=640, height=640, framerate=24, bitrate=2000000, port=8554):
        self.width=width
        self.height=height
        self.framerate=framerate
        self.bitrate=bitrate
        self.port=port
        self.ffmpeg_process=None
    
    def start_camera_stream(self):
        # Start Raspberry Pi camera with H.264 output
        camera_cmd = (
            f"raspivid -o - -t 0 -w {self.width} -h {self.height} "
            f"-fps {self.framerate} -b {self.bitrate} -pf high"
        )
        return subprocess.Popen(camera_cmd.split(),stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def start_rtsp_server(self, camera_process):
        ffmeg_cmd = (
            f"ffmpeg -re -i pipe:0 -c:v copy -f rtsp rtsp://0.0.0.0:{self.port}/live.sdp"
        )
        self.ffmpeg_process = subprocess.Popen(
            ffmeg_cmd.split(),
            stdin=camera_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    def start(self):
        print(f"Starting RTSP server on port {self.port}...")
        camera_process = self.start_camera_stream()
        self.start_rtsp_server(camera_process)
    def stop(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            print("RTSP server stopped.")

if __name__=="__main__":
    streaming = RTSPStreaming(width=640, height=480, framerate=24, bitrate=2000000, port=8554)
    try:
        streaming.start()
        print(f"RTSP stream is live at rtsp://192.168.1.7:8554/live.sdp")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        streaming.stop()

