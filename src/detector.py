from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def detect(frame):
    results = model(frame, verbose=False)[0]

    detections = []
    emergency_detected = False

    emergency_counts = {
        "Ambulance": 0
    }

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        cls = int(box.cls[0])
        label = model.names[cls]

        # 🔥 store FULL BOX + label
        detections.append((cx, cy, x1, y1, x2, y2, label))

        # 🔥 ambulance simulation
        if label == "car":
            if (x1 + y1) % 25 == 0:
                emergency_detected = True
                emergency_counts["Ambulance"] += 1

    return detections, emergency_detected, emergency_counts