import os

path = os.path.join('backend', 'verify_out.txt')
if os.path.exists(path):
    with open(path, 'rb') as f:
        content = f.read()
        # Try both common encodings
        try:
            print(content.decode('utf-16'))
        except:
            try:
                print(content.decode('utf-8'))
            except:
                print(content)
else:
    print("File not found.")
