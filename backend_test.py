import requests
import json
import base64
import time
import os
import sys
from datetime import datetime, timedelta

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

print(f"Testing backend API at: {API_URL}")

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
test_performances = {}
test_votes = {}
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

def test_api_root():
    """Test the API root endpoint"""
    response = requests.get(f"{API_URL}/")
    if response.status_code != 200:
        print(f"Error: API root returned status code {response.status_code}")
        return False
    
    data = response.json()
    if "message" not in data or "RevMix API is running" not in data["message"]:
        print(f"Error: Unexpected response from API root: {data}")
        return False
    
    print("API root endpoint is working correctly")
    return True

# Authentication Tests with Supabase
def test_register_new_user():
    """Test registering a new user with Supabase auth"""
    # Generate a unique username and email
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    email = f"test_{timestamp}@example.com"
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
        return False
    
    data = response.json()
    if "user" not in data or "session" not in data:
        print(f"Error: Register response missing user or session: {data}")
        return False
    
    if data["user"]["username"] != username:
        print(f"Error: Register returned wrong username: {data['user']['username']}")
        return False
    
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
    return True

def test_login_user():
    """Test logging in with a registered user"""
    # Use the user we just registered
    if not test_users:
        if not test_register_new_user():
            print("Error: Failed to register user for login test")
            return False
    
    username = list(test_users.keys())[0]
    password = test_users[username]["password"]
    
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print(f"Error: Login returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "user" not in data or "session" not in data:
        print(f"Error: Login response missing user or session: {data}")
        return False
    
    if data["user"]["username"] != username:
        print(f"Error: Login returned wrong username: {data['user']['username']}")
        return False
    
    # Update auth token
    test_auth_tokens[username] = data["session"]["access_token"]
    
    print(f"Successfully logged in as user: {username}")
    return True

def test_logout_user():
    """Test logging out a user"""
    # Use the user we just logged in
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for logout test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post(f"{API_URL}/auth/logout", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Logout returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "message" not in data or "Logged out successfully" not in data["message"]:
        print(f"Error: Unexpected logout response: {data}")
        return False
    
    print(f"Successfully logged out user: {username}")
    return True

def test_register_duplicate_username():
    """Test that registering with an existing username fails"""
    # Use the username we already registered
    if not test_users:
        if not test_register_new_user():
            print("Error: Failed to register user for duplicate test")
            return False
    
    username = list(test_users.keys())[0]
    
    # Try to register with the same username but different email
    register_data = {
        "username": username,
        "email": f"different_{int(time.time())}@example.com",
        "password": "Password123!"
    }
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    # This should fail with a 400 status code
    if response.status_code != 400:
        print(f"Error: Duplicate username registration should fail, got status code {response.status_code}")
        return False
    
    print("Successfully verified duplicate username registration is rejected")
    return True

def test_get_current_user():
    """Test getting the current user profile with auth token"""
    # Register and login a new user if needed
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for current user test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Get current user returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    user_data = response.json()
    if user_data["username"] != username:
        print(f"Error: Current user data doesn't match expected user: {user_data}")
        return False
    
    print(f"Successfully retrieved current user profile for: {user_data['username']}")
    return True

def test_get_user_profile():
    """Test getting a user profile by ID"""
    # Use a user we've already registered
    if not test_users:
        if not test_register_new_user():
            print("Error: Failed to register user for profile test")
            return False
    
    username = list(test_users.keys())[0]
    user_id = test_users[username]["id"]
    
    response = requests.get(f"{API_URL}/users/profile/{user_id}")
    
    if response.status_code != 200:
        print(f"Error: Get profile returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    profile_data = response.json()
    if profile_data["id"] != user_id or profile_data["username"] != username:
        print(f"Error: Profile data doesn't match expected user: {profile_data}")
        return False
    
    # Check for XP and badges
    if "xp" not in profile_data or "badges" not in profile_data:
        print(f"Error: Profile missing XP or badges: {profile_data}")
        return False
    
    print(f"Successfully retrieved user profile for: {profile_data['username']}")
    return True

def test_get_leaderboard():
    """Test getting the leaderboard"""
    response = requests.get(f"{API_URL}/users/leaderboard")
    
    if response.status_code != 200:
        print(f"Error: Leaderboard returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "leaderboard" not in data or not isinstance(data["leaderboard"], list):
        print(f"Error: Leaderboard response invalid: {data}")
        return False
    
    # Check if leaderboard is sorted by XP (descending)
    leaderboard = data["leaderboard"]
    if len(leaderboard) > 1:
        is_sorted = all(leaderboard[i]["xp"] >= leaderboard[i+1]["xp"] for i in range(len(leaderboard)-1))
        if not is_sorted:
            print(f"Error: Leaderboard is not sorted by XP (descending)")
            return False
    
    print(f"Successfully retrieved leaderboard with {len(leaderboard)} users")
    return True

# Room Tests
def test_create_room():
    """Test creating a new room with 1-hour expiry"""
    # Login a user if needed
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for room creation test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    user_id = test_users[username]["id"]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a room
    room_data = {
        "name": f"Test Room {int(time.time())}",
        "type": "challenge",
        "prompt": "Test your skills in this room!",
        "timer_duration": 240,
        "max_participants": 5
    }
    
    response = requests.post(f"{API_URL}/rooms", json=room_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Create room returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    new_room = response.json()
    if new_room["name"] != room_data["name"] or new_room["host_id"] != user_id:
        print(f"Error: Created room data doesn't match input: {new_room}")
        return False
    
    # Check for 1-hour expiry
    created_at = datetime.fromisoformat(new_room["created_at"].replace('Z', '+00:00'))
    expires_at = datetime.fromisoformat(new_room["expires_at"].replace('Z', '+00:00'))
    
    # Check if expires_at is approximately 1 hour after created_at
    time_diff = expires_at - created_at
    if abs(time_diff.total_seconds() - 3600) > 60:  # Allow 1 minute tolerance
        print(f"Error: Room expiry time is not 1 hour from creation: {time_diff.total_seconds()} seconds")
        return False
    
    # Store room data for later tests
    test_rooms[new_room["id"]] = {
        "id": new_room["id"],
        "name": new_room["name"],
        "host_id": new_room["host_id"],
        "host_username": username
    }
    
    print(f"Successfully created room: {new_room['name']} with ID: {new_room['id']} and 1-hour expiry")
    return True

def test_get_rooms():
    """Test getting all active rooms (not expired)"""
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
    current_time = datetime.now()
    for room in data["rooms"]:
        expires_at = datetime.fromisoformat(room["expires_at"].replace('Z', '+00:00'))
        if expires_at < current_time:
            print(f"Error: Room {room['id']} is expired but still returned in active rooms")
            return False
    
    print(f"Successfully retrieved {len(data['rooms'])} active rooms")
    return True

def test_get_room_by_id():
    """Test getting a specific room by ID"""
    # Create a room if needed
    if not test_rooms:
        if not test_create_room():
            print("Error: Failed to create room for get_room_by_id test")
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
    
    print(f"Successfully retrieved room: {room_data['name']}")
    return True

def test_join_room():
    """Test joining a room"""
    # Create a room if needed
    if not test_rooms:
        if not test_create_room():
            print("Error: Failed to create room for join room test")
            return False
    
    # Register a second user
    timestamp = int(time.time())
    username = f"joiner_{timestamp}"
    email = f"joiner_{timestamp}@example.com"
    password = "Password123!"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"Error: Register joiner returned status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    joiner_data = register_response.json()
    joiner_token = joiner_data["session"]["access_token"]
    
    # Store user data
    test_users[username] = {
        "id": joiner_data["user"]["id"],
        "username": username,
        "email": email,
        "password": password,
        "supabase_id": joiner_data["user"]["supabase_id"]
    }
    test_auth_tokens[username] = joiner_token
    
    # Join the room
    room_id = list(test_rooms.keys())[0]
    
    headers = {
        "Authorization": f"Bearer {joiner_token}"
    }
    
    join_response = requests.post(f"{API_URL}/rooms/{room_id}/join", headers=headers)
    
    if join_response.status_code != 200:
        print(f"Error: Join room returned status code {join_response.status_code}")
        print(f"Response: {join_response.text}")
        return False
    
    # Verify the user was added to the room
    room_response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if room_response.status_code != 200:
        print(f"Error: Get room after join returned status code {room_response.status_code}")
        print(f"Response: {room_response.text}")
        return False
    
    room_data = room_response.json()
    if joiner_data["user"]["id"] not in room_data["participants"]:
        print(f"Error: Joiner ID not found in room participants: {room_data}")
        return False
    
    print(f"Successfully joined room: {room_data['name']}")
    return True

def test_room_results():
    """Test getting room results"""
    # Create a room if needed
    if not test_rooms:
        if not test_create_room():
            print("Error: Failed to create room for room results test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    
    response = requests.get(f"{API_URL}/rooms/{room_id}/results")
    
    if response.status_code != 200:
        print(f"Error: Get room results returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "room" not in data or "performances" not in data:
        print(f"Error: Room results response invalid: {data}")
        return False
    
    if data["room"]["id"] != room_id:
        print(f"Error: Room results ID doesn't match requested ID: {data}")
        return False
    
    print(f"Successfully retrieved results for room: {data['room']['name']}")
    return True

def test_close_room():
    """Test closing a room (host only)"""
    # Create a room if needed
    if not test_rooms:
        if not test_create_room():
            print("Error: Failed to create room for close room test")
            return False
    
    room_id = list(test_rooms.keys())[0]
    host_username = test_rooms[room_id]["host_username"]
    host_token = test_auth_tokens[host_username]
    
    headers = {
        "Authorization": f"Bearer {host_token}"
    }
    
    response = requests.post(f"{API_URL}/rooms/{room_id}/close", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Close room returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Verify the room is closed
    room_response = requests.get(f"{API_URL}/rooms/{room_id}")
    
    if room_response.status_code != 200:
        print(f"Error: Get room after close returned status code {room_response.status_code}")
        print(f"Response: {room_response.text}")
        return False
    
    room_data = room_response.json()
    if room_data["status"] != "closed":
        print(f"Error: Room status is not 'closed' after closing: {room_data}")
        return False
    
    print(f"Successfully closed room: {room_data['name']}")
    return True

# Performance Tests
def test_submit_performance_with_timeline():
    """Test submitting a performance with audio timeline data"""
    # Create a room if needed
    if not test_rooms:
        if not test_create_room():
            print("Error: Failed to create room for performance test")
            return False
    
    # Login a user if needed
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for performance test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    user_id = test_users[username]["id"]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    room_id = list(test_rooms.keys())[0]
    
    # Create a mock audio data (base64 encoded string)
    mock_audio = base64.b64encode(b"This is a mock audio file for testing").decode('utf-8')
    
    # Create audio timeline data
    audio_timeline = [
        {
            "id": "track1",
            "type": "main",
            "start": 0,
            "end": 60.5,
            "volume": 1.0
        },
        {
            "id": "effect1",
            "type": "effect",
            "start": 15.2,
            "end": 16.5,
            "volume": 0.8
        },
        {
            "id": "effect2",
            "type": "effect",
            "start": 45.0,
            "end": 46.0,
            "volume": 0.7
        }
    ]
    
    # Submit a performance
    performance_data = {
        "room_id": room_id,
        "audio_data": mock_audio,
        "duration": 60.5,
        "timeline_marks": [10.2, 25.7, 45.1],
        "audio_timeline": audio_timeline
    }
    
    response = requests.post(f"{API_URL}/performances", json=performance_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Submit performance returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    new_performance = response.json()
    if new_performance["user_id"] != user_id or new_performance["room_id"] != room_id:
        print(f"Error: Performance data doesn't match input: {new_performance}")
        return False
    
    # Check if audio timeline was saved
    if "audio_timeline" not in new_performance or len(new_performance["audio_timeline"]) != len(audio_timeline):
        print(f"Error: Audio timeline not saved correctly: {new_performance}")
        return False
    
    # Store performance data for later tests
    test_performances[new_performance["id"]] = {
        "id": new_performance["id"],
        "user_id": new_performance["user_id"],
        "username": username,
        "room_id": room_id
    }
    
    print(f"Successfully submitted performance with ID: {new_performance['id']} and audio timeline")
    return True

def test_get_room_performances():
    """Test getting performances for a room"""
    # Submit a performance if needed
    if not test_performances:
        if not test_submit_performance_with_timeline():
            print("Error: Failed to submit performance for get_room_performances test")
            return False
    
    performance = list(test_performances.values())[0]
    room_id = performance["room_id"]
    
    response = requests.get(f"{API_URL}/performances/room/{room_id}")
    
    if response.status_code != 200:
        print(f"Error: Get room performances returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "performances" not in data or not isinstance(data["performances"], list):
        print(f"Error: Performances response invalid: {data}")
        return False
    
    # Check if our performance is in the list
    found = False
    for perf in data["performances"]:
        if perf["id"] == performance["id"]:
            found = True
            break
    
    if not found:
        print(f"Error: Submitted performance not found in room performances")
        return False
    
    print(f"Successfully retrieved {len(data['performances'])} performances for room")
    return True

# Voting Tests
def test_submit_vote():
    """Test submitting a vote for a performance"""
    # Submit a performance if needed
    if not test_performances:
        if not test_submit_performance_with_timeline():
            print("Error: Failed to submit performance for vote test")
            return False
    
    # Register a second user for voting
    timestamp = int(time.time())
    username = f"voter_{timestamp}"
    email = f"voter_{timestamp}@example.com"
    password = "Password123!"
    
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        print(f"Error: Register voter returned status code {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    voter_data = register_response.json()
    voter_token = voter_data["session"]["access_token"]
    voter_id = voter_data["user"]["id"]
    
    # Store user data
    test_users[username] = {
        "id": voter_id,
        "username": username,
        "email": email,
        "password": password,
        "supabase_id": voter_data["user"]["supabase_id"]
    }
    test_auth_tokens[username] = voter_token
    
    # Get performance to vote on
    performance = list(test_performances.values())[0]
    performance_id = performance["id"]
    room_id = performance["room_id"]
    
    headers = {
        "Authorization": f"Bearer {voter_token}"
    }
    
    # Submit a vote
    vote_data = {
        "performance_id": performance_id,
        "room_id": room_id,
        "flow": 8,
        "lyrics": 9,
        "creativity": 7,
        "emoji_reaction": "🔥"
    }
    
    response = requests.post(f"{API_URL}/votes", json=vote_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Submit vote returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    vote = response.json()
    if vote["voter_id"] != voter_id or vote["performance_id"] != performance_id:
        print(f"Error: Vote data doesn't match input: {vote}")
        return False
    
    # Store vote data for later tests
    test_votes[vote["id"]] = {
        "id": vote["id"],
        "voter_id": voter_id,
        "voter_username": username,
        "performance_id": performance_id
    }
    
    # Verify the vote was recorded in the performance
    performances_response = requests.get(f"{API_URL}/performances/room/{room_id}")
    
    if performances_response.status_code != 200:
        print(f"Error: Get performances after vote returned status code {performances_response.status_code}")
        print(f"Response: {performances_response.text}")
        return False
    
    performances = performances_response.json()["performances"]
    performance_obj = next((p for p in performances if p["id"] == performance_id), None)
    
    if not performance_obj:
        print(f"Error: Performance not found after voting")
        return False
    
    if voter_id not in performance_obj["votes"]:
        print(f"Error: Vote not recorded in performance: {performance_obj}")
        return False
    
    if performance_obj["average_score"] == 0:
        print(f"Error: Average score not calculated after vote: {performance_obj}")
        return False
    
    print(f"Successfully submitted vote with score: Flow={vote_data['flow']}, Lyrics={vote_data['lyrics']}, Creativity={vote_data['creativity']}")
    return True

def test_vote_restrictions_multiple_votes():
    """Test that a user cannot vote multiple times for the same performance"""
    # Submit a vote if needed
    if not test_votes:
        if not test_submit_vote():
            print("Error: Failed to submit vote for restrictions test")
            return False
    
    vote = list(test_votes.values())[0]
    voter_username = vote["voter_username"]
    voter_token = test_auth_tokens[voter_username]
    performance_id = vote["performance_id"]
    
    # Get the room ID
    performance = test_performances[performance_id]
    room_id = performance["room_id"]
    
    headers = {
        "Authorization": f"Bearer {voter_token}"
    }
    
    # Try to vote again
    vote_data = {
        "performance_id": performance_id,
        "room_id": room_id,
        "flow": 7,
        "lyrics": 8,
        "creativity": 6,
        "emoji_reaction": "👍"
    }
    
    response = requests.post(f"{API_URL}/votes", json=vote_data, headers=headers)
    
    # This should fail with a 400 status code
    if response.status_code != 400:
        print(f"Error: Multiple votes should be rejected, got status code {response.status_code}")
        return False
    
    print("Successfully verified multiple votes are rejected")
    return True

def test_vote_restrictions_self_voting():
    """Test that a user cannot vote for their own performance"""
    # Submit a performance if needed
    if not test_performances:
        if not test_submit_performance_with_timeline():
            print("Error: Failed to submit performance for self-voting test")
            return False
    
    performance = list(test_performances.values())[0]
    performer_username = performance["username"]
    performer_token = test_auth_tokens[performer_username]
    performance_id = performance["id"]
    room_id = performance["room_id"]
    
    headers = {
        "Authorization": f"Bearer {performer_token}"
    }
    
    # Try to vote for own performance
    vote_data = {
        "performance_id": performance_id,
        "room_id": room_id,
        "flow": 10,
        "lyrics": 10,
        "creativity": 10,
        "emoji_reaction": "🔥"
    }
    
    response = requests.post(f"{API_URL}/votes", json=vote_data, headers=headers)
    
    # This should fail with a 400 status code
    if response.status_code != 400:
        print(f"Error: Self-voting should be rejected, got status code {response.status_code}")
        return False
    
    print("Successfully verified self-voting is rejected")
    return True

# Audio Effects Tests
def test_get_audio_effects():
    """Test getting the built-in audio effects library"""
    response = requests.get(f"{API_URL}/audio-effects")
    
    if response.status_code != 200:
        print(f"Error: Get audio effects returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "effects" not in data or not isinstance(data["effects"], list):
        print(f"Error: Audio effects response invalid: {data}")
        return False
    
    # Check if we have the built-in effects
    builtin_effects = [effect for effect in data["effects"] if effect["category"] == "builtin"]
    if len(builtin_effects) < 4:  # We should have at least 4 built-in effects
        print(f"Error: Not enough built-in audio effects: {len(builtin_effects)}")
        return False
    
    # Check for required effect names
    required_effects = ["Boom", "Applause", "Air Horn", "Vinyl Scratch"]
    for name in required_effects:
        if not any(effect["name"] == name for effect in builtin_effects):
            print(f"Error: Built-in effect '{name}' not found")
            return False
    
    print(f"Successfully retrieved {len(data['effects'])} audio effects, including {len(builtin_effects)} built-in effects")
    return True

def test_create_custom_audio_effect():
    """Test creating a custom audio effect"""
    # Login a user if needed
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for custom effect test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a mock audio data
    mock_audio = base64.b64encode(b"This is a mock custom audio effect").decode('utf-8')
    
    # Create a custom effect
    effect_data = {
        "name": f"Custom Effect {int(time.time())}",
        "audio_data": mock_audio,
        "duration": 2.5
    }
    
    response = requests.post(f"{API_URL}/audio-effects", json=effect_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Create custom effect returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    new_effect = response.json()
    if new_effect["name"] != effect_data["name"] or new_effect["category"] != "custom":
        print(f"Error: Custom effect data doesn't match input: {new_effect}")
        return False
    
    print(f"Successfully created custom audio effect: {new_effect['name']}")
    return True

# Challenge Tests
def test_get_challenges():
    """Test getting all challenges"""
    response = requests.get(f"{API_URL}/challenges")
    
    if response.status_code != 200:
        print(f"Error: Get challenges returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    if "challenges" not in data or not isinstance(data["challenges"], list):
        print(f"Error: Challenges response invalid: {data}")
        return False
    
    print(f"Successfully retrieved {len(data['challenges'])} challenges")
    return True

def test_create_challenge():
    """Test creating a new challenge"""
    # Login a user if needed
    if not test_auth_tokens:
        if not test_login_user():
            print("Error: Failed to login user for challenge creation test")
            return False
    
    username = list(test_auth_tokens.keys())[0]
    token = test_auth_tokens[username]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Create a challenge
    challenge_data = {
        "title": f"Test Challenge {int(time.time())}",
        "description": "This is a test challenge created by the API test",
        "type": "public",
        "rules": {
            "time_limit": 60,
            "theme": "test",
            "rounds": 2
        }
    }
    
    response = requests.post(f"{API_URL}/challenges", json=challenge_data, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Create challenge returned status code {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    new_challenge = response.json()
    if new_challenge["title"] != challenge_data["title"]:
        print(f"Error: Created challenge data doesn't match input: {new_challenge}")
        return False
    
    print(f"Successfully created challenge: {new_challenge['title']} with ID: {new_challenge['id']}")
    return True

def run_all_tests():
    """Run all tests and print a summary"""
    print(f"\n{'='*80}\nRevMix Backend API Test Suite\n{'='*80}")
    print(f"Testing backend at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # API Root
    run_test("API Root", test_api_root)
    
    # Authentication Tests
    run_test("Register New User", test_register_new_user)
    run_test("Login User", test_login_user)
    run_test("Get Current User", test_get_current_user)
    run_test("Register Duplicate Username", test_register_duplicate_username)
    run_test("Logout User", test_logout_user)
    
    # User Profile Tests
    run_test("Get User Profile", test_get_user_profile)
    run_test("Get Leaderboard", test_get_leaderboard)
    
    # Room Tests
    run_test("Create Room with 1-hour Expiry", test_create_room)
    run_test("Get Active Rooms", test_get_rooms)
    run_test("Get Room by ID", test_get_room_by_id)
    run_test("Join Room", test_join_room)
    run_test("Get Room Results", test_room_results)
    
    # Performance Tests
    run_test("Submit Performance with Timeline", test_submit_performance_with_timeline)
    run_test("Get Room Performances", test_get_room_performances)
    
    # Voting Tests
    run_test("Submit Vote", test_submit_vote)
    run_test("Vote Restrictions - Multiple Votes", test_vote_restrictions_multiple_votes)
    run_test("Vote Restrictions - Self Voting", test_vote_restrictions_self_voting)
    
    # Audio Effects Tests
    run_test("Get Audio Effects Library", test_get_audio_effects)
    run_test("Create Custom Audio Effect", test_create_custom_audio_effect)
    
    # Challenge Tests
    run_test("Get All Challenges", test_get_challenges)
    run_test("Create Challenge", test_create_challenge)
    
    # Room Lifecycle Tests
    run_test("Close Room", test_close_room)
    
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
    success = run_all_tests()
    sys.exit(0 if success else 1)