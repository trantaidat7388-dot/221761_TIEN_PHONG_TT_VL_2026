import os
import glob

# Get all .log files recursively from D:
# We'll use os.walk to be safer with deep paths and avoid permission errors
log_files = []
for root, dirs, files in os.walk('D:\\'):
    for file in files:
        if file.endswith('.log'):
            path = os.path.join(root, file)
            try:
                mtime = os.path.getmtime(path)
                # Filter for last 60 minutes
                import time
                if time.time() - mtime < 3600:
                    log_files.append((path, mtime))
            except:
                pass
    # Avoid too deep or protected system dirs if we hit them
    if 'Windows' in root or '$Recycle.Bin' in root:
        dirs[:] = [] # skip subdirs

# Sort by mtime descending
log_files.sort(key=lambda x: x[1], reverse=True)

# Write to file
with open('backend/recent_logs_full.txt', 'w', encoding='utf-8') as f:
    for path, mtime in log_files:
        f.write(f"{path} | {mtime}\n")
