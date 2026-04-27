# sba_sitemap_fixed.py
import requests
from bs4 import BeautifulSoup
import sys

BASE = "https://www.sba.gov"
sitemap_urls = set()
page = 1
max_pages = 25

print("=== SBA SITEMAP HARVESTER ===", flush=True)
print(f"Testing page 1...", flush=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Accept": "application/xml,text/xml,*/*"
})

while page <= max_pages:
    url = f"{BASE}/sitemap.xml?page={page}"
    print(f"\n[{page}/{max_pages}] {url}", end=" ", flush=True)
    
    try:
        # stream=true + chunked read for large XML
        r = session.get(url, timeout=(5, 15), stream=True)
        r.raise_for_status()
        
        content = b""
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
        
        print(f"OK ({len(content)} bytes)", flush=True)
        
        soup = BeautifulSoup(content, "lxml-xml")  # Faster XML parser
        locs = [loc.text.strip() for loc in soup.find_all("loc") 
                if loc.text and "sba.gov" in loc.text]
        
        new_urls = set(locs) - sitemap_urls
        sitemap_urls.update(locs)
        print(f"New: {len(new_urls)}, Running total: {len(sitemap_urls)}", flush=True)
        
        if len(locs) == 0:
            print("Empty page - done!")
            break
            
    except requests.exceptions.Timeout:
        print("TIMEOUT", flush=True)
        break
    except requests.exceptions.HTTPError as e:
        print(f"HTTP {e.response.status_code}", flush=True)
        break
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        break
    
    page += 1
    sys.stdout.flush()

print(f"\n\nSUCCESS: {len(sitemap_urls)} total unique URLs")
with open("sba_sitemap_urls.txt", "w") as f:
    f.write("\n".join(sorted(sitemap_urls)))

print("Saved: sba_sitemap_urls.txt")
print("Next: python filter_rag.py")
