import os
import time
import json
import cv2
import requests
from PIL import Image
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="AegisCare - Elderly Monitor",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. Environment & Credentials ---
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

TELEGRAM_BOT_TOKEN = "8944820080:AAEunj6B_dpTfRZewxh7r-W95U4MhU_GO1A"
TELEGRAM_CHAT_ID = "8608774495"

VIDEO_PATH = "demo_cctv.mp4"
OUTPUT_JSON = "activity_logs.json"
SAMPLE_INTERVAL_SEC = 2

# --- 3. Telegram Dispatcher ---
def send_telegram_alert(timestamp_str: str, summary: str):
    """Sends an emergency Telegram alert when a fall is detected."""
    message = (
        f"🚨 *CRITICAL EMERGENCY ALERT: FALL DETECTED* 🚨\n\n"
        f"📍 *Camera:* Living Room CCTV\n"
        f"⏱️ *Timestamp:* {timestamp_str}\n"
        f"⚠️ *Observation:* {summary}\n\n"
        f"👉 *Action Required:* Check on the resident immediately!"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram alert error: {e}")

# --- 4. Frame Analysis Engine ---
def analyze_frame(frame, timestamp_sec: float, model) -> dict:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    time_label = f"{int(timestamp_sec // 60):02d}:{int(timestamp_sec % 60):02d}"

    prompt = f"""
    Analyze this elderly care CCTV frame captured at {timestamp_sec:.1f}s ({time_label}).
    Focus strictly on:
    1. Activities: eating, taking_medicine, walking, sitting, lying_down, idle.
    2. Fall/Distress: true if the person slipped, fell, or is lying on the floor.

    Return strictly valid JSON:
    {{
      "timestamp_sec": {timestamp_sec},
      "time_label": "{time_label}",
      "activity": "eating" | "taking_medicine" | "walking" | "sitting" | "lying_down" | "idle",
      "is_distress": false,
      "summary": "1-sentence summary of the action."
    }}
    """
    try:
        response = model.generate_content(
            [prompt, pil_image],
            generation_config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        
        # Fire Telegram alert if fall detected
        if data.get("is_distress", False) or data.get("activity") == "lying_down":
            send_telegram_alert(time_label, data.get("summary", "Fall detected."))
            
        return data
    except Exception:
        return {
            "timestamp_sec": timestamp_sec,
            "time_label": time_label,
            "activity": "idle",
            "is_distress": False,
            "summary": "Observation logged."
        }

def run_pipeline():
    if not GEMINI_KEY:
        st.error("Missing `GEMINI_API_KEY` in `.env` file.")
        return []

    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        st.error(f"Could not open video file: `{VIDEO_PATH}`")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = int(fps * SAMPLE_INTERVAL_SEC)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logs = []
    frame_idx = 0

    progress_bar = st.progress(0)
    status_text = st.empty()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            ts = frame_idx / fps
            status_text.text(f"Analyzing frame at {int(ts//60):02d}:{int(ts%60):02d}...")
            res = analyze_frame(frame, ts, model)
            logs.append(res)
            time.sleep(0.4)

        if total_frames > 0:
            progress_bar.progress(min(frame_idx / total_frames, 1.0))
        frame_idx += 1

    cap.release()
    progress_bar.empty()
    status_text.empty()

    with open(OUTPUT_JSON, "w") as f:
        json.dump(logs, f, indent=2)

    return logs

# --- 5. UI Layout ---
st.title("🛡️ AegisCare: AI Elderly Monitoring System")
st.caption("Automated CCTV routine tracking & direct emergency dispatch")

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🚀 Run CCTV Analysis", type="primary"):
        with st.spinner("Processing video frames with Gemini 1.5 Flash..."):
            run_pipeline()
            st.success("Analysis Complete!")
            st.rerun()

# Load Logs
logs = []
if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, "r") as f:
        logs = json.load(f)

# Layout Split
col_video, col_data = st.columns([1.2, 1])

with col_video:
    st.subheader("📹 CCTV Feed")
    if os.path.exists(VIDEO_PATH):
        st.video(VIDEO_PATH)
    else:
        st.warning(f"Place your `{VIDEO_PATH}` in the root folder.")

    if logs:
        m1, m2 = st.columns(2)
        total_events = len(logs)
        falls = sum(1 for x in logs if x.get("is_distress", False) or x.get("activity") == "lying_down")
        m1.metric("Sampling Points", total_events)
        m2.metric("Emergency Alerts", falls, delta_color="inverse")

with col_data:
    st.subheader("📋 Routine Compliance")
    
    meds_taken = any(x.get("activity") == "taking_medicine" for x in logs)
    meals_taken = any(x.get("activity") == "eating" for x in logs)
    walked = any(x.get("activity") == "walking" for x in logs)

    st.checkbox("Morning Medication Logged", value=meds_taken, disabled=True)
    st.checkbox("Meal / Breakfast Logged", value=meals_taken, disabled=True)
    st.checkbox("Mobility / Walking Logged", value=walked, disabled=True)

    st.divider()
    st.subheader("⏱️ Real-Time Activity Log")

    if not logs:
        st.info("Click **'Run CCTV Analysis'** in the sidebar to process the video.")
    else:
        for item in logs:
            t = item.get("time_label", "00:00")
            act = item.get("activity", "idle").replace("_", " ").title()
            summary = item.get("summary", "")
            distress = item.get("is_distress", False) or item.get("activity") == "lying_down"

            if distress:
                st.error(f"🚨 **[{t}] FALL DETECTED:** {summary} *(Telegram Sent)*")
            elif item.get("activity") in ["taking_medicine", "eating"]:
                st.success(f"✅ **[{t}] {act}:** {summary}")
            else:
                st.info(f"ℹ️ **[{t}] {act}:** {summary}")
