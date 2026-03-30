import cv2
import config
from src.tracker import SimpleTracker
from src.detector import detect
from src.density import calculate_density
from src.signal import get_signal

cap = cv2.VideoCapture(config.VIDEO_PATH)

if not cap.isOpened():
    print("❌ Cannot open video")
    exit()

tracker = SimpleTracker()

history_lane1 = []
history_lane2 = []

# 🔥 emergency cooldown timer
emergency_timer = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (800, 600))

    # STEP 1: detection
    detections, emergency_detected, emergency_counts = detect(frame)

    # STEP 2: tracking
    objects = tracker.update(detections)

    # STEP 3: density
    avg_lane1, avg_lane2 = calculate_density(
        objects, frame.shape, history_lane1, history_lane2
    )

    # 🔥 cooldown logic
    if emergency_detected:
        emergency_timer = config.EMERGENCY_COOLDOWN

    if emergency_timer > 0:
        emergency_flag = True
        emergency_timer -= 1
    else:
        emergency_flag = False

    # STEP 4: signal
    d1, t1, c1 = get_signal(avg_lane1, emergency_flag)
    d2, t2, c2 = get_signal(avg_lane2, emergency_flag)

    h, w = frame.shape[:2]

    # draw region
    cv2.rectangle(frame, (0, int(h*config.REGION_TOP)),
                  (w, int(h*config.REGION_BOTTOM)), (255,0,0), 2)

    # lane divider
    cv2.line(frame, (w//2, 0), (w//2, h), (0,255,255), 2)

    # draw objects
    for obj_id, (cx, cy) in objects.items():
        cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)
        cv2.putText(frame, f"ID:{obj_id}", (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)

    # display lane count
    cv2.putText(frame, f"Lane1: {avg_lane1}", (20,40), cv2.FONT_HERSHEY_SIMPLEX, 1, c1, 2)
    cv2.putText(frame, f"Lane2: {avg_lane2}", (20,80), cv2.FONT_HERSHEY_SIMPLEX, 1, c2, 2)

    # emergency counts
    cv2.putText(frame, f"Ambulance: {emergency_counts['Ambulance']}", (20,120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.putText(frame, f"Fire: {emergency_counts['Fire Brigade']}", (20,150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    cv2.putText(frame, f"Police: {emergency_counts['Police']}", (20,180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

    # signal display
    cv2.putText(frame, f"L1: {d1} ({t1}s)", (20,220),
                cv2.FONT_HERSHEY_SIMPLEX, 1, c1, 2)

    cv2.putText(frame, f"L2: {d2} ({t2}s)", (20,260),
                cv2.FONT_HERSHEY_SIMPLEX, 1, c2, 2)

    # emergency alert
    if emergency_flag:
        cv2.putText(frame, "EMERGENCY PRIORITY ACTIVE", (200,300),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

    cv2.imshow("Smart Traffic System", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()