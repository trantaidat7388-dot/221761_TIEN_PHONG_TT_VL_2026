import os
import glob

# Get all .tex files recursively
tex_files = glob.glob('**/*.tex', recursive=True)

# Get their modification times
file_mtimes = []
for f in tex_files:
    try:
        mtime = os.path.getmtime(f)
        file_mtimes.append((f, mtime))
    except:
        pass

# Sort by mtime descending
file_mtimes.sort(key=lambda x: x[1], reverse=True)

# Write top 20 to file
with open('backend/recent_tex_full.txt', 'w', encoding='utf-8') as f:
    for path, mtime in file_mtimes[:20]:
        f.write(f"{path} | {mtime}\n")
