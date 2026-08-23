import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import datetime
import tempfile
import time
import requests

# 1. Viewport Config
st.set_page_config(
    page_title="AEGIS RED | Edge Vision Matrix",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TELEGRAM_BOT_TOKEN = "8944820080:AAEunj6B_dpTfRZewxh7r-W95U4MhU_GO1A"
TELEGRAM_CHAT_ID = "8608774495"

# 2. Complete CSS Fix (Hides Default Streamlit Navbar & Fixes Spacing)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Space+Grotesk:wght@600;700;800&family=JetBrains+Mono:wght@600;700&display=swap');

    /* Hide Streamlit Header/Footer completely to eliminate top cut-off */
    header { visibility: hidden !important; height: 0px !important; }
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    /* Natural padding from top */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        max-width: 96% !important;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #1c0509 0%, #0c0204 60%, #050102 100%);
        color: #f8fafc;
    }

    /* Fixed Top Command Header */
    .top-nav {
        background: linear-gradient(135deg, rgba(38, 7, 13, 0.95), rgba(18, 3, 6, 0.98));
        border: 1.5px solid #ff1744;
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 0 25px rgba(255, 23, 68, 0.25);
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-badge {
        background: #ff1744;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 5px 12px;
        border-radius: 6px;
        letter-spacing: 0.8px;
        box-shadow: 0 0 12px rgba(255, 23, 68, 0.6);
    }

    .brand-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.35rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.3px;
        margin: 0;
    }

    .nav-telemetry {
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 0.82rem;
        color: #cbd5e1;
    }

    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #00e676;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #00e676;
    }

    /* 4-Tile Telemetry Row */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }

    .kpi-box {
        background: rgba(26, 4, 8, 0.85);
        border: 1px solid rgba(255, 23, 68, 0.25);
        border-radius: 10px;
        padding: 14px 18px;
        border-left: 4px solid #ff1744;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }

    .kpi-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #fda4af;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.65rem;
        font-weight: 800;
        color: #ffffff;
        margin-top: 4px;
    }

    /* Sidebar Cards */
    .panel-card {
        background: rgba(22, 3, 7, 0.9);
        border: 1px solid rgba(255, 23, 68, 0.2);
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
    }

    .panel-title {
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #fda4af;
        margin-bottom: 12px;
    }

    /* Status Notifications */
    .incident-nominal {
        background: rgba(0, 230, 118, 0.12);
        border: 1px solid #00e676;
        border-left: 6px solid #00e676;
        border-radius: 8px;
        padding: 14px;
        color: #ffffff;
    }

    .incident-critical {
        background: rgba(255, 23, 68, 0.2);
        border: 1.5px solid #ff1744;
        border-left: 6px solid #ff1744;
        border-radius: 8px;
        padding: 14px;
        color: #ffffff;
        animation: crimson-pulse 1.2s infinite;
    }

    .incident-warning {
        background: rgba(255, 145, 0, 0.18);
        border: 1.5px solid #ff9100;
        border-left: 6px solid #ff9100;
        border-radius: 8px;
        padding: 14px;
        color: #ffffff;
    }

    @keyframes crimson-pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.6); }
        70% { box-shadow: 0 0 0 12px rgba(255, 23, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }

    /* SIEM Audit Table */
    .audit-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
    }

    .audit-table th {
        text-align: left;
        color: #94a3b8;
        padding: 8px;
        border-bottom: 1px solid rgba(255, 23, 68, 0.2);
        font-size: 0.72rem;
        text-transform: uppercase;
    }

    .audit-table td {
        padding: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #f1f5f9;
        font-family: 'JetBrains Mono', monospace;
    }
</style>

<!-- Visible Header -->
<div class="top-nav">
    <div class="nav-brand">
        <span class="brand-badge">AEGIS RED</span>
        <span class="brand-title">Autonomous Edge Vision Command</span>
    </div>
    <div class="nav-telemetry">
        <span><span class="status-dot"></span> NODE: <strong>ACTIVE</strong></span>
        <span>GATEWAY: <strong>192.168.1.104</strong></span>
        <span>PROTOCOL: <strong>RTSP / H.264</strong></span>
        <span style="background: rgba(255, 23, 68, 0.15); border: 1px solid #ff1744; padding: 4px 8px; border-radius: 4px; font-weight: 700; color: #ff1744;">ENTERPRISE PROD</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Source Selection Control
