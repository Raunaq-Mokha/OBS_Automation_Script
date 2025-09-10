# obs-auto.py
import schedule
import asyncio
import time
from obs_live import OBSController  # uses your original script

# 👇 Customize your schedule here (day, 24h time)
STREAM_SCHEDULE = [
    ("wednesday", "19:00"),
    ("friday", "19:00"),
    ("sunday", "08:30")
]

async def start_stream():
    controller = OBSController(host="localhost", port=4455, password="Oindia001")
    if await controller.connect():
        try:
            await controller.start_streaming()
        finally:
            await controller.disconnect()

def trigger_stream_start():
    print("🚀 Triggering scheduled stream start...")
    asyncio.run(start_stream())

# Register each schedule
for day, time_str in STREAM_SCHEDULE:
    getattr(schedule.every(), day).at(time_str).do(trigger_stream_start)
    print(f"📅 Scheduled: {day.title()} at {time_str}")

# Keep script running
print("🟢 OBS auto-start scheduler running...")
while True:
    schedule.run_pending()
    time.sleep(30)
