from deep_sort_realtime.deepsort_tracker import DeepSort

class TrackerManager:
    def __init__(self):
        self.trackers = {}

    def get_tracker(self, camera_id):
        if camera_id not in self.trackers:
            self.trackers[camera_id] = DeepSort(max_age=5, n_init=2, nms_max_overlap=1.0)
        return self.trackers[camera_id]

tracker_manager = TrackerManager()
