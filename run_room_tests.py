import sys
import os

# Run only the room lifecycle tests from the main backend_test.py
sys.path.append('/app')
from backend_test import (
    run_test,
    test_register_new_user,
    test_login_user,
    test_create_room,
    test_get_rooms,
    test_get_room_by_id,
    test_close_room
)

def run_room_lifecycle_tests():
    """Run only the room lifecycle tests"""
    print("\n" + "="*80)
    print("RevMix Room Lifecycle Management Tests")
    print("="*80)
    
    # Authentication (needed for room creation)
    run_test("Register New User", test_register_new_user)
    run_test("Login User", test_login_user)
    
    # Room Lifecycle Tests
    run_test("Create Room with 1-hour Expiry", test_create_room)
    run_test("Get Active Rooms", test_get_rooms)
    run_test("Get Room by ID", test_get_room_by_id)
    
    # Don't close the room - we want to verify it stays open
    # run_test("Close Room", test_close_room)

if __name__ == "__main__":
    run_room_lifecycle_tests()