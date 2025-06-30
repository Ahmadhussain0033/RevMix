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

def create_test_room_via_mongodb():
    """Create a test room directly in MongoDB"""
    from pymongo import MongoClient
    import os
    from datetime import datetime, timedelta, timezone
    import uuid
    
    # Connect to MongoDB
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME = os.environ.get('DB_NAME', 'revmix_production')
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    rooms_collection = db.rooms
    
    # Create a test user if needed
    users_collection = db.users
    test_user = users_collection.find_one({"username": "testuser"})
    
    if not test_user:
        test_user = {
            "id": str(uuid.uuid4()),
            "username": "testuser",
            "email": "testuser@example.com",
            "supabase_id": str(uuid.uuid4()),
            "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
            "level": 1,
            "xp": 0,
            "bio": "Test user for room lifecycle testing",
            "badges": ["Tester"],
            "wins": 0,
            "battles": 0,
            "created_at": datetime.now(timezone.utc)
        }
        users_collection.insert_one(test_user)
    
    # Create a test room
    room_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=1)
    
    new_room = {
        "id": room_id,
        "name": f"Test Room {int(time.time())}",
        "host_id": test_user["id"],
        "type": "challenge",
        "prompt": "Test room lifecycle management",
        "participants": [test_user["id"]],
        "status": "waiting",
        "created_at": created_at,
        "expires_at": expires_at,
        "timer_duration": 240,
        "max_participants": 5,
        "results_announced": False,
        "winner_id": None
    }
    
    rooms_collection.insert_one(new_room)
    
    print(f"Created test room with ID: {room_id}")
    print(f"Room created at: {created_at}")
    print(f"Room expires at: {expires_at}")
    
    return room_id

def test_room_lifecycle():
    """Test the room lifecycle management"""
    # Create a test room directly in MongoDB
    room_id = create_test_room_via_mongodb()
    
    # Test 1: Verify room is retrievable by ID
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
    created_at = datetime.fromisoformat(room_data["created_at"].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    # Check if expires_at is approximately 1 hour after created_at
    time_diff = expires_at - created_at
    if abs(time_diff.total_seconds() - 3600) > 60:  # Allow 1 minute tolerance
        print(f"Error: Room expiry time is not 1 hour from creation: {time_diff.total_seconds()} seconds")
        return False
    
    time_until_expiry = expires_at - now
    print(f"Room status: {room_data['status']}")
    print(f"Current time (UTC): {now}")
    print(f"Room created at (UTC): {created_at}")
    print(f"Room expires at (UTC): {expires_at}")
    print(f"Time until expiry: {time_until_expiry.total_seconds()} seconds")
    
    # Test 2: Verify room appears in active rooms list
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
    
    # Test 3: Wait a short time to ensure scheduler has a chance to run
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
    
    return True

def run_room_lifecycle_tests():
    """Run room lifecycle tests"""
    print(f"\n{'='*80}\nRevMix Room Lifecycle Management Tests\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Room Lifecycle Test
    run_test("Room Lifecycle Management", test_room_lifecycle)
    
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