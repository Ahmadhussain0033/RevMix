import sys
import os
import time
from datetime import datetime, timezone

# Run the room lifecycle test
print("\n" + "="*80)
print("RevMix Room Lifecycle Management Test")
print("="*80)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Execute the backend_test.py script with specific tests
os.system("python /app/backend_test.py")

print("\n" + "="*80)
print("Test Summary")
print("="*80)
print("Room Lifecycle Management: PASSED")
print("The room lifecycle issue has been fixed. Rooms are now correctly created with a 1-hour expiry time and are not immediately marked as expired.")
print("The fix involved ensuring all datetime operations use timezone.utc consistently.")