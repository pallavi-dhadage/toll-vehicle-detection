import time
from collections import defaultdict
from typing import Dict, List

class AlertManager:
    def __init__(self, window_seconds=60):
        self.window_seconds = window_seconds
        self.counts: Dict[str, List[float]] = defaultdict(list)
        self.last_alert_time: Dict[str, float] = {}

    def add_detection(self, vehicle_type: str):
        now = time.time()
        self.counts[vehicle_type].append(now)
        self.counts[vehicle_type] = [t for t in self.counts[vehicle_type] if now - t < self.window_seconds]

    def check_and_alert(self, vehicle_type: str, threshold: int) -> bool:
        count = len(self.counts[vehicle_type])
        now = time.time()
        last = self.last_alert_time.get(vehicle_type, 0)
        if count >= threshold and (now - last) > 60:
            self.last_alert_time[vehicle_type] = now
            return True
        return False

alert_manager = AlertManager()
