import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta, timezone

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

# Ensure the backend URL is set
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in frontend/.env")
    sys.exit(1)

# Add /api prefix to all endpoints
API_URL = f"{BACKEND_URL}/api"

print(f"Testing room lifecycle management at: {API_URL}")

def test_get_active_rooms():
    """Test getting all active rooms and verify they are not expired"""
    response = requests.get(f"{API_URL}/rooms")
    
    if response.status_code != 200:
        print(f"Error: Get rooms returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "rooms" not in data or not isinstance(data["rooms"], list):
        print(f"Error: Rooms response invalid: {data}")
        return False
    
    # Check that all rooms have expires_at in the future
    current_time = datetime.now(timezone.utc)
    for room in data["rooms"]:
        expires_at = datetime.fromisoformat(room["expires_at"].replace('Z', '+00:00'))
        if expires_at < current_time:
            print(f"Error: Room {room['id']} is expired but still returned in active rooms")
            return False
        
        # Check room status
        if room["status"] == "closed":
            print(f"Error: Room {room['id']} is closed but still returned in active rooms")
            return False
        
        # Calculate time until expiry
        time_until_expiry = expires_at - current_time
        print(f"Room {room['id']} expires in {time_until_expiry.total_seconds()} seconds")
    
    print(f"Successfully retrieved {len(data['rooms'])} active rooms")
    return True

def test_room_expiry_times():
    """Test that room expiry times are correctly set in UTC timezone"""
    response = requests.get(f"{API_URL}/rooms")
    
    if response.status_code != 200:
        print(f"Error: Get rooms returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "rooms" not in data or not isinstance(data["rooms"], list):
        print(f"Error: Rooms response invalid: {data}")
        return False
    
    if len(data["rooms"]) == 0:
        print("No active rooms found to test expiry times")
        return True
    
    # Check the expiry times of all rooms
    current_time = datetime.now(timezone.utc)
    print(f"Current time (UTC): {current_time}")
    
    for room in data["rooms"]:
        created_at = datetime.fromisoformat(room["created_at"].replace('Z', '+00:00'))
        expires_at = datetime.fromisoformat(room["expires_at"].replace('Z', '+00:00'))
        
        # Check if expires_at is approximately 1 hour after created_at
        time_diff = expires_at - created_at
        if abs(time_diff.total_seconds() - 3600) > 60:  # Allow 1 minute tolerance
            print(f"Error: Room {room['id']} expiry time is not 1 hour from creation: {time_diff.total_seconds()} seconds")
            return False
        
        # Check if room is still active
        time_until_expiry = expires_at - current_time
        print(f"Room {room['id']} created at {created_at}")
        print(f"Room {room['id']} expires at {expires_at}")
        print(f"Room {room['id']} expires in {time_until_expiry.total_seconds()} seconds")
        print(f"Room {room['id']} status: {room['status']}")
        print("---")
    
    print("All room expiry times are correctly set to 1 hour after creation")
    return True

def run_room_lifecycle_tests():
    """Run room lifecycle tests"""
    print(f"\n{'='*80}\nRevMix Room Lifecycle Management Tests\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Room Lifecycle Tests
    print("\n" + "="*80)
    print("Test: Get Active Rooms")
    print("="*80)
    active_rooms_result = test_get_active_rooms()
    
    print("\n" + "="*80)
    print("Test: Room Expiry Times")
    print("="*80)
    expiry_times_result = test_room_expiry_times()
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Get Active Rooms: {'PASSED' if active_rooms_result else 'FAILED'}")
    print(f"Room Expiry Times: {'PASSED' if expiry_times_result else 'FAILED'}")
    
    return active_rooms_result and expiry_times_result

if __name__ == "__main__":
    success = run_room_lifecycle_tests()
    sys.exit(0 if success else 1)