import os
from pathlib import Path

# Extract logic from backend/app/config.py
# BASE_DIR = Path(__file__).parent.parent.parent
# But we are running from root, so Path(__file__) is root/backend/check_paths.py
# Thus BASE_DIR should be root/backend/parent/parent/parent = root? No.

script_path = Path('backend/app/config.py').resolve()
BASE_DIR = script_path.parent.parent.parent

TEMP_FOLDER = BASE_DIR / "backend" / "storage" / "temp_jobs"

print(f"BASE_DIR: {BASE_DIR}")
print(f"TEMP_FOLDER: {TEMP_FOLDER}")
print(f"Exists? {TEMP_FOLDER.exists()}")
if TEMP_FOLDER.exists():
    print(f"Contents: {os.listdir(TEMP_FOLDER)}")
