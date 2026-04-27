#!/bin/bash
cd /home/t0n34781/projects/badgr_harness
source .venv/bin/activate
export OLLAMA_MODEL=qwen2.5-coder:7b

python3 - << 'PY'
from pathlib import Path
import json
from datetime import datetime

base = Path('/home/t0n34781')
portfolio_cats = ["business_artwork","digital_artwork","business_plans","engineering_practices","software_development","tools_development","website_development"]

index = []
for root,dirs,files in os.walk(base, max_depth=2):  # Fast test depth
 dirs[:] = [d for d in dirs if not d.startswith('.')]
 for fn in files:
  if fn.startswith('.'): continue
  p = Path(root)/fn
  try:
   s = p.stat()
   if s.st_size > 0:
    ext = p.suffix.lower()
    cat = {'py':'software_development','js':'website_development','json':'config_or_index','txt':'docs_or_notes','md':'engineering_practices','png':'digital_artwork','pdf':'business_plans','html':'website_development'}.get(ext[1:],'other')
    index.append({'path':str(p),'rel':str(p.relative_to(base)),'cat':cat,'portfolio':cat in portfolio_cats,'size':s.st_size,'created':datetime.fromtimestamp(s.st_ctime).isoformat()})
  except: pass

Path('output').mkdir(exist_ok=True)
with open('output/badgr_simple.jsonl','w') as f:
 for i in index: f.write(json.dumps(i)+'\n')
print(f"✅ SIMPLE TEST: {len(index)} files indexed (depth 2)")
PY
