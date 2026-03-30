from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
import cv2
import os
import config
from urllib.parse import unquote_plus, quote_plus

from src.detector import detect
from src.tracker import SimpleTracker
from src.density import calculate_density
from src.signal import get_signal   # 🚦 NEW IMPORT

app = Flask(__name__)
app.secret_key = "secret123"

VIDEO_FOLDER = config.VIDEO_FOLDER

tracker = SimpleTracker()
history_lane1, history_lane2 = [], []

# ==============================
# GRAPH STORAGE (PER SOURCE)
# ==============================
video_history = {}


# 🔐 LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == "admin" and request.form['password'] == "1234":
            session['user'] = "admin"
            return redirect(url_for('index'))
        return "Invalid Credentials"
    return render_template('login.html')


# 🏠 DASHBOARD
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


# 📁 STORE PAGE
@app.route('/store')
def store():
    videos = config.VIDEO_URLS
    return render_template('store.html', videos=videos)


# ==============================
# GRAPH API
# ==============================
@app.route('/graph_data/<path:source>')
def graph_data(source):
    return jsonify(video_history.get(source, []))


# 🎥 PROCESS FRAME
def process_frame(frame, source):
    global video_history

    frame = cv2.resize(frame, (700, 450))

    try:
        detections, emergency_detected, emergency_counts = detect(frame)

        # 🔥 Tracking using centers
        centers = [(d[0], d[1]) for d in detections]
        objects = tracker.update(centers)

        lane1, lane2 = calculate_density(objects, frame.shape, history_lane1, history_lane2)

        total_count = len(objects)

        # ==============================
        # GRAPH UPDATE
        # ==============================
        if source not in video_history:
            video_history[source] = []

        video_history[source].append(total_count)

        if len(video_history[source]) > 50:
            video_history[source].pop(0)

        h, w, _ = frame.shape

        # Lane divider
        cv2.line(frame, (w//2, 0), (w//2, h), (0,255,255), 2)

        # 🔥 DRAW BOUNDING BOXES
        for det in detections:
            cx, cy, x1, y1, x2, y2, label = det

            assigned_id = None
            for obj_id, (px, py) in objects.items():
                if abs(cx - px) < 20 and abs(cy - py) < 20:
                    assigned_id = obj_id
                    break

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

            text = f"{label} ID:{assigned_id}" if assigned_id is not None else label

            cv2.putText(frame, text, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        # 🚦 SIGNAL LOGIC
        signal_text, signal_time = get_signal(
            lane1,
            lane2,
            emergency_counts['Ambulance'] > 0
        )

        # 🔥 Lane colors based on signal
        color1 = (0,255,0) if "Lane 1" in signal_text else (0,0,255)
        color2 = (0,255,0) if "Lane 2" in signal_text else (0,0,255)

        # Lane counts
        cv2.putText(frame, f"Lane1: {lane1}", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color1, 2)

        cv2.putText(frame, f"Lane2: {lane2}", (10,60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color2, 2)

        # Total
        cv2.putText(frame, f"Total: {total_count}", (10,90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        # Ambulance count
        cv2.putText(frame, f"Ambulance: {emergency_counts['Ambulance']}", (10,120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        # 🚦 Signal display
        cv2.putText(frame, f"Signal: {signal_text}", (10,160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv2.putText(frame, f"Timer: {signal_time}s", (10,190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    except Exception as e:
        print("⚠️ Processing error:", e)

    return frame


# 🎥 STORED VIDEO
@app.route('/video/<filename>')
def video(filename):
    # filename is logical name e.g. video1, video2, etc.
    video_url = config.VIDEO_URLS.get(filename)

    if video_url is None:
        return f"Video '{filename}' not found", 404

    def gen():
        cap = cv2.VideoCapture(video_url)

        if not cap.isOpened():
            # fallback local path
            local_path = os.path.join(VIDEO_FOLDER, os.path.basename(video_url))
            cap = cv2.VideoCapture(local_path)

        while True:
            success, frame = cap.read()

            if not success:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = process_frame(frame, filename)

            ret, buffer = cv2.imencode('.jpg', frame)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


# 🎥 LIVE PAGE
@app.route('/live')
def live_page():
    return render_template('live.html')


# 🎥 LIVE FEED
@app.route('/live_feed')
def live_feed():
    def gen():
        cap = cv2.VideoCapture(0)

        while True:
            success, frame = cap.read()

            if not success:
                continue

            frame = process_frame(frame, "live")

            ret, buffer = cv2.imencode('.jpg', frame)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


# 🚀 RUN
if __name__ == "__main__":
    app.run(debug=True)