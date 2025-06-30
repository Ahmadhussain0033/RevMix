#!/usr/bin/env python3
"""
Script to add a test admin user to the RevMix database
"""

import os
import uuid
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get MongoDB URL
MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    print("Error: MONGO_URL not found in environment")
    exit(1)

# Connect to MongoDB
client = MongoClient(MONGO_URL)
DB_NAME = os.environ.get('DB_NAME', 'revmix_production')
db = client[DB_NAME]
users_collection = db.users

def add_admin_user():
    """Add admin test user to database"""
    
    # Check if admin user already exists
    existing_user = users_collection.find_one({"username": "Admin"})
    if existing_user:
        print("Admin user already exists!")
        print(f"User ID: {existing_user['id']}")
        print(f"Username: {existing_user['username']}")
        print(f"Email: {existing_user.get('email', 'admin@revmix.com')}")
        return existing_user
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": "Admin",
        "email": "admin@revmix.com",
        "supabase_id": None,  # Not using Supabase for this test user
        "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
        "level": 99,  # Admin level
        "xp": 10000,  # High XP for admin
        "bio": "Admin user for testing 🔑",
        "badges": ["Admin", "Tester", "VIP", "Battle Master"],
        "wins": 50,
        "battles": 100,
        "created_at": datetime.now(timezone.utc),
        "password_hash": None,  # We'll handle this separately
        "is_test_user": True  # Flag to identify test users
    }
    
    # Insert the user
    result = users_collection.insert_one(admin_user)
    admin_user.pop('_id', None)
    
    print("✅ Admin user created successfully!")
    print(f"User ID: {admin_user['id']}")
    print(f"Username: {admin_user['username']}")
    print(f"Password: admin123")
    print(f"Email: {admin_user['email']}")
    print(f"Level: {admin_user['level']}")
    print(f"XP: {admin_user['xp']}")
    print("\n🎮 You can now login with:")
    print("Username: Admin")
    print("Password: admin123")
    
    return admin_user

if __name__ == "__main__":
    print("Adding Admin test user to RevMix database...")
    add_admin_user()