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
    page_title="SPIDER-SENSE | AI Safety Guardian",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = "8944820080:AAEunj6B_dpTfRZewxh7r-W95U4MhU_GO1A"
TELEGRAM_CHAT_ID = "8608774495"

# 2. Spider-Man Themed Styling (Crimson Red + Electric Blue + Web Accents)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Outfit:wght@400;600;700;900&family=JetBrains+Mono:wght@700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .spidey-title {
        font-family: 'Bangers', cursive !important;
        letter-spacing: 2px;
    }

    .mono-font {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Dark Comic Canvas with Spider-Web Glow */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #1a050b 0%, #060814 60%, #020308 100%);
        color: #ffffff;
    }

    /* Spider-Man Hero Header */
    .hero-banner {
        background: linear-gradient(135deg, rgba(230, 0, 40, 0.35) 0%, rgba(0, 102, 255, 0.3) 100%);
        border: 2.5px solid #ff003c;
        border-radius: 22px;
        padding: 24px 36px;
        margin-bottom: 24px;
        box-shadow: 0 0 35px rgba(255, 0, 60, 0.45), inset 0 0 20px rgba(0, 140, 255, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .hero-title {
        font-size: 3rem;
        color: #ff003c;
        text-shadow: 0 0 15px #ff003c, 0 0 30px #ff003c, 3px 3px 0px #0055ff;
        margin: 0;
        line-height: 1.1;
    }

    .hero-subtitle {
        color: #00d4ff;
        font-size: 1.1rem;
        font-weight: 700;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }

    /* Spider-Sense Status Cards */
    .status-card {
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.7);
        transition: all 0.3s ease;
    }

    /* Green Safe State */
    .status-normal {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.25), rgba(0, 50, 25, 0.4));
        border: 3px solid #00ff88;
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.4);
    }

    /* Crimson Spider-Sense Alert */
    .status-fall {
        background: linear-gradient(135deg, rgba(255, 0, 60, 0.45), rgba(80, 0, 15, 0.6));
        border: 3px solid #ff003c;
        box-shadow: 0 0 35px rgba(255, 0, 60, 0.7);
        animation: spider-pulse 1s infinite;
    }

    /* Electric Amber Intrusion */
    .status-intrusion {
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.4), rgba(60, 35, 0, 0.5));
        border: 3px solid #ffaa00;
        box-shadow: 0 0 30px rgba(255, 170, 0, 0.6);
        animation: spider-pulse 1.4s infinite;
    }

    @keyframes spider-pulse {
        0% { transform: scale(1); box-shadow: 0 0 15px rgba(255, 0, 60, 0.7); }
        50% { transform: scale(1.02); box-shadow: 0 0 45px rgba(255, 0, 60, 1), 0 0 20px #00d4ff; }
        100% { transform: scale(1); box-shadow: 0 0 15px rgba(255, 0, 60, 0.7); }
    }

    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 18px;
    }

    .metric-card-fall {
        background: linear-gradient(145deg, rgba(35, 5, 12, 0.9), rgba(15, 2, 5, 0.95));
        border: 2px solid #ff003c;
        border-radius: 18px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 0 20px rgba(255, 0, 60, 0.35);
    }

    .metric-card-zone {
        background: linear-gradient(145deg, rgba(5, 20, 45, 0.9), rgba(2, 8, 20, 0.95));
        border: 2px solid #00d4ff;
        border-radius: 18px;
        padding: 22px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.35);
    }

    .metric-label {
        font-size: 0.9rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .metric-value {
        font-family: 'Bangers', cursive;
        font-size: 3rem;
        letter-spacing: 2px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Top Banner
st.markdown("""
<div class="hero-banner">
    <div>
        <div class="hero-title spidey-title">🕷️ SPIDER-SENSE // GUARDIAN AI</div>
        <div class="hero-subtitle">Real-Time Skeletal Fall Detection & Restricted Web-Zone Defense</div>
    </div>
    <div style="background: linear-gradient(90deg, #ff003c, #0055ff); border: 2px solid #ffffff; padding: 10px 20px; border-radius: 40px; font-weight: 900; color: #ffffff; letter-spacing: 1px; box-shadow: 0 0 20px rgba(255,0,60,0.8);">
        SPIDER-NET ACTIVE
    </div>
</div>
""", unsafe_allow_html=True)

# 4. Stream Source Selection
col_ctrl1, col_ctrl2 = st.columns([1, 1])
with col_ctrl1:
    input_source = st.radio("⚡ Select Input Stream:", ("Live Webcam Feed", "Upload CCTV Clip"), horizontal=True)

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
            st.info("Feed complete.")
            break

        h, w, _ = frame.shape
        zone_x1, zone_y1, zone_x2, zone_y2 = int(w * 0.6), int(h * 0.1), int(w * 0.95), int(h * 0.6)

        # Draw Spider Electric Blue Perimeter
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (255, 170, 0), 3)
        cv2.putText(frame, "[ SPIDER WEB ZONE ]", (zone_x1 + 10, zone_y1 + 25), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 170, 0), 2)

        results = model(frame, conf=0.35, verbose=False)
        current_status = "NORMAL"
        badge_style = "status-normal"
        badge_icon = "🟢"
        badge_title = "ALL CLEAR // PATROL SECURE"
        badge_desc = "Subject is standing tall. Spider-Sense is calm."

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
                    badge_title = "SPIDER-SENSE TINGLING: FALL DETECTED!"
                    badge_desc = "Person is down on the floor! Emergency dispatch triggered!"
                    
                    # Glowing Red Box for Fall
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 0, 255), 4)
                    cv2.putText(frame, "!! EMERGENCY FALL !!", (bx1, by1 - 12), 
                                cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 255), 2)
                    
                    alert_msg = f"🚨 *SPIDER-SENSE CRITICAL ALERT*\n*Event:* Person Fall/Collapse Detected!\n*Time:* `{datetime.datetime.now().strftime('%H:%M:%S')}`\n*Location:* Sector 01"
                    send_telegram_alert(alert_msg)

                elif zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:
                    current_status = "INTRUSION"
                    intrusion_counter += 1
                    badge_style = "status-intrusion"
                    badge_icon = "🕸️"
                    badge_title = "PERIMETER BREACH: WEB ZONE TRIPPED!"
                    badge_desc = "Unauthorized movement inside restricted perimeter boundary."
                    
                    # Amber Box for Intrusion
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 165, 255), 3)
                    cv2.putText(frame, "!! INTRUDER IN WEB !!", (bx1, by1 - 12), 
                                cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 165, 255), 2)
                    
                    alert_msg = f"🕸️ *SPIDER-SENSE WARNING*\n*Event:* Restricted Web Zone Intruder!\n*Time:* `{datetime.datetime.now().strftime('%H:%M:%S')}`"
                    send_telegram_alert(alert_msg)

        annotated_frame = results[0].plot() if results else frame
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        # Dynamic Status Banner
        status_placeholder.markdown(f"""
        <div class="status-card {badge_style}">
            <div style="font-size: 3rem; line-height: 1;">{badge_icon}</div>
            <div>
                <div style="font-size: 1.35rem; font-weight: 800; letter-spacing: -0.3px;">{badge_title}</div>
                <div style="font-size: 1rem; opacity: 0.95; margin-top: 4px; font-weight: 500;">{badge_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Spider-Man Themed HUD Counters
        metrics_placeholder.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card-fall">
                <div class="metric-label" style="color: #ff003c;">FALL ALERTS</div>
                <div class="metric-value" style="color: #ff003c;">{fall_counter}</div>
            </div>
            <div class="metric-card-zone">
                <div class="metric-label" style="color: #00d4ff;">WEB BREACHES</div>
                <div class="metric-value" style="color: #00d4ff;">{intrusion_counter}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        time.sleep(0.01)

    video_capture.release()

# 6. Stream Execution
if input_source == "Live Webcam Feed":
    cap = cv2.VideoCapture(0)
    process_stream(cap)

elif input_source == "Upload CCTV Clip":
    uploaded_file = st.file_uploader("Upload an incident clip (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        cap = cv2.VideoCapture(tfile.name)
        process_stream(cap)
    else:
        st.info("👈 Upload a video file above to start the Spider-Sense scanner.")
