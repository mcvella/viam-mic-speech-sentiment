#!/usr/bin/env python3
"""
Test script for the mic-speech-sentiment module.
This script demonstrates how to use the module programmatically.
"""

import asyncio
import json
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions


async def test_mic_speech_sentiment():
    """Test the mic-speech-sentiment sensor"""
    
    # Connect to your robot
    # Replace with your robot's address and credentials
    robot = await RobotClient.at_address(
        "localhost:8080",  # Replace with your robot's address
        dial_options=DialOptions(
            credentials=Credentials(
                type="robot-location-secret",
                payload="your-secret-here"  # Replace with your robot's secret
            )
        )
    )
    
    try:
        # Get the mic-speech-sentiment sensor
        sensor = robot.get_sensor("mic_speech_sentiment")
        
        print("Testing mic-speech-sentiment sensor...")
        
        # Test 1: Get status
        print("\n1. Getting sensor status...")
        status = await sensor.do_command({"command": "get_status"})
        print(f"Status: {json.dumps(status, indent=2)}")
        
        # Test 2: Get readings (will be empty initially)
        print("\n2. Getting initial readings...")
        readings = await sensor.get_readings()
        print(f"Readings: {json.dumps(readings, indent=2)}")
        
        # Test 3: Start listening
        print("\n3. Starting listening...")
        result = await sensor.do_command({"command": "start_listening"})
        print(f"Start result: {json.dumps(result, indent=2)}")
        
        # Test 4: Wait a bit and check for readings
        print("\n4. Waiting for speech input (speak into microphone)...")
        for i in range(10):  # Wait up to 10 seconds
            await asyncio.sleep(1)
            readings = await sensor.get_readings()
            if readings:
                print(f"Got readings after {i+1} seconds:")
                print(json.dumps(readings, indent=2))
                break
            print(f"  Still waiting... ({i+1}/10)")
        
        # Test 5: Stop listening
        print("\n5. Stopping listening...")
        result = await sensor.do_command({"command": "stop_listening"})
        print(f"Stop result: {json.dumps(result, indent=2)}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        await robot.close()


if __name__ == "__main__":
    print("Mic-Speech-Sentiment Module Test")
    print("=" * 40)
    print("Make sure your robot is running and the module is configured.")
    print("You'll need a microphone connected to test speech input.")
    print()
    
    asyncio.run(test_mic_speech_sentiment())
