import streamlit as st
import cv2
import numpy as np
import datetime
import tempfile
import time
import os
import requests
import av
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from ultralytics import YOLO

# ─────────────────────────────────────────────────────────────────────────
# 1. Page Configuration
# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AEGIS | Smart CCTV Safety Monitor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────
# 2. Telegram Credentials — loaded from secrets, never hardcoded
#
# Locally: put these in .streamlit/secrets.toml (see secrets.toml.example)
# On Streamlit Community Cloud: set them in the app's "Secrets" panel
# ─────────────────────────────────────────────────────────────────────────
def get_secret(key, default=None):
    """Read from st.secrets first, then environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# ─────────────────────────────────────────────────────────────────────────
# 3. Google Fonts & High-Impact Neon CSS
# ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Space+Grotesk:wght@700;800&family=JetBrains+Mono:wght@600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    h1, h2, h3, .brand-title {
        font-family: 'Space Grotesk', sans-serif !important;
    }

    .stApp {
        background: radial-gradient(circle at 15% 15%, #111827 0%, #030712 100%);
        color: #f8fafc;
    }

    .hero-box {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.22), rgba(236, 72, 153, 0.22));
        border: 1.5px solid rgba(255, 255, 255, 0.15);
        border-radius: 18px;
        padding: 22px 28px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(12px);
    }

    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .hero-tagline {
        color: #cbd5e1;
        font-size: 1rem;
        font-weight: 500;
        margin-top: 4px;
    }

    .status-card {
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .status-normal {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.08));
        border: 2px solid #10b981;
        color: #ecfdf5;
    }

    .status-fall {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(185, 28, 28, 0.15));
        border: 2px solid #ef4444;
        color: #fef2f2;
        animation: pulse-border 1.2s infinite;
    }

    .status-intrusion {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(217, 119, 6, 0.15));
        border: 2px solid #f59e0b;
        color: #fffbeb;
        animation: pulse-border 1.5s infinite;
    }

    @keyframes pulse-border {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { box-shadow: 0 0 0 14px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 14px;
    }

    .metric-pill {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(8px);
    }

    .metric-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94a3b8;
    }

    .metric-num {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.9rem;
        font-weight: 800;
        margin-top: 4px;
    }

    .config-note {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Top Banner
st.markdown("""
<div class="hero-box">
    <div class="hero-title">AEGIS // SMART CCTV MONITOR</div>
    <div class="hero-tagline">Real-time emergency fall detection & restricted perimeter security</div>
</div>
""", unsafe_allow_html=True)

if not TELEGRAM_ENABLED:
    st.markdown("""
    <div class="config-note">
        ℹ️ Telegram alerts are <b>disabled</b> — no bot token / chat ID configured.
        The app will still run and display detections on-screen. Add
        <code>TELEGRAM_BOT_TOKEN</code> and <code>TELEGRAM_CHAT_ID</code> to your Streamlit
        secrets to enable push alerts.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────
