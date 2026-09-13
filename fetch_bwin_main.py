import urllib.request
import gzip

url = "https://sports.bwin.fr/ClientDist/browser/main-OLUIUIFL.js"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        print("Raw length:", len(content))
        if resp.headers.get("Content-Encoding") == "gzip":
            content = gzip.decompress(content)
        print("Decompressed length:", len(content))
        # search for accessid
        import re
        matches = re.findall(rb'accessid[=:][\s"\']*([a-zA-Z0-9_-]+)', content, re.I)
        print("Matches in main:", matches)
except Exception as e:
    print("Urllib error:", e)
