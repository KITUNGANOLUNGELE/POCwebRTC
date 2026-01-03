import cv2
import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

class BnWTrack(VideoStreamTrack):
    def __init__(self, source_track, skip_frames=30, scale=0.5):
        super().__init__()
        self.track = source_track
        self.frame_count = 0
        self.skip_frames = skip_frames
        self.scale = scale

    async def recv(self):
        frame = await self.track.recv()  
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        
        h, w = img.shape[:2]
        small = cv2.resize(img, (int(w*self.scale), int(h*self.scale)))
        cv2.putText(small, "image from openCV", (10,20), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255,0,255), 2)
        processed = cv2.resize(small, (w, h))

        new_frame = VideoFrame.from_ndarray(processed, format="bgr24")
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        return new_frame