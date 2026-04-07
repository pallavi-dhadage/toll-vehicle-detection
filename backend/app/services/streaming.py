import cv2
import threading
import time
import asyncio
from typing import Dict, Optional, List, Callable
from ..services.detector import detector
from ..services.tracker import tracker_manager
from ..services.alerts import alert_manager

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

    def _compute_iou(self, box1, box2):
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - inter
        return inter / union if union > 0 else 0

    def _run(self):
        cap = cv2.VideoCapture(self.url)
        if not cap.isOpened():
            print(f"Camera {self.id}: cannot open {self.url}")
            self.running = False
            return

        tracker = tracker_manager.get_tracker(self.id)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (640, 480))
            _, img_encoded = cv2.imencode('.jpg', frame)
            detections = detector.detect(img_encoded.tobytes())

            deepsort_dets = []
            for det in detections:
                bbox = det["bbox"]
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                deepsort_dets.append(([bbox[0], bbox[1], w, h], det["confidence"], 0))

            tracked_objects = tracker.update_tracks(deepsort_dets, frame=frame)

            results = []
            vehicle_types_seen = set()

            for track in tracked_objects:
                if not track.is_confirmed():
                    continue
                track_id = track.track_id
                ltrb = track.to_ltrb()
                best_iou = 0
                best_det = None
                for det in detections:
                    iou = self._compute_iou(ltrb, det["bbox"])
                    if iou > best_iou:
                        best_iou = iou
                        best_det = det
                if best_det:
                    vtype = best_det["type"]
                    vehicle_types_seen.add(vtype)
                    alert_manager.add_detection(vtype)
                    results.append({
                        "track_id": track_id,
                        "type": vtype,
                        "confidence": best_det["confidence"],
                        "bbox": list(ltrb)
                    })
                else:
                    results.append({
                        "track_id": track_id,
                        "type": "unknown",
                        "confidence": 0,
                        "bbox": list(ltrb)
                    })

            for vtype in vehicle_types_seen:
                if alert_manager.check_and_alert(vtype, 3):  # alert after 3 vehicles in a minute
                    alert_msg = {
                        'type': 'alert',
                        'message': f'⚠️ High volume of {vtype}s detected in the last minute!',
                        'vehicle_type': vtype,
                        'timestamp': time.time()
                    }
                    with self._lock:
                        subs = list(self.subscribers)
                    for sub in subs:
                        try:
                            asyncio.run_coroutine_threadsafe(
                                sub.send_json(alert_msg),
                                asyncio.get_event_loop()
                            )
                        except Exception as e:
                            print(f"Alert send error: {e}")

            with self._lock:
                subscribers = list(self.subscribers)
            for sub in subscribers:
                try:
                    asyncio.run_coroutine_threadsafe(
                        sub.send_json({
                            'camera_id': self.id,
                            'detections': results,
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
