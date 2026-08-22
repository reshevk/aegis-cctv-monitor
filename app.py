import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import datetime
import tempfile
import time
import requests

# 1. Enterprise Viewport Setup
st.set_page_config(
    page_title="AEGIS Command | Autonomous Edge Vision Matrix",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

TELEGRAM_BOT_TOKEN = "8944820080:AAEunj6B_dpTfRZewxh7r-W95U4MhU_GO1A"
TELEGRAM_CHAT_ID = "8608774495"

# 2. Enterprise UI Engine CSS (Commercial Security Operations Center Layout)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #0b0f17;
        color: #f3f4f6;
    }

    /* Top Command Header */
    .top-nav {
        background: #111827;
        border-bottom: 1px solid #1f2937;
        padding: 12px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: -4rem -4rem 1.5rem -4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.5);
    }

    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-badge {
        background: #2563eb;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        padding: 4px 10px;
        border-radius: 6px;
        letter-spacing: 0.5px;
    }

    .brand-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.3px;
        margin: 0;
    }

    .nav-system-status {
        display: flex;
        align-items: center;
        gap: 20px;
        font-size: 0.85rem;
        color: #9ca3af;
    }

    .status-dot {
        height: 8px;
        width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10b981;
    }

    /* Enterprise Panel Containers */
    .panel-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }

    .panel-title {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #9ca3af;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Telemetry KPI Cards */
    .kpi-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }

    .kpi-box {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 14px;
        border-left: 4px solid #3b82f6;
    }

    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #9ca3af;
        text-transform: uppercase;
    }

    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
        margin-top: 4px;
    }

    /* Dynamic Incident Alert Cards */
    .incident-nominal {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid #059669;
        border-left: 6px solid #10b981;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }

    .incident-critical {
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid #b91c1c;
        border-left: 6px solid #ef4444;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
        animation: critical-pulse 1.2s infinite;
    }

    .incident-warning {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid #d97706;
        border-left: 6px solid #f59e0b;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 14px;
    }

    @keyframes critical-pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    /* Event Audit Table */
    .audit-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.82rem;
    }

    .audit-table th {
        text-align: left;
        color: #6b7280;
        padding: 8px;
        border-bottom: 1px solid #1f2937;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.72rem;
    }

    .audit-table td {
        padding: 8px;
        border-bottom: 1px solid #111827;
        color: #d1d5db;
        font-family: 'JetBrains Mono', monospace;
    }
</style>

<!-- Top Enterprise Bar -->
<div class="top-nav">
    <div class="nav-brand">
        <span class="brand-badge">AEGIS OS</span>
        <span class="brand-title">Autonomous Edge Vision & Safety System</span>
    </div>
    <div class="nav-system-status">
        <span><span class="status-dot"></span> EDGE NODE: <strong>ACTIVE (CPU-ACCELERATED)</strong></span>
        <span>GATEWAY: <strong>192.168.1.104</strong></span>
        <span>PROTOCOL: <strong>RTSP / H.264</strong></span>
        <span style="background: #1f2937; padding: 4px 10px; border-radius: 4px; font-weight: 600;">BUILD v4.2.0-PROD</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Stream Selection Controls (Clean Enterprise Segmented Bar)
