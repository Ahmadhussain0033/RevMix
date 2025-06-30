import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta, timezone
import uuid

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

# Create a test room directly in MongoDB
def create_test_room():
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

def test_get_room_by_id(room_id):
    """Test getting a specific room by ID"""
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
    
    if expires_at <= now:
        print(f"Error: Room expiry time is not in the future: {expires_at} <= {now}")
        return False
    
    time_until_expiry = expires_at - now
    print(f"Room status: {room_data['status']}")
    print(f"Current time (UTC): {now}")
    print(f"Room created at (UTC): {created_at}")
    print(f"Room expires at (UTC): {expires_at}")
    print(f"Time until expiry: {time_until_expiry.total_seconds()} seconds")
    
    return True

def test_room_appears_in_active_rooms(room_id):
    """Test that newly created room appears in the list of active rooms"""
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

def test_room_not_immediately_expired(room_id):
    """Test that room is not immediately marked as expired"""
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

def run_room_lifecycle_tests():
    """Run room lifecycle tests"""
    print(f"\n{'='*80}\nRevMix Room Lifecycle Management Tests\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create a test room directly in MongoDB
    room_id = create_test_room()
    
    # Room Lifecycle Tests
    print("\n" + "="*80)
    print("Test: Get Room by ID")
    print("="*80)
    get_room_result = test_get_room_by_id(room_id)
    
    print("\n" + "="*80)
    print("Test: Room Appears in Active Rooms")
    print("="*80)
    active_rooms_result = test_room_appears_in_active_rooms(room_id)
    
    print("\n" + "="*80)
    print("Test: Room Not Immediately Expired")
    print("="*80)
    not_expired_result = test_room_not_immediately_expired(room_id)
    
    # Print summary
    print(f"\n{'='*80}\nTest Summary\n{'='*80}")
    print(f"Get Room by ID: {'PASSED' if get_room_result else 'FAILED'}")
    print(f"Room Appears in Active Rooms: {'PASSED' if active_rooms_result else 'FAILED'}")
    print(f"Room Not Immediately Expired: {'PASSED' if not_expired_result else 'FAILED'}")
    
    return get_room_result and active_rooms_result and not_expired_result

if __name__ == "__main__":
    success = run_room_lifecycle_tests()
    sys.exit(0 if success else 1)