#!/usr/bin/env python3
"""
OBS Studio Stream Control Script
Connects to OBS via WebSocket to start/stop streaming
"""

import asyncio
import json
import websockets
import hashlib
import base64
import argparse
from datetime import datetime, timedelta
import time

class OBSController:
    def __init__(self, host="localhost", port=4455, password=None):
        self.host = host
        self.port = port
        self.password = password
        self.websocket = None
        
    async def connect(self):
        """Connect to OBS WebSocket server"""
        uri = f"ws://{self.host}:{self.port}"
        try:
            self.websocket = await websockets.connect(uri)
            print(f"Connected to OBS at {uri}")
            
            # Wait for Hello message from OBS
            hello_message = await self.websocket.recv()
            hello_data = json.loads(hello_message)
            print(f"Received Hello message")
            
            # Send Identify message with authentication
            await self._send_identify(hello_data)
            
            # Wait for Identified message
            identified_message = await self.websocket.recv()
            identified_data = json.loads(identified_message)
            
            if identified_data["op"] == 2:  # Identified
                print("✅ Successfully identified with OBS")
                return True
            else:
                print(f"❌ Failed to identify: {identified_data}")
                return False
                
        except ConnectionRefusedError:
            print("Error: Could not connect to OBS WebSocket server")
            print("Make sure OBS is running and WebSocket server is enabled")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    async def _send_identify(self, hello_data):
        """Send Identify message with authentication if required"""
        identify_message = {
            "op": 1,
            "d": {
                "rpcVersion": 1
            }
        }
        
        # Check if authentication is required
        if "authentication" in hello_data["d"]:
            auth_data = hello_data["d"]["authentication"]
            challenge = auth_data["challenge"]
            salt = auth_data["salt"]
            
            if self.password:
                # Generate authentication string
                secret = base64.b64encode(
                    hashlib.sha256((self.password + salt).encode()).digest()
                ).decode()
                
                auth_response = base64.b64encode(
                    hashlib.sha256((secret + challenge).encode()).digest()
                ).decode()
                
                identify_message["d"]["authentication"] = auth_response
                print("🔐 Authentication included in Identify message")
            else:
                print("❌ Authentication required but no password provided")
                raise Exception("Authentication required but no password provided")
        else:
            print("ℹ️ No authentication required")
        
        await self.websocket.send(json.dumps(identify_message))
    
    async def start_streaming(self):
        """Start streaming in OBS"""
        request = {
            "op": 6,
            "d": {
                "requestType": "StartStream",
                "requestId": "start-stream"
            }
        }
        
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        result = json.loads(response)
        
        if result["d"]["requestStatus"]["result"]:
            print("✅ Streaming started successfully!")
        else:
            print(f"❌ Failed to start streaming: {result['d']['requestStatus']['comment']}")
    
    async def stop_streaming(self):
        """Stop streaming in OBS"""
        request = {
            "op": 6,
            "d": {
                "requestType": "StopStream",
                "requestId": "stop-stream"
            }
        }
        
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        result = json.loads(response)
        
        if result["d"]["requestStatus"]["result"]:
            print("✅ Streaming stopped successfully!")
        else:
            print(f"❌ Failed to stop streaming: {result['d']['requestStatus']['comment']}")
    
    async def get_stream_status(self):
        """Get current streaming status"""
        request = {
            "op": 6,
            "d": {
                "requestType": "GetStreamStatus",
                "requestId": "get-stream-status"
            }
        }
        
        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        result = json.loads(response)
        
        if result["d"]["requestStatus"]["result"]:
            status = result["d"]["responseData"]
            if status["outputActive"]:
                print(f"🔴 Currently streaming")
                print(f"   Duration: {status['outputDuration']}ms")
                print(f"   Bytes sent: {status['outputBytes']}")
            else:
                print("⚫ Not currently streaming")
        else:
            print(f"❌ Failed to get stream status: {result['d']['requestStatus']['comment']}")
    
    async def schedule_stream(self, start_time, duration_minutes=None):
        """Schedule streaming to start at a specific time"""
        try:
            # Parse the time
            target_time = datetime.strptime(start_time, "%H:%M").replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
            
            # If time has passed today, schedule for tomorrow
            if target_time <= datetime.now():
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - datetime.now()).total_seconds()
            
            print(f"⏰ Stream scheduled for {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏳ Waiting {int(wait_seconds)} seconds...")
            
            # Wait until scheduled time
            await asyncio.sleep(wait_seconds)
            
            print("🚀 Starting scheduled stream...")
            await self.start_streaming()
            
            # If duration is specified, schedule stop
            if duration_minutes:
                print(f"⏰ Stream will stop automatically in {duration_minutes} minutes")
                await asyncio.sleep(duration_minutes * 60)
                print("⏹️ Stopping scheduled stream...")
                await self.stop_streaming()
                
        except ValueError:
            print("❌ Invalid time format. Use HH:MM (24-hour format)")
        except Exception as e:
            print(f"❌ Scheduling error: {e}")

    async def disconnect(self):
        """Disconnect from OBS WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from OBS")

async def main():
    parser = argparse.ArgumentParser(description="Control OBS Studio streaming")
    parser.add_argument("action", choices=["start", "stop", "status", "schedule"], 
                       help="Action to perform")
    parser.add_argument("--host", default="localhost", 
                       help="OBS WebSocket host (default: localhost)")
    parser.add_argument("--port", type=int, default=4455, 
                       help="OBS WebSocket port (default: 4455)")
    parser.add_argument("--password", 
                       help="OBS WebSocket password (if authentication is enabled)")
    parser.add_argument("--time", 
                       help="Schedule time in HH:MM format (24-hour)")
    parser.add_argument("--duration", type=int,
                       help="Stream duration in minutes (optional)")
    
    args = parser.parse_args()
    
    controller = OBSController(args.host, args.port, args.password)
    
    if await controller.connect():
        try:
            if args.action == "start":
                await controller.start_streaming()
            elif args.action == "stop":
                await controller.stop_streaming()
            elif args.action == "status":
                await controller.get_stream_status()
            elif args.action == "schedule":
                if not args.time:
                    print("❌ --time required for schedule action")
                    return
                await controller.schedule_stream(args.time, args.duration)
        finally:
            await controller.disconnect()

if __name__ == "__main__":
    asyncio.run(main())