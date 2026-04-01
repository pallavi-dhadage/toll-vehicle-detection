import cv2
import threading
import time
import asyncio
from typing import Dict, Optional, List, Callable
from ..services.detector import detector

class Camera:
    def __init__(self, camera_id: str, url: str, fps: int = 2):
        self.id = camera_id
        self.url = url
        self.fps = fps
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.subscribers: List[Callable] = []
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        cap = cv2.VideoCapture(self.url)
        if not cap.isOpened():
            print(f"Camera {self.id}: cannot open {self.url}")
            self.running = False
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # Resize for performance
            frame = cv2.resize(frame, (640, 480))

            # Detect vehicles
            _, img_encoded = cv2.imencode('.jpg', frame)
            detections = detector.detect(img_encoded.tobytes())

            # Send to all subscribers
            with self._lock:
                subscribers = list(self.subscribers)
            for sub in subscribers:
                try:
                    asyncio.run_coroutine_threadsafe(
                        sub.send_json({
                            'camera_id': self.id,
                            'detections': detections,
                            'timestamp': time.time()
                        }),
                        asyncio.get_event_loop()
                    )
                except Exception as e:
                    print(f"Error sending to subscriber: {e}")

            time.sleep(1.0 / self.fps)

        cap.release()

    def subscribe(self, handler):
        with self._lock:
            self.subscribers.append(handler)

    def unsubscribe(self, handler):
        with self._lock:
            if handler in self.subscribers:
                self.subscribers.remove(handler)


class CameraManager:
    def __init__(self):
        self.cameras: Dict[str, Camera] = {}
        self._lock = threading.Lock()

    def add_camera(self, camera_id: str, url: str, fps: int = 2):
        with self._lock:
            if camera_id in self.cameras:
                return False
            cam = Camera(camera_id, url, fps)
            self.cameras[camera_id] = cam
            cam.start()
            return True

    def remove_camera(self, camera_id: str):
        with self._lock:
            if camera_id not in self.cameras:
                return False
            cam = self.cameras[camera_id]
            cam.stop()
            del self.cameras[camera_id]
            return True

    def get_camera(self, camera_id: str) -> Optional[Camera]:
        with self._lock:
            return self.cameras.get(camera_id)

    def list_cameras(self):
        with self._lock:
            return list(self.cameras.keys())

camera_manager = CameraManager()