# 4. Sidebar Controls
# ─────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🎛️ **Feed Selection**")
input_source = st.sidebar.radio(
    "Select Video Feed:",
    ("Live Webcam (Browser)", "Upload Video File")
)
confidence_thresh = st.sidebar.slider("AI Sensitivity Level", 0.25, 0.85, 0.40, step=0.05)
alert_cooldown = st.sidebar.slider("Alert Cooldown (seconds)", 5, 60, 10, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Alert Status")
st.sidebar.markdown(
    "🟢 Telegram alerts **ON**" if TELEGRAM_ENABLED else "⚪ Telegram alerts **OFF**"
)

# ─────────────────────────────────────────────────────────────────────────
# 5. Telegram Alerts (debounced)
# ─────────────────────────────────────────────────────────────────────────
if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = 0.0

def send_telegram_alert(message: str, cooldown: float = 10.0):
    if not TELEGRAM_ENABLED:
        return
    current_time = time.time()
    if current_time - st.session_state.last_alert_time <= cooldown:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.ok:
            st.session_state.last_alert_time = current_time
        else:
            st.sidebar.warning(f"Telegram alert failed ({resp.status_code}).")
    except requests.exceptions.RequestException as e:
        st.sidebar.warning(f"Telegram alert failed: {e}")

# ─────────────────────────────────────────────────────────────────────────
# 6. Model Loading (cached, with a friendly error if the weights are missing)
# ─────────────────────────────────────────────────────────────────────────
MODEL_PATH = os.environ.get("AEGIS_MODEL_PATH", "yolov8n-pose.pt")

@st.cache_resource
def load_model(path):
    return YOLO(path)

try:
    model = load_model(MODEL_PATH)
    model_load_error = None
except Exception as e:
    model = None
    model_load_error = str(e)

if model_load_error:
    st.error(
        f"⚠️ Could not load the YOLO pose model (`{MODEL_PATH}`). "
        f"Detection is disabled until this is fixed.\n\nDetails: {model_load_error}"
    )

# ─────────────────────────────────────────────────────────────────────────
# 7. UI Layout
# ─────────────────────────────────────────────────────────────────────────
col_video, col_status = st.columns([1.65, 1.15])
status_placeholder = col_status.empty()
metrics_placeholder = col_status.empty()

# Shared counters (persist across frames within a session)
if "fall_counter" not in st.session_state:
    st.session_state.fall_counter = 0
if "intrusion_counter" not in st.session_state:
    st.session_state.intrusion_counter = 0


def render_status(badge_style, badge_icon, badge_title, badge_desc):
    status_placeholder.markdown(f"""
    <div class="status-card {badge_style}">
        <div style="font-size: 2.4rem; line-height: 1;">{badge_icon}</div>
        <div>
            <div style="font-size: 1.25rem; font-weight: 800; letter-spacing: -0.3px;">{badge_title}</div>
            <div style="font-size: 0.92rem; opacity: 0.9; margin-top: 4px; font-weight: 500;">{badge_desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics():
    metrics_placeholder.markdown(f"""
    <div class="metric-row">
        <div class="metric-pill">
            <div class="metric-label">Fall Alerts</div>
            <div class="metric-num" style="color: #f87171;">{st.session_state.fall_counter}</div>
        </div>
        <div class="metric-pill">
            <div class="metric-label">Intrusions</div>
            <div class="metric-num" style="color: #fbbf24;">{st.session_state.intrusion_counter}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def analyze_frame(frame, conf_thresh):
    """
    Runs pose detection on a single BGR frame, draws overlays, and returns
    (annotated_frame, status, badge info, alert_message_or_None).
    """
    h, w, _ = frame.shape
    zone_x1, zone_y1, zone_x2, zone_y2 = int(w * 0.6), int(h * 0.1), int(w * 0.95), int(h * 0.6)

    cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (245, 158, 11), 2)
    cv2.putText(frame, "RESTRICTED AREA", (zone_x1 + 10, zone_y1 + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (245, 158, 11), 2)

    status = "NORMAL"
    badge = ("status-normal", "🟢", "AREA SECURE & SAFE",
             "Person is upright and active. No emergency detected.")
    alert_msg = None

    if model is None:
        return frame, status, badge, alert_msg

    results = model(frame, conf=conf_thresh, verbose=False)

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy() if result.boxes is not None else []
        keypoints_all = result.keypoints.data.cpu().numpy() if result.keypoints is not None else []

        for idx, box in enumerate(boxes):
            bx1, by1, bx2, by2 = map(int, box[:4])
            box_w, box_h = bx2 - bx1, by2 - by1
            cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2

            is_box_horizontal = box_w > (box_h * 0.95)
            is_skeleton_collapsed = False

            if len(keypoints_all) > idx:
                kpts = keypoints_all[idx]
                l_shoulder, r_shoulder = kpts[5], kpts[6]
                l_hip, r_hip = kpts[11], kpts[12]

                if (l_shoulder[2] > 0.25 or r_shoulder[2] > 0.25) and (l_hip[2] > 0.25 or r_hip[2] > 0.25):
                    shoulder_y = np.mean([pt[1] for pt in [l_shoulder, r_shoulder] if pt[2] > 0.25])
                    hip_y = np.mean([pt[1] for pt in [l_hip, r_hip] if pt[2] > 0.25])
                    if abs(shoulder_y - hip_y) < 60:
                        is_skeleton_collapsed = True

            if is_box_horizontal or is_skeleton_collapsed:
                status = "FALL"
                st.session_state.fall_counter += 1
                badge = ("status-fall", "🚨", "EMERGENCY: FALL DETECTED",
                         "Person has collapsed or fallen flat. Immediate help required!")

                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (239, 68, 68), 3)
                cv2.putText(frame, "! FALL DETECTED !", (bx1, by1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (239, 68, 68), 2)

                alert_msg = (
                    f"🚨 *AEGIS EMERGENCY ALERT*\n*Incident:* Fall / Collapse Detected!\n"
                    f"*Time:* `{datetime.datetime.now().strftime('%H:%M:%S')}`\n*Location:* Live CCTV Camera"
                )

            elif zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:
                status = "INTRUSION"
                st.session_state.intrusion_counter += 1
                badge = ("status-intrusion", "⚠️", "WARNING: INTRUSION",
                         "Unauthorized movement inside the restricted zone.")

                cv2.rectangle(frame, (bx1, by1), (bx2, by2), (245, 158, 11), 3)
                cv2.putText(frame, "! INTRUSION !", (bx1, by1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (245, 158, 11), 2)

                alert_msg = (
                    f"⚠️ *AEGIS SECURITY ALERT*\n*Incident:* Restricted Area Intrusion\n"
                    f"*Time:* `{datetime.datetime.now().strftime('%H:%M:%S')}`"
                )

    annotated = results[0].plot() if results else frame
    return annotated, status, badge, alert_msg


# ─────────────────────────────────────────────────────────────────────────
# 8a. Live Webcam mode — runs in the VISITOR'S browser via WebRTC.
#     (A server-side cv2.VideoCapture(0) only works when you run this
#     locally — a cloud server has no physical webcam of its own.)
# ─────────────────────────────────────────────────────────────────────────
if input_source == "Live Webcam (Browser)":

    def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        annotated, status, badge, alert_msg = analyze_frame(img, confidence_thresh)

        if alert_msg:
            send_telegram_alert(alert_msg, cooldown=alert_cooldown)

        render_status(*badge)
        render_metrics()

        return av.VideoFrame.from_ndarray(annotated, format="bgr24")

    with col_video:
        webrtc_streamer(
            key="aegis-live",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback=video_frame_callback,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )
    st.caption(
        "Live mode uses your **browser's** camera (with your permission) — this works "
        "the same whether the app is running locally or deployed to the cloud."
    )

# ─────────────────────────────────────────────────────────────────────────
# 8b. Upload Video File mode
# ─────────────────────────────────────────────────────────────────────────
elif input_source == "Upload Video File":
    uploaded_file = st.sidebar.file_uploader(
        "Upload CCTV Clip (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"]
    )

    if uploaded_file is not None:
        video_placeholder = col_video.empty()
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
        tfile.write(uploaded_file.read())
        tfile.close()

        cap = cv2.VideoCapture(tfile.name)
        if not cap.isOpened():
            st.error("Could not open this video file. Try a different format (.mp4 is most reliable).")
        else:
            stop_button = st.sidebar.button("⏹ Stop Processing")
            try:
                while cap.isOpened():
                    if stop_button:
                        break
                    ret, frame = cap.read()
                    if not ret:
                        st.info("Video stream completed.")
                        break

                    annotated, status, badge, alert_msg = analyze_frame(frame, confidence_thresh)
                    if alert_msg:
                        send_telegram_alert(alert_msg, cooldown=alert_cooldown)

                    frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                    render_status(*badge)
                    render_metrics()

                    time.sleep(0.01)
            finally:
                cap.release()
                try:
                    os.unlink(tfile.name)
                except OSError:
                    pass
    else:
        st.info("👈 Upload a recorded CCTV video clip from the left sidebar.")
        render_metrics()
