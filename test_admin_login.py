#!/usr/bin/env python3
"""
Test script to verify Admin user login
"""

import requests
import json

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

def test_admin_login():
    """Test admin user login"""
    print("🔐 Testing Admin user login...")
    
    login_data = {
        "username": "Admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{API_URL}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Admin login successful!")
        print(f"User: {data['user']['username']}")
        print(f"Level: {data['user']['level']}")
        print(f"XP: {data['user']['xp']}")
        print(f"Badges: {', '.join(data['user']['badges'])}")
        return data
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_room_creation_with_admin(auth_data):
    """Test room creation with admin user"""
    if not auth_data:
        return
        
    print("\n🏠 Testing room creation with Admin user...")
    
    headers = {
        'Authorization': f"Bearer {auth_data['session']['access_token']}"
    }
    
    room_data = {
        "name": "Admin's Test Room",
        "type": "solo",
        "prompt": "Testing room creation as Admin!",
        "timer_duration": 300,
        "max_participants": 5
    }
    
    response = requests.post(f"{API_URL}/rooms", json=room_data, headers=headers)
    
    if response.status_code == 200:
        room = response.json()
        print("✅ Room creation successful!")
        print(f"Room ID: {room['id']}")
        print(f"Room Name: {room['name']}")
        print(f"Host: {room['host_id']}")
        print(f"Status: {room['status']}")
        print(f"Expires At: {room['expires_at']}")
        return room
    else:
        print(f"❌ Room creation failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

if __name__ == "__main__":
    print("🎮 Testing Admin User Authentication and Room Creation")
    print("=" * 60)
    
    # Test login
    auth_data = test_admin_login()
    
    # Test room creation
    if auth_data:
        test_room_creation_with_admin(auth_data)
    
    print("\n" + "=" * 60)
    print("✨ Test completed!")