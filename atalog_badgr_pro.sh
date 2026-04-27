#!/bin/bash
# catalog_badgr_turbo.sh — MAX SPEED: parallel AI on 12 cores

cd /home/t0n34781/projects/badgr_harness && source .venv/bin/activate
export OLLAMA_NUM_PARALLEL=6  # Harness max
read -p "Model (qwen2.5-coder:7b): " model
MAX_WORKERS=12  # Ryzen cores

python3 << 'EOF'
import os
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
import subprocess
import multiprocessing as mp

BASE_PATH = Path('/home/t0n34781')
portfolio_cats = ["business_artwork", "digital_artwork", "business_plans", "engineering_practices", 
                  "software_development", "tools_development", "website_development"]

def scan_file(path_str):
    path = Path(path_str)
    if path.name.startswith('.'): return None
    try:
        st = path.stat()
        if st.st_size == 0: return None
        rel = path.relative_to(BASE_PATH)
        cat = categorize(path.name)
        port = cat in portfolio_cats
        created = datetime.fromtimestamp(st.st_ctime).isoformat()
        summary = ai_describe(str(path), MODEL)  # Global model
        return {
            'full_path': str(path), 'relative_path': str(rel), 'filename': path.name,
            'category': cat, 'portfolio_relevant': port, 'size_bytes': st.st_size,
            'created': created, 'ai_description': summary
        }
    except:
        return None

def ai_describe(path: str, model: str) -> str:
    try:
        # Batch-friendly: short prompt
        prompt = f"1-sentence BADGR portfolio desc: {Path(path).name} purpose/category."
        cmd = ['ollama', 'run', '--raw', model, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, cwd='/home/t0n34781')
        return result.stdout.strip()[:150] if result.returncode == 0 else "Desc gen failed"
    except:
        return "AI timeout"

def categorize(fn: str) -> str:
    # Same rules as before
    ext = Path(fn).suffix.lower()
    rules = {'.py': 'software_development', '.js': 'website_development', '.json': 'config_or_index', 
             '.txt': 'docs_or_notes', '.md': 'engineering_practices', '.png': 'digital_artwork', 
             '.pdf': 'business_plans', '.html': 'website_development'}
    return rules.get(ext, 'uncategorized')

# Collect ALL paths first (fast)
paths = []
for root, dirs, files in os.walk(BASE_PATH):
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for fn in files:
        if not fn.startswith('.'):
            p = Path(root) / fn
            try:
                if p.stat().st_size > 0: paths.append(str(p))
            except: pass

print(f"🚀 Scanning {len(paths)} files w/ {MAX_WORKERS} parallel workers...")

MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5-coder:7b')
with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(scan_file, p): p for p in paths}
    index = []
    for future in as_completed(futures):
        res = future.result()
        if res: index.append(res)

os.makedirs('output', exist_ok=True)
with open('output/badgr_turbo_index.jsonl', 'w') as f:
    for item in sorted(index, key=lambda x: x['size_bytes'], reverse=True):
        f.write(json.dumps(item) + '\n')

print(f"💥 TURBO COMPLETE: {len(index)} files → output/badgr_turbo_index.jsonl | Portfolio: {sum(1 for i in index if i["portfolio_relevant"])}")
EOF
