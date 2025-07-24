import requests
import zipfile
import os

file_id = "14rRzeFOOjgWg-uSZ8R9DSsHCqO5WSgDW"
url = f"https://drive.google.com/uc?id={file_id}&export=download"

# Download and extract
response = requests.get(url)
if response.status_code == 200:
    with open("temp.zip", "wb") as f:
        f.write(response.content)
    
    with zipfile.ZipFile("temp.zip", 'r') as zip_ref:
        files = zip_ref.namelist()
        root = files[0].split('/')[0] + '/' if files and '/' in files[0] and all(f.startswith(files[0].split('/')[0] + '/') for f in files) else ''
        
        for info in zip_ref.infolist():
            if not info.is_dir():
                path = info.filename[len(root):] if root and info.filename.startswith(root) else info.filename
                if path:
                    target = os.path.join("poc_fl_data", path)
                    os.makedirs(os.path.dirname(target), exist_ok=True)
                    with zip_ref.open(info.filename) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
    
    os.remove("temp.zip")
    print("Downloaded and extracted to poc_fl_data/")
else:
    print(f"Failed: {response.status_code}")
