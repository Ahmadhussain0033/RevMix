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

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Global variables to store test data
test_users = {}
test_rooms = {}
test_auth_tokens = {}

def run_test(test_name, test_func):
    """Run a test and track results"""
    test_results["total"] += 1
    print(f"\n{'='*80}\nRunning test: {test_name}\n{'='*80}")
    
    try:
        result = test_func()
        if result:
            test_results["passed"] += 1
            test_results["tests"].append({"name": test_name, "status": "PASSED"})
            print(f"✅ Test PASSED: {test_name}")
            return True
        else:
            test_results["failed"] += 1
            test_results["tests"].append({"name": test_name, "status": "FAILED"})
            print(f"❌ Test FAILED: {test_name}")
            return False
    except Exception as e:
        test_results["failed"] += 1
        test_results["tests"].append({"name": test_name, "status": "FAILED", "error": str(e)})
        print(f"❌ Test FAILED with exception: {test_name}")
        print(f"Error: {str(e)}")
        return False

def register_test_user():
    """Register a test user for room creation"""
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"test.user{timestamp}@gmail.com"
    password = "Password123!"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if response.status_code != 200:
        print(f"Error: Register returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    data = response.json()
    
    # Store user data for later tests
    test_users[username] = {
        "id": data["user"]["id"],
        "username": username,
        "email": email,
        "password": password,
        "supabase_id": data["user"]["supabase_id"]
    }
    
    # Store auth token
    test_auth_tokens[username] = data["session"]["access_token"]
    
    print(f"Successfully registered new user: {username}")
    return username

def test_room_creation():
    """Test creating a new room and verify it has proper expiration time"""
    # Register a user if needed
    if not test_auth_tokens:
        username = register_test_user()
        if not username:
            print("Error: Failed to register user for room creation test")
            return False
    else:
        username = list(test_auth_tokens.keys())[0]
    
    token = test_auth_tokens[username]
    user_id = test_users[username]["id"]
    
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
    
    # Store room data for later tests
    test_rooms[new_room["id"]] = {
        "id": new_room["id"],
        "name": new_room["name"],
        "host_id": new_room["host_id"],
        "host_username": username,
        "created_at": new_room["created_at"],
        "expires_at": new_room["expires_at"]
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
    
    return True

def test_room_appears_in_active_rooms():
    """Test that newly created room appears in the list of active rooms"""
    # Create a room if needed
    if not test_rooms:
        if not test_room_creation():
            print("Error: Failed to create room for active rooms test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    
    response = requests.get(f"{API_URL}/rooms")
    
    if response.status_code != 200:
        print(f"Error: Get rooms returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "rooms" not in data or not isinstance(data["rooms"], list):
        print(f"Error: Rooms response invalid: {data}")
        return False
    
    # Check if our room is in the list
    found = False
    for room in data["rooms"]:
        if room["id"] == room_id:
            found = True
            break
    
    if not found:
        print(f"Error: Created room not found in active rooms list")
        return False
    
    print(f"Successfully verified room appears in active rooms list")
    return True

def test_room_retrieval_by_id():
    """Test retrieving a specific room by ID"""
    # Create a room if needed
    if not test_rooms:
        if not test_room_creation():
            print("Error: Failed to create room for retrieval test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    
    response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if response.status_code != 200:
        print(f"Error: Get room by ID returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    room_data = response.json()
    if room_data["id"] != room_id:
        print(f"Error: Retrieved room ID doesn't match requested ID: {room_data}")
        return False
    
    # Verify room is not closed
    if room_data["status"] == "closed":
        print(f"Error: Room is marked as closed immediately after creation")
        return False
    
    # Verify expires_at is in the future
    expires_at = datetime.fromisoformat(room_data["expires_at"].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    if expires_at <= now:
        print(f"Error: Room expiry time is not in the future: {expires_at} <= {now}")
        return False
    
    time_until_expiry = expires_at - now
    print(f"Room status: {room_data['status']}")
    print(f"Current time (UTC): {now}")
    print(f"Room expires at (UTC): {expires_at}")
    print(f"Time until expiry: {time_until_expiry.total_seconds()} seconds")
    
    return True

def test_room_not_immediately_expired():
    """Test that room is not immediately marked as expired"""
    # Create a room if needed
    if not test_rooms:
        if not test_room_creation():
            print("Error: Failed to create room for expiration test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    
    # Wait a short time to ensure scheduler has a chance to run
    print("Waiting 10 seconds to allow scheduler to run...")
    time.sleep(10)
    
    # Check room status again
    response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if response.status_code != 200:
        print(f"Error: Get room after wait returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    room_data = response.json()
    
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
    
    return True

def test_timezone_consistency():
    """Test that timezone handling is consistent between room creation and cleanup"""
    # Create a room if needed
    if not test_rooms:
        if not test_room_creation():
            print("Error: Failed to create room for timezone test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    room_data = test_rooms[room_id]
    
    # Get the current room data
    response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if response.status_code != 200:
        print(f"Error: Get room returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    current_room_data = response.json()
    
    # Check that created_at and expires_at have timezone information (UTC)
    created_at_str = current_room_data["created_at"]
    expires_at_str = current_room_data["expires_at"]
    
    # Verify these are valid ISO format with timezone info
    try:
        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
    except ValueError as e:
        print(f"Error: Invalid datetime format: {e}")
        print(f"created_at: {created_at_str}")
        print(f"expires_at: {expires_at_str}")
        return False
    
    # Verify the timezone is UTC
    now_utc = datetime.now(timezone.utc)
    time_diff = expires_at - now_utc
    
    print(f"Current time (UTC): {now_utc}")
    print(f"Room created at: {created_at}")
    print(f"Room expires at: {expires_at}")
    print(f"Time until expiry: {time_diff.total_seconds()} seconds")
    
    # Room should expire in the future (close to 1 hour from creation)
    if time_diff.total_seconds() < 0:
        print(f"Error: Room already expired according to UTC time")
        return False
    
    # Room should expire in less than 1 hour (since we created it earlier)
    if time_diff.total_seconds() > 3600:
        print(f"Error: Room expires more than 1 hour from now")
        return False
    
    return True

def run_room_lifecycle_tests():
    """Run all room lifecycle tests"""
    print(f"\n{'='*80}\nRevMix Room Lifecycle Management Tests\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Room Lifecycle Tests
    run_test("Room Creation with 1-hour Expiry", test_room_creation)
    run_test("Room Appears in Active Rooms List", test_room_appears_in_active_rooms)
    run_test("Room Retrieval by ID", test_room_retrieval_by_id)
    run_test("Room Not Immediately Expired", test_room_not_immediately_expired)
    run_test("Timezone Consistency", test_timezone_consistency)
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success rate: {(test_results['passed'] / test_results['total']) * 100:.2f}%")
    
    if test_results['failed'] > 0:
        print("\nFailed tests:")
        for test in test_results['tests']:
            if test['status'] == 'FAILED':
                print(f"- {test['name']}")
                if 'error' in test:
                    print(f"  Error: {test['error']}")
    
    return test_results['failed'] == 0

if __name__ == "__main__":
    success = run_room_lifecycle_tests()
    sys.exit(0 if success else 1)