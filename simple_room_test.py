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

def register_and_login():
    """Register a new user and login"""
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"test.user{timestamp}@gmail.com"
    password = "Password123!"
    
    # Register
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"Error: Register returned status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return None
    
    register_data = register_response.json()
    
    # Login
    login_data = {
        "username": username,
        "password": password
    }
    
    login_response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"Error: Login returned status code {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return None
    
    login_data = login_response.json()
    
    return {
        "user_id": login_data["user"]["id"],
        "username": username,
        "token": login_data["session"]["access_token"]
    }

def test_room_creation_and_expiry():
    """Test creating a room and verify it has proper expiration time"""
    # Register and login
    user_data = register_and_login()
    if not user_data:
        print("Failed to register and login user")
        return False
    
    # Create a room
    headers = {
        "Authorization": f"Bearer {user_data['token']}"
    }
    
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
    
    # Verify room status is "waiting"
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
    
    print(f"Successfully verified room lifecycle management")
    return True

def run_room_lifecycle_tests():
    """Run room lifecycle tests"""
    print(f"\n{'='*80}\nRevMix Room Lifecycle Management Tests\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Room Lifecycle Test
    run_test("Room Creation and Lifecycle Management", test_room_creation_and_expiry)
    
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