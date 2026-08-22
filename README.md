# AEGIS — Smart CCTV Safety Monitor

Real-time fall detection and restricted-perimeter intrusion alerts using
YOLOv8-Pose, built with Streamlit.

## ⚠️ Before you push this to GitHub

The original version of this app had a **Telegram bot token and chat ID
hardcoded in the source file**. That has been removed. Credentials are now
loaded from Streamlit secrets / environment variables and are never stored
in the repo. If you ever pasted real credentials into `app.py` in a
previous commit, **rotate that bot token** (message `@BotFather` on
Telegram → `/revoke`) before making the repo public — old commits still
contain it in git history even after you edit the file.

## Why not Vercel

Vercel runs serverless functions and static frontends — it can't host a
long-running Streamlit process with WebSocket support, which this app
needs. It also can't help with `cv2.VideoCapture(0)`: that opens a webcam
*attached to the server*, and cloud servers don't have one. That's why
live mode now captures video **in the visitor's browser** via
`streamlit-webrtc` and streams it to the app for processing — this works
locally and in the cloud, with no server-side camera required.

Recommended hosts instead: **Streamlit Community Cloud** (free, easiest),
**Hugging Face Spaces**, or **Render/Railway**.

## Local setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml with your real bot token + chat id (optional)

streamlit run app.py
```

The YOLO pose model (`yolov8n-pose.pt`) downloads automatically on first
run — no need to commit the weights file.

## Deploying to Streamlit Community Cloud

1. Push this folder to a GitHub repo (`.streamlit/secrets.toml` is
   gitignored, so your real credentials won't be included — only
   `secrets.toml.example` will).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and pick this repo + `app.py` as the entry point.
3. In **App settings → Secrets**, paste:
   ```toml
   TELEGRAM_BOT_TOKEN = "your-real-token"
   TELEGRAM_CHAT_ID = "your-real-chat-id"
   ```
4. Deploy. `packages.txt` installs the system libraries OpenCV/av need
   (`libgl1`, `ffmpeg`, etc.) automatically — no extra setup required.

Telegram alerts are optional: if no secrets are set, the app runs fine
and just shows detections on-screen with alerts disabled.

## Features

- **Fall detection** — pose-based (shoulder/hip collapse) + bounding-box
  aspect ratio, catches falls a simple box check alone would miss.
- **Restricted-zone intrusion detection** — configurable zone overlay.
- **Browser-based live webcam** via WebRTC — works locally and deployed.
- **Upload-and-analyze** mode for recorded clips (.mp4/.avi/.mov).
- **Debounced Telegram alerts** so a fall/intrusion doesn't spam your
  phone every frame.
- Adjustable AI sensitivity and alert cooldown from the sidebar.
- Graceful handling of a missing/broken model file, failed Telegram
  sends, and unreadable video files — the app tells you what went wrong
  instead of crashing.

## Notes / limitations

- The restricted zone is currently a fixed rectangle (60–95% width,
  10–60% height of the frame). Consider exposing this as a sidebar
  control if you need it adjustable per camera.
- Fall/intrusion counters reset per browser session (Streamlit's
  `session_state`), not persisted to a database — add one if you need
  historical logging across sessions.
- This is a demo/prototype-grade safety tool, not a certified medical or
  security device — validate carefully before relying on it for real
  monitoring.
