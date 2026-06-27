
from PIL import Image
import os

def get_folder_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            fp = os.path.join(root, file)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def generate_thumb(file_path):
    try:
        base_dir = os.path.dirname(file_path)
        thumb_dir = os.path.join(base_dir, ".thumbs")
        os.makedirs(thumb_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        thumb_path = os.path.join(thumb_dir, filename)
        
        with Image.open(file_path) as img:
            img.thumbnail((200, 200))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(thumb_path, "JPEG", quality=80)
    except Exception as e:
        print(f"Błąd miniatury: {e}")
