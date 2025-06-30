import sys
import os
import time
from datetime import datetime, timezone

# Run only the room creation test from the main backend_test.py
sys.path.append('/app')
from backend_test import (
    API_URL,
    test_register_new_user,
    test_login_user,
    test_users,
    test_auth_tokens,
    test_rooms
)

def test_create_room_and_verify_lifecycle():
    """Test creating a room and verify it's not immediately expired"""
    # Register and login a user
    if not test_register_new_user():
        print("Error: Failed to register user for room creation test")
        return False
    
    if not test_login_user():
        print("Error: Failed to login user for room creation test")
        return False
    
    # Get user credentials
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    user_id = test_users[username]["id"]
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a room
    room_data = {
        "name": f"Lifecycle Test Room {int(time.time())}",
        "type": "challenge",
        "prompt": "Test room lifecycle management",
        "timer_duration": 240,
        "max_participants": 5
    }
    
    response = requests.post(f"{API_URL}/rooms", json=room_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Create room returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    new_room = response.json()
    room_id = new_room["id"]
    
    # Store room data for later tests
    test_rooms[room_id] = {
        "id": room_id,
        "name": new_room["name"],
        "host_id": new_room["host_id"],
        "host_username": username
    }
    
    # Verify room properties
    if new_room["status"] != "waiting":
        print(f"Error: Room status should be 'waiting', got '{new_room['status']}'")
        return False
    
    # Check for 1-hour expiry
    created_at = datetime.fromisoformat(new_room["created_at"].replace('Z', '+00:00'))
    expires_at = datetime.fromisoformat(new_room["expires_at"].replace('Z', '+00:00'))
    
    # Check if expires_at is approximately 1 hour after created_at
    time_diff = expires_at - created_at
    if abs(time_diff.total_seconds() - 3600) > 60:  # Allow 1 minute tolerance
        print(f"Error: Room expiry time is not 1 hour from creation: {time_diff.total_seconds()} seconds")
        return False
    
    print(f"Successfully created room: {new_room['name']} with ID: {new_room['id']}")
    print(f"Room created at: {created_at}")
    print(f"Room expires at: {expires_at}")
    print(f"Time difference: {time_diff.total_seconds()} seconds (should be ~3600)")
    
    # Verify room appears in active rooms list
    rooms_response = requests.get(f"{API_URL}/rooms")
    
    if rooms_response.status_code != 200:
        print(f"Error: Get rooms returned status code {rooms_response.status_code}")
        print(f"Response: {rooms_response.text}")
        return False
    
    rooms_data = rooms_response.json()
    
    # Check if our room is in the list
    found = False
    for room in rooms_data["rooms"]:
        if room["id"] == room_id:
            found = True
            break
    
    if not found:
        print(f"Error: Created room not found in active rooms list")
        return False
    
    print(f"Successfully verified room appears in active rooms list")
    
    # Wait a short time to ensure scheduler has a chance to run
    print("Waiting 10 seconds to allow scheduler to run...")
    time.sleep(10)
    
    # Check room status again
    room_response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if room_response.status_code != 200:
        print(f"Error: Get room after wait returned status code {room_response.status_code}")
        print(f"Response: {room_response.text}")
        return False
    
    room_data = room_response.json()
    
    # Verify room is still not closed
    if room_data["status"] == "closed":
        print(f"Error: Room is marked as closed after waiting")
        return False
    
    # Verify room still appears in active rooms list
    rooms_response = requests.get(f"{API_URL}/rooms")
    
    if rooms_response.status_code != 200:
        print(f"Error: Get rooms after wait returned status code {rooms_response.status_code}")
        print(f"Response: {rooms_response.text}")
        return False
    
    rooms_data = rooms_response.json()
    
    # Check if our room is still in the list
    found = False
    for room in rooms_data["rooms"]:
        if room["id"] == room_id:
            found = True
            break
    
    if not found:
        print(f"Error: Room not found in active rooms list after waiting")
        return False
    
    print(f"Successfully verified room is not immediately expired")
    print(f"Room status after waiting: {room_data['status']}")
    
    # Check timezone consistency
    now_utc = datetime.now(timezone.utc)
    time_until_expiry = expires_at - now_utc
    
    print(f"Current time (UTC): {now_utc}")
    print(f"Room expires at (UTC): {expires_at}")
    print(f"Time until expiry: {time_until_expiry.total_seconds()} seconds")
    
    # Room should expire in the future (close to 1 hour from creation)
    if time_until_expiry.total_seconds() < 0:
        print(f"Error: Room already expired according to UTC time")
        return False
    
    # Room should expire in less than 1 hour (since we created it earlier)
    if time_until_expiry.total_seconds() > 3600:
        print(f"Error: Room expires more than 1 hour from now")
        return False
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RevMix Room Lifecycle Management Test")
    print("="*80)
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    result = test_create_room_and_verify_lifecycle()
    
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"Room Lifecycle Management: {'PASSED' if result else 'FAILED'}")
    
    sys.exit(0 if result else 1)