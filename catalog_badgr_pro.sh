#!/bin/bash
# catalog_badgr_pro.sh — Run in /home/t0n34781/projects/badgr_harness (.venv active)

cd /home/t0n34781 || exit 1
read -p "Ollama model (qwen2.5-coder:7b): " model
read -p "Max depth/files (0=full): " max_depth

python3 << 'EOF'
import os
import json
import subprocess
import stat
from datetime import datetime
from pathlib import Path

BASE_PATH = Path('/home/t0n34781')
portfolio_cats = ["business_artwork", "digital_artwork", "business_plans", "engineering_practices", 
                  "software_development", "tools_development", "website_development"]

def ai_describe(path: str, model: str) -> str:
    try:
        cmd = ['ollama', 'run', model, f"""Precise 1-2 sentence description for BADGR Technologies portfolio.
File: {path}
Content purpose/category:"""]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45, cwd='/home/t0n34781')
        return result.stdout.strip().split('\n')[0][:200] if result.returncode == 0 else "AI summary pending"
    except:
        return "Local AI error"

def categorize(fn: str) -> str:
    ext = Path(fn).suffix.lower()
    rules = {
        '.py': 'software_development', '.js': 'website_development', '.ts': 'software_development',
        '.json': 'config_or_index', '.yaml': 'config_or_index', '.txt': 'docs_or_notes', '.md': 'engineering_practices',
        '.png': 'digital_artwork', '.jpg': 'business_artwork', '.pdf': 'business_plans', '.html': 'website_development'
    }
    return rules.get(ext, 'uncategorized')

index = []
for root, dirs, files in os.walk(BASE_PATH, max_depth=int(max_depth) if max_depth else 99):
    dirs[:] = [d for d in dirs if not d.startswith('.')]  # Skip .dirs
    for fn in files:
        if fn.startswith('.'): continue
        path = Path(root) / fn
        try:
            st = path.stat()
            if st.st_size == 0: continue
            rel_path = path.relative_to(BASE_PATH)
            cat = categorize(fn)
            port = cat in portfolio_cats
            created = datetime.fromtimestamp(st.st_ctime).isoformat()
            summary = ai_describe(str(path), model)
            index.append({
                'full_path': str(path), 'relative_path': str(rel_path),
                'filename': fn, 'category': cat, 'portfolio_relevant': port,
                'size_bytes': st.st_size, 'created': created, 'ai_description': summary
            })
        except (OSError, PermissionError):
            pass

os.makedirs('output', exist_ok=True)
with open('output/badgr_full_index.json', 'w') as f:
    json.dump({'base': '/home/t0n34781', 'index': index[:5000], 'total_scanned': len(index)}, f, indent=2)  # Cap for safety
print(f"✅ Indexed {len(index)} files → output/badgr_full_index.json (top 5000 shown)")
EOF
