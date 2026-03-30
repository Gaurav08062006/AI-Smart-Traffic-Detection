# src/tracker.py

import math

class SimpleTracker:
    def __init__(self):
        self.objects = {}
        self.id_count = 0

    def update(self, detections):
        new_objects = {}

        for cx, cy in detections:
            matched = False

            for obj_id, (px, py) in self.objects.items():
                distance = math.hypot(cx - px, cy - py)

                # 🔥 increased threshold → more stable tracking
                if distance < 60:
                    new_objects[obj_id] = (cx, cy)
                    matched = True
                    break

            if not matched:
                new_objects[self.id_count] = (cx, cy)
                self.id_count += 1

        self.objects = new_objects
        return self.objects