input_source = st.selectbox(
    "Active Sensor Feed:", 
    ("Physical Sensor 01 (Integrated HD Camera)", "Physical IP / CCTV Stream (RTSP)", "Upload Recorded CCTV Clip")
)

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = 0

if "incident_log" not in st.session_state:
    st.session_state.incident_log = []

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

# 4. Viewport Layout
col_main_stream, col_sidebar_hud = st.columns([1.75, 1.05])
kpi_placeholder = col_main_stream.empty()
video_placeholder = col_main_stream.empty()
status_placeholder = col_sidebar_hud.empty()
log_placeholder = col_sidebar_hud.empty()

@st.cache_resource
def load_model():
    return YOLO("yolov8n-pose.pt")

model = load_model()

def get_working_camera():
    """Robust camera locator checking backends and indices."""
    for index in [0, 1, 2]:
        # Try DirectShow first on Windows
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                return cap
            cap.release()
        
        # Fallback to default backend
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                return cap
            cap.release()
    return None

def process_stream(video_capture):
    fall_counter = 0
    intrusion_counter = 0
    frame_count = 0
    start_bench = time.time()

    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret or frame is None:
            st.warning("Video stream ended or frame could not be read.")
            break

        frame_count += 1
        fps = round(frame_count / (time.time() - start_bench + 0.001), 1)

        h, w, _ = frame.shape
        zone_x1, zone_y1, zone_x2, zone_y2 = int(w * 0.6), int(h * 0.1), int(w * 0.95), int(h * 0.6)

        # Draw Restricted Zone Boundary
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 140, 255), 2)
        cv2.putText(frame, "RESTRICTED BOUNDARY [ZONE 01]", (zone_x1 + 8, zone_y1 + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 140, 255), 1)

        results = model(frame, conf=0.35, verbose=False)
        current_status = "NOMINAL"
        badge_class = "incident-nominal"
        badge_header = "AREA SECURE // ALL SENSORS NOMINAL"
        badge_sub = "No biomechanical anomalies or perimeter breaches flagged."

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy() if result.boxes else []
            keypoints_all = result.keypoints.data.cpu().numpy() if result.keypoints is not None else []

            for idx, box in enumerate(boxes):
                bx1, by1, bx2, by2 = map(int, box[:4])
                box_w = bx2 - bx1
                box_h = by2 - by1
                cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2

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

                timestamp_str = datetime.datetime.now().strftime('%H:%M:%S')

                # Critical Incident: Fall
                if is_box_horizontal or is_skeleton_collapsed:
                    current_status = "CRITICAL"
                    fall_counter += 1
                    badge_class = "incident-critical"
                    badge_header = "CRITICAL INCIDENT: POSTURAL COLLAPSE"
                    badge_sub = "Biomechanical collapse verified. Immediate responder dispatch initiated."
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 0, 255), 2)
                    cv2.putText(frame, "INCIDENT: PATIENT COLLAPSE", (bx1, by1 - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
                    
                    alert_msg = f"🚨 *AEGIS CRITICAL ALERT*\n*Event:* Postural Fall / Collapse\n*Timestamp:* `{timestamp_str}`\n*Device ID:* CAM-01-PRIMARY"
                    send_telegram_alert(alert_msg)

                    if len(st.session_state.incident_log) == 0 or st.session_state.incident_log[-1]["type"] != "FALL":
                        st.session_state.incident_log.append({"time": timestamp_str, "type": "FALL", "loc": "CAM-01", "sev": "CRITICAL"})

                # Warning Incident: Intrusion
                elif zone_x1 < cx < zone_x2 and zone_y1 < cy < zone_y2:
                    current_status = "WARNING"
                    intrusion_counter += 1
                    badge_class = "incident-warning"
                    badge_header = "SECURITY EVENT: BOUNDARY BREACH"
                    badge_sub = "Unauthorized target detected inside virtual restricted zone [Zone 01]."
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 140, 255), 2)
                    cv2.putText(frame, "RESTRICTED AREA BREACH", (bx1, by1 - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 140, 255), 2)
                    
                    alert_msg = f"⚠️ *AEGIS SECURITY EVENT*\n*Event:* Perimeter Intrusion [Zone 01]\n*Timestamp:* `{timestamp_str}`"
                    send_telegram_alert(alert_msg)

                    if len(st.session_state.incident_log) == 0 or st.session_state.incident_log[-1]["type"] != "INTRUSION":
                        st.session_state.incident_log.append({"time": timestamp_str, "type": "INTRUSION", "loc": "ZONE-01", "sev": "WARNING"})

        annotated_frame = results[0].plot() if results else frame
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        # 4-Tile Telemetry Row
        kpi_placeholder.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-box" style="border-left-color: #ff1744;">
                <div class="kpi-label">Throughput</div>
                <div class="kpi-val">{fps} <span style="font-size: 0.85rem; color: #fda4af;">FPS</span></div>
            </div>
            <div class="kpi-box" style="border-left-color: #00e676;">
                <div class="kpi-label">System Health</div>
                <div class="kpi-val" style="color: #00e676; font-size: 1.25rem; margin-top: 6px;">OPERATIONAL</div>
            </div>
            <div class="kpi-box" style="border-left-color: #ff1744;">
                <div class="kpi-label">Fall Events</div>
                <div class="kpi-val" style="color: #ff1744;">{fall_counter}</div>
            </div>
            <div class="kpi-box" style="border-left-color: #ff9100;">
                <div class="kpi-label">Perimeter Breaches</div>
                <div class="kpi-val" style="color: #ff9100;">{intrusion_counter}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Threat Matrix Status Card
        status_placeholder.markdown(f"""
        <div class="panel-card">
            <div class="panel-title">Threat Assessment Matrix</div>
            <div class="{badge_class}">
                <div style="font-weight: 800; font-size: 0.95rem;">{badge_header}</div>
                <div style="font-size: 0.82rem; opacity: 0.9; margin-top: 4px;">{badge_sub}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # SIEM Audit Log
        recent_events = st.session_state.incident_log[-4:] if st.session_state.incident_log else []
        log_rows = "".join([
            f"<tr><td>{e['time']}</td><td style='color:{'#ff1744' if e['sev']=='CRITICAL' else '#ff9100'}; font-weight:700;'>{e['type']}</td><td>{e['loc']}</td><td>{e['sev']}</td></tr>"
            for e in reversed(recent_events)
        ])
        
        if not log_rows:
            log_rows = "<tr><td colspan='4' style='color:#94a3b8; text-align:center;'>No incidents logged in session</td></tr>"

        log_placeholder.markdown(f"""
        <div class="panel-card">
            <div class="panel-title">Live SIEM Incident Ledger</div>
            <table class="audit-table">
                <thead>
                    <tr><th>Time</th><th>Incident</th><th>Source</th><th>Severity</th></tr>
                </thead>
                <tbody>
                    {log_rows}
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        time.sleep(0.01)

    video_capture.release()

# 5. Execution Handlers
if input_source == "Physical Sensor 01 (Integrated HD Camera)":
    cap = get_working_camera()
    if cap is None:
        st.error("⚠️ Could not detect an active webcam. Ensure no other application (Teams, Zoom, Windows Camera) is using your webcam.")
    else:
        process_stream(cap)

elif input_source == "Physical IP / CCTV Stream (RTSP)":
    cctv_url = st.text_input("Enter Encrypted RTSP Channel Endpoint:", value="rtsp://admin:password@192.168.1.100:554/stream1")
    if st.button("Initialize Video Stream Channel"):
        cap = cv2.VideoCapture(cctv_url)
        process_stream(cap)

elif input_source == "Upload Recorded CCTV Clip":
    uploaded_file = st.file_uploader("Upload incident recording (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        cap = cv2.VideoCapture(tfile.name)
        process_stream(cap)
