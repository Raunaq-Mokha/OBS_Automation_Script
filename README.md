OBS Auto-Streaming Scripts
This project provides Python scripts to automatically control and schedule OBS Studio live streams
using the OBS WebSocket API.
n Project Structure
obs_live.py – Core controller for connecting to OBS WebSocket and sending commands.
Features:
- Start/stop streaming
- Get stream status
- Schedule a one-time stream start/stop at a specific time
- Authentication support (if OBS WebSocket password is enabled)
obs-auto.py – Scheduler wrapper for recurring streams.
Features:
- Define recurring weekly schedules (e.g., Wednesday 19:00, Friday 19:00, Sunday 08:30)
- Automatically triggers obs_live.py to start the stream at scheduled times
- Runs continuously in the background
