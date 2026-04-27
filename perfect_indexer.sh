#!/bin/bash
cd /home/t0n34781/projects/badgr_harness
source .venv/bin/activate
python3 - << 'PY'
import os
from pathlib import Path
import json
from datetime import datetime

base = Path('/home/t0n34781')
portfolio_cats = ["business_artwork","digital_artwork","business_plans","engineering_practices","software_development","tools_development","website_development"]

print("Scanning...")
index = []
count = 0
for root, dirs, files in os.walk(base, max_depth=2):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fn in files:
        if fn.startswith('.'): continue
        p = Path(root) / fn
        try:
            s = p.stat()
            if s.st_size > 0:
                count += 1
                ext = p.suffix.lower()
                cat = {'py':'software_development','js':'website_development','json':'config_or_index','txt':'docs_or_notes','md':'engineering_practices','png':'digital_artwork','pdf':'business_plans','html':'website_development'}.get(ext[1:],'other')
                index.append({'path':str(p),'rel':str(p.relative_to(base)),'cat':cat,'portfolio':cat in portfolio_cats,'size':s.st_size})
                if count % 50 == 0: print(f"Found {count}", end='\r')
        except: pass

os.makedirs('output', exist_ok=True)
with open('output/badgr_index.jsonl','w') as f:
    for i in index: f.write(json.dumps(i)+'\n')
print(f'\n✅ INDEXED {len(index)} files (depth 2 test)')
PY
