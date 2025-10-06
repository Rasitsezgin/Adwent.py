# Direk başlat: #  python Adwent.py
Google Dorks Python kodu#!/usr/bin/env python3
from googlesearch import search
import time

# Hedef domain (düzelt)
target = "example.com"

# Payload listesi (dork kalıpları)
payloads = [
    'intitle:"index of" "parent directory"',
    'inurl:id=',
    'inurl:page.php?intPageID=',
    'inurl:product.php?item=',
    'inurl:catid=',
    'inurl:admin',
    'intitle:"admin login"',
    'inurl:login',
    '"Warning: mysql"',
    '"Fatal error"',
    '"unexpected T_STRING"',
    f'intext:"@{target}"',
    'filetype:pdf',
    'ext:sql OR ext:log OR ext:env OR ext:bak'
]

print("🕵️ Google Dork Taraması Başladı...\n")

for payload in payloads:
    dork = f"site:{target} {payload}"
    print(f"[+] Dork: {dork}")
    try:
        for url in search(dork, num_results=5):
            print(f"    -> {url}")
        time.sleep(2)  # Google rate-limit önleme
    except Exception as e:
        print(f"    HATA: {e}")
    print()
