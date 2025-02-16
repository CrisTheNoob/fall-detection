from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, "detection/index.html")

import cv2
import numpy as np
from django.http import StreamingHttpResponse


SEMAPHORE_API_KEY = "YOUR_SEMAPHORE_API_KEY"
RECIPIENT_NUMBER = "639XXXXXXXXX"  #

# Load pre-trained fall detection model (Replace with an actual model)
fall_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_fullbody.xml")

fall_alert_sent = False  # To prevent spam messages

def send_sms_alert():
    global fall_alert_sent
    if not fall_alert_sent:
        url = "https://api.semaphore.co/api/v4/messages"
        payload = {
            "apikey": SEMAPHORE_API_KEY,
            "number": RECIPIENT_NUMBER,
            "message": "⚠️ Fall Detected! Please check immediately.",
            "sendername": "FallAlert"
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("SMS Alert Sent!")
            fall_alert_sent = True  # Prevent multiple alerts
        else:
            print("Failed to send SMS:", response.text)

def detect_fall(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bodies = fall_cascade.detectMultiScale(gray, 1.1, 5)

    fall_detected = False
    for (x, y, w, h) in bodies:
        aspect_ratio = h / w  # A fall usually means lying down, so the aspect ratio changes
        if aspect_ratio < 1.2:  # Adjust this threshold based on testing
            fall_detected = True
            cv2.putText(frame, "FALL DETECTED!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

    return frame, fall_detected

def video_stream():
    cap = cv2.VideoCapture(0)  # Use external webcam (change index if needed)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, fall_detected = detect_fall(frame)

        _, jpeg = cv2.imencode('.jpg', frame)
        frame_bytes = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

    cap.release()
    cv2.destroyAllWindows()

def video_feed(request):
    return StreamingHttpResponse(video_stream(), content_type="multipart/x-mixed-replace; boundary=frame")
