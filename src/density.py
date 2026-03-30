# src/density.py

def calculate_density(objects, frame_shape, history_lane1, history_lane2):
    h, w, _ = frame_shape
    mid = w // 2

    lane1 = 0
    lane2 = 0

    for obj_id, (cx, cy) in objects.items():
        if cx < mid:
            lane1 += 1
        else:
            lane2 += 1

    return lane1, lane2