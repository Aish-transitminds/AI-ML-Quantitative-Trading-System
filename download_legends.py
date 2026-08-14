import urllib.request
import os

os.makedirs("web/public/legends", exist_ok=True)

images = {
    "rakesh.jpg": "https://upload.wikimedia.org/wikipedia/commons/1/14/Rakesh_Jhunjhunwala.jpg",
    "warren.jpg": "https://upload.wikimedia.org/wikipedia/commons/5/51/Warren_Buffett_KU_School_of_Business_2017.jpg",
    "jim.jpg": "https://upload.wikimedia.org/wikipedia/commons/e/e0/Jim_Simons_1993.jpg"
}

for name, url in images.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req) as response, open(f"web/public/legends/{name}", 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"Successfully downloaded {name}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")
