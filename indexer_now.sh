#!/bin/bash
cd /home/t0n34781/projects/badgr_harness && source .venv/bin/activate
python3 - <<PY
from pathlib import Path
import json
from datetime import datetime

base = Path('/home/t0n34781')
portfolio_cats = ["business_artwork","digital_artwork","business_plans","engineering_practices","software_development","tools_development","website_development"]

print("Indexing /home/t0n34781/projects* + /home/t0n34781/badgr* (fast)")
index = []
for proj_dir in base.glob('projects/*') + base.glob('badgr*'):
    if proj_dir.is_dir():
        for p in proj_dir.rglob('*'):
            if p.is_file() and not p.name.startswith('.') and p.stat().st_size > 0:
                ext = p.suffix.lower()
                cat = {'py':'software_development','js':'website_development','json':'config_or_index','txt':'docs_or_notes','md':'engineering_practices','png':'digital_artwork','pdf':'business_plans','html':'website_development'}.get(ext[1:],'other')
                index.append({'path':str(p),'rel':str(p.relative_to(base)),'cat':cat,'portfolio':cat in portfolio_cats,'size':p.stat().st_size})

Path('output').mkdir(exist_ok=True)
json.dump(index, open('output/badgr_index.json','w'), indent=2)
print(f"✅ {len(index)} files indexed!")
PY
