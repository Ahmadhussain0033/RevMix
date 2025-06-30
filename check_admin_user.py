#!/usr/bin/env python3
"""
Check if Admin user exists in database
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get MongoDB URL
MONGO_URL = os.environ.get('MONGO_URL')
client = MongoClient(MONGO_URL)
DB_NAME = os.environ.get('DB_NAME', 'revmix_production')
db = client[DB_NAME]
users_collection = db.users

def check_admin_user():
    """Check if admin user exists"""
    admin_user = users_collection.find_one({"username": "Admin"})
    
    if admin_user:
        print("✅ Admin user found in database:")
        print(f"ID: {admin_user['id']}")
        print(f"Username: {admin_user['username']}")
        print(f"Email: {admin_user['email']}")
        print(f"Is Test User: {admin_user.get('is_test_user', 'Not set')}")
        print(f"Supabase ID: {admin_user.get('supabase_id', 'None')}")
        return True
    else:
        print("❌ Admin user not found in database")
        return False

if __name__ == "__main__":
    check_admin_user()