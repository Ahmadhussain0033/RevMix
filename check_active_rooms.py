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
    print(f"Current time (UTC): {current_time}")
    
    for room in data["rooms"]:
        expires_at = datetime.fromisoformat(room["expires_at"].replace('Z', '+00:00'))
        created_at = datetime.fromisoformat(room["created_at"].replace('Z', '+00:00'))
        
        # Check if expires_at is approximately 1 hour after created_at
        time_diff = expires_at - created_at
        time_until_expiry = expires_at - current_time
        
        print(f"Room {room['id']} status: {room['status']}")
        print(f"Room {room['id']} created at: {created_at}")
        print(f"Room {room['id']} expires at: {expires_at}")
        print(f"Room {room['id']} creation to expiry: {time_diff.total_seconds()} seconds")
        print(f"Room {room['id']} time until expiry: {time_until_expiry.total_seconds()} seconds")
        print("---")
        
        if expires_at < current_time:
            print(f"Error: Room {room['id']} is expired but still returned in active rooms")
            return False
        
        # Check room status
        if room["status"] == "closed":
            print(f"Error: Room {room['id']} is closed but still returned in active rooms")
            return False
    
    print(f"Successfully retrieved {len(data['rooms'])} active rooms")
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
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Get Active Rooms: {'PASSED' if active_rooms_result else 'FAILED'}")
    
    return active_rooms_result

if __name__ == "__main__":
    success = run_room_lifecycle_tests()
    sys.exit(0 if success else 1)