col_mode, col_info = st.columns([2, 1])
with col_mode:
    input_source = st.selectbox(
        "ACTIVE SENSOR / STREAM SOURCE:", 
        ("Physical Sensor 01 (Integrated HD Camera)", "Enterprise RTSP NVR Stream", "Archived Telemetry Video File"),
        label_visibility="collapsed"
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

# 4. Main Operations Layout
col_main_stream, col_sidebar_hud = st.columns([1.75, 1.05])
kpi_placeholder = col_main_stream.empty()
video_placeholder = col_main_stream.empty()
status_placeholder = col_sidebar_hud.empty()
log_placeholder = col_sidebar_hud.empty()

@st.cache_resource
def load_model():
    return YOLO("yolov8n-pose.pt")

model = load_model()

def process_stream(video_capture):
    fall_counter = 0
    intrusion_counter = 0
    frame_count = 0
    start_bench = time.time()

    while video_capture.isOpened():
        ret, frame = video_capture.read()
        if not ret:
            st.info("Input stream terminated or buffer empty.")
            break

        frame_count += 1
        fps = round(frame_count / (time.time() - start_bench + 0.001), 1)

        h, w, _ = frame.shape
        zone_x1, zone_y1, zone_x2, zone_y2 = int(w * 0.6), int(h * 0.1), int(w * 0.95), int(h * 0.6)

        # Draw Professional Low-Profile Overlay
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (234, 88, 12), 2)
        cv2.putText(frame, "RESTRICTED BOUNDARY [ZONE 01]", (zone_x1 + 8, zone_y1 + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (234, 88, 12), 1)

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
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (239, 68, 68), 2)
                    cv2.putText(frame, "INCIDENT: PATIENT COLLAPSE", (bx1, by1 - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (239, 68, 68), 2)
                    
                    alert_msg = f"🚨 *AEGIS CRITICAL ALERT*\n*Event:* Postural Fall / Collapse\n*Timestamp:* `{timestamp_str}`\n*Device ID:* CAM-01-NORTH"
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
                    
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (245, 158, 11), 2)
                    cv2.putText(frame, "RESTRICTED AREA BREACH", (bx1, by1 - 8), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 158, 11), 2)
                    
                    alert_msg = f"⚠️ *AEGIS SECURITY EVENT*\n*Event:* Perimeter Intrusion [Zone 01]\n*Timestamp:* `{timestamp_str}`"
                    send_telegram_alert(alert_msg)

                    if len(st.session_state.incident_log) == 0 or st.session_state.incident_log[-1]["type"] != "INTRUSION":
                        st.session_state.incident_log.append({"time": timestamp_str, "type": "INTRUSION", "loc": "ZONE-01", "sev": "WARNING"})

        # Render Professional Stream Header Overlay
        annotated_frame = results[0].plot() if results else frame
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

        # Top Real-Time KPI Telemetry Tiles
        kpi_placeholder.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-box" style="border-left-color: #3b82f6;">
                <div class="kpi-label">Processing Throughput</div>
                <div class="kpi-val">{fps} <span style="font-size: 0.9rem; color: #6b7280;">FPS</span></div>
            </div>
            <div class="kpi-box" style="border-left-color: #10b981;">
                <div class="kpi-label">System Health</div>
                <div class="kpi-val" style="color: #10b981; font-size: 1.3rem; margin-top: 8px;">OPERATIONAL</div>
            </div>
            <div class="kpi-box" style="border-left-color: #ef4444;">
                <div class="kpi-label">Fall Events</div>
                <div class="kpi-val" style="color: #f87171;">{fall_counter}</div>
            </div>
            <div class="kpi-box" style="border-left-color: #f59e0b;">
                <div class="kpi-label">Perimeter Breaches</div>
                <div class="kpi-val" style="color: #fbbf24;">{intrusion_counter}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sidebar Live Status Card
        status_placeholder.markdown(f"""
        <div class="panel-card">
            <div class="panel-title">Real-Time Threat Level</div>
            <div class="{badge_class}">
                <div style="font-weight: 700; font-size: 0.95rem;">{badge_header}</div>
                <div style="font-size: 0.82rem; color: #9ca3af; margin-top: 4px;">{badge_sub}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sidebar Live Audit Log
        recent_events = st.session_state.incident_log[-4:] if st.session_state.incident_log else []
        log_rows = "".join([
            f"<tr><td>{e['time']}</td><td style='color:{'#f87171' if e['sev']=='CRITICAL' else '#fbbf24'}; font-weight:700;'>{e['type']}</td><td>{e['loc']}</td><td>{e['sev']}</td></tr>"
            for e in reversed(recent_events)
        ])
        
        if not log_rows:
            log_rows = "<tr><td colspan='4' style='color:#6b7280; text-align:center;'>No incidents logged in session</td></tr>"

        log_placeholder.markdown(f"""
        <div class="panel-card">
            <div class="panel-title">Live Audit Log (SIEM Dispatch)</div>
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

# 5. Stream Source Router
if input_source == "Physical Sensor 01 (Integrated HD Camera)":
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    process_stream(cap)

elif input_source == "Enterprise RTSP NVR Stream":
    cctv_url = st.text_input("Enter Encrypted RTSP Channel Endpoint:", value="rtsp://admin:pass@192.168.1.100:554/stream1")
    if st.button("Initialize Video Stream Channel"):
        cap = cv2.VideoCapture(cctv_url)
        process_stream(cap)

elif input_source == "Archived Telemetry Video File":
    uploaded_file = st.file_uploader("Upload incident recording (.mp4, .avi, .mov)", type=["mp4", "avi", "mov"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        cap = cv2.VideoCapture(tfile.name)
        process_stream(cap)
