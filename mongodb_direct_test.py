import time
import os
import sys
from datetime import datetime, timedelta, timezone
import uuid

def test_room_lifecycle_in_mongodb():
    """Test room lifecycle management directly in MongoDB"""
    from pymongo import MongoClient
    
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
        print(f"Created test user: {test_user['username']}")
    else:
        print(f"Using existing test user: {test_user['username']}")
    
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
    
    # Wait a short time to ensure scheduler has a chance to run
    print("Waiting 10 seconds to allow scheduler to run...")
    time.sleep(10)
    
    # Check room status after waiting
    room = rooms_collection.find_one({"id": room_id})
    
    if not room:
        print(f"Error: Room not found after waiting")
        return False
    
    print(f"Room status after waiting: {room['status']}")
    
    # Verify room is still not closed
    if room["status"] == "closed":
        print(f"Error: Room is marked as closed after waiting")
        return False
    
    # Verify room expiry time is still in the future
    now = datetime.now(timezone.utc)
    time_until_expiry = room["expires_at"] - now
    
    print(f"Current time (UTC): {now}")
    print(f"Room expires at (UTC): {room['expires_at']}")
    print(f"Time until expiry: {time_until_expiry.total_seconds()} seconds")
    
    if time_until_expiry.total_seconds() < 0:
        print(f"Error: Room already expired according to UTC time")
        return False
    
    # Room should expire in less than 1 hour (since we created it earlier)
    if time_until_expiry.total_seconds() > 3600:
        print(f"Error: Room expires more than 1 hour from now")
        return False
    
    print("Room lifecycle test passed!")
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("RevMix Room Lifecycle Management Test (MongoDB Direct)")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    result = test_room_lifecycle_in_mongodb()
    
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80)
    print(f"Room Lifecycle Management: {'PASSED' if result else 'FAILED'}")
    
    sys.exit(0 if result else 1)