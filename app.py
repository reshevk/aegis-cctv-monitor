import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import datetime
import tempfile
import time
import requests

# 1. Page Config
st.set_page_config(
    page_title="AEGIS | AI Vision Safety Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "8944820080:AAEunj6B_dpTfRZewxh7r-W95U4MhU_GO1A"
TELEGRAM_CHAT_ID = "8608774495"

# 2. Punchy Google Fonts & High-Impact Visual Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;900&family=Syne:wght@700;800&family=Space+Mono:wght@700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    h1, h2, h3, .brand-text {
        font-family: 'Syne', sans-serif !important;
    }

    .mono-font {
        font-family: 'Space Mono', monospace !important;
    }

    /* Deep Space Gradient Canvas */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #171d36 0%, #090c15 100%);
        color: #ffffff;
    }

    /* Hero Header */
    .hero-banner {
        background: linear-gradient(90deg, rgba(255, 0, 128, 0.25) 0%, rgba(0, 240, 255, 0.25) 100%);
        border: 2px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #ff007f, #00f0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Live Status HUD Cards */
    .status-card {
        border-radius: 18px;
        padding: 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.5);
    }

    .status-normal {
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.25), rgba(0, 230, 118, 0.05));
        border: 2.5px solid #00e676;
        color: #ffffff;
    }

    .status-fall {
        background: linear-gradient(135deg, rgba(255, 23, 68, 0.35), rgba(255, 23, 68, 0.1));
        border: 2.5px solid #ff1744;
        color: #ffffff;
        animation: pulse-red 1.2s infinite;
    }

    .status-intrusion {
        background: linear-gradient(135deg, rgba(255, 145, 0, 0.35), rgba(255, 145, 0, 0.1));
        border: 2.5px solid #ff9100;
        color: #ffffff;
        animation: pulse-amber 1.5s infinite;
    }

    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.8); }
        70% { box-shadow: 0 0 0 18px rgba(255, 23, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }

    @keyframes pulse-amber {
        0% { box-shadow: 0 0 0 0 rgba(255, 145, 0, 0.8); }
        70% { box-shadow: 0 0 0 18px rgba(255, 145, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 145, 0, 0); }
    }

    /* Metric Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }

    .metric-card {
        background: rgba(22, 27, 46, 0.85);
        border: 1.5px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }

    .metric-label {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #94a3b8;
    }

    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Top Banner
st.markdown("""
<div class="hero-banner">
    <div>
        <div class="hero-title">⚡ AEGIS // VISION SAFETY AI</div>
        <div class="hero-subtitle">Real-Time Skeletal Fall Detection & Autonomous Perimeter Defense</div>
    </div>
    <div style="background: rgba(0, 240, 255, 0.2); border: 1px solid #00f0ff; padding: 8px 16px; border-radius: 30px; font-weight: 700; color: #00f0ff;">
        LIVE ENGINE READY
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Stream Source Selection
col_ctrl1, col_ctrl2 = st.columns([1, 1])
with col_ctrl1:
    input_source = st.radio("Select Input Mode:", ("Live Laptop Webcam", "Upload CCTV Video File"), horizontal=True)

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = 0

def send_telegram_alert(message):
    current_time = time.time()
    if current_time - st.session_state.last_alert_time > 10:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload, timeout=2)
            st.session_state.last_alert_time = current_time
        except Exception:
            pass

# 5. UI Layout
col_feed, col_telemetry = st.columns([1.65, 1.1])
video_placeholder = col_feed.empty()
status_placeholder = col_telemetry.empty()
metrics_placeholder = col_telemetry.empty()

@st.cache_resource
def load_model():
    return YOLO("yolov8n-pose.pt")

model = load_model()

def process_stream(video_capture):
    fall_counter = 0
    intrusion_counter = 0

    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            st.info("Video stream finished.")
            break

        h, w, _ = frame.shape
        zone_x1, zone_y1, zone_x2, zone_y2 = int(w * 0.6), int(h * 0.1), int(w * 0.95), int(h * 0.6)

        # Draw Neon Restricted Perimeter
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 165, 255), 2)
        cv2.putText(frame, "[ RESTRICTED ZONE ]", (zone_x1 + 10, zone_y1 + 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        results = model(frame, conf=0.35, verbose=False)
        current_status = "NORMAL"
        badge_style = "status-normal"
        badge_icon = "🟢"
        badge_title = "SYSTEM SECURE // NORMAL"
        badge_desc = "Human subject is upright and active. No hazards detected."

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy() if result.boxes else []
            keypoints_all = result.keypoints.data.cpu().numpy() if result.keypoints is not None else []

            for idx, box in enumerate(boxes):
                bx1, by1, bx2, by2 = map(int, box[:4])
                box_w = bx2 - bx1
                box_h = by2 - by1
                cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2

                # Fall Detection Conditions
                is_box_horizontal = box_w > (box_h * 0.95)
                is_skeleton_collapsed = False

                if len(keypoints_all) > idx:
                    kpts = keypoints_all[idx]
                    l_shoulder, r_shoulder = kpts[5], kpts[6]
                    l_hip, r_hip = kpts[11], kpts[12]

                    if (l_shoulder[2] > 0.3 or r_shoulder[2] > 0.3) and (l_hip[2] > 0.3 or r_hip[2] > 0.3):
                        shoulder_y = np.mean([pt[1] for pt in [l_shoulder, r_shoulder] if pt[2] > 0.3])
                        hip_y = np.mean([pt[1] for pt in [l_hip, r_hip] if pt[2] > 0.3])
                        if abs(shoulder_y - hip_y) < 55:
                            is_skeleton_collapsed = True

                if is_box_horizontal or is_skeleton_collapsed:
                    current_status = "FALL"
                    fall_counter += 1
                    badge_style = "status-fall"
                    badge_icon = "🚨"
                    badge_title = "EMERGENCY: FALL DETECTED"
                    badge_desc = "Person is horizontal on the floor. Immediate assistance required!"
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 0, 255), 3)
                    cv2.putText(frame, "! HUMAN FALL DETECTED !", (bx1, by1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    alert_msg = f"🚨 *AEGIS CRITICAL ALERT*\n*Event:* Human Fall / Collapse Detected!\n*Timestamp:* `{datetime.datetime.now().strftime('%H:%M:%S')}`\n*Location:* Camera 01 (Local)"
                    send_telegram_alert(alert_msg)

                elif zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:
                    current_status = "INTRUSION"
                    intrusion_counter += 1
                    badge_style = "status-intrusion"
                    badge_icon = "⚠️"
                    badge_title = "WARNING: PERIMETER BREACH"
                    badge_desc = "Person detected inside designated restricted zone."
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 165, 255), 3)
                    cv2.putText(frame, "! INTRUDER !", (bx1, by1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                    
                    alert_msg = f"⚠️ *AEGIS SECURITY ALERT*\n*Event:* Restricted Perimeter Breach\n*Timestamp:* `{datetime.datetime.now().strftime('%H:%M:%S')}`"
                    send_telegram_alert(alert_msg)

        annotated_frame = results[0].plot() if results else frame
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        # Update Dynamic Status Banner
        status_placeholder.markdown(f"""
        <div class="status-card {badge_style}">
            <div style="font-size: 2.8rem; line-height: 1;">{badge_icon}</div>
            <div>
                <div style="font-size: 1.3rem; font-weight: 800; letter-spacing: -0.3px;">{badge_title}</div>
                <div style="font-size: 0.95rem; opacity: 0.9; margin-top: 4px;">{badge_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Update Live Metric HUD
        metrics_placeholder.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Fall Incidents</div>
                <div class="metric-value" style="color: #ff1744;">{fall_counter}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Zone Breaches</div>
                <div class="metric-value" style="color: #ff9100;">{intrusion_counter}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        time.sleep(0.01)

    video_capture.release()

# 6. Stream Execution
if input_source == "Live Laptop Webcam":
    cap = cv2.VideoCapture(0)
    process_stream(cap)

elif input_source == "Upload CCTV Video File":
    uploaded_file = st.file_uploader("Choose a video clip (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        cap = cv2.VideoCapture(tfile.name)
        process_stream(cap)
    else:
        st.info("👈 Upload a recorded CCTV video file above to start analysis.")
