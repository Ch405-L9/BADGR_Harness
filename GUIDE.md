# **BADGR Harness — Unified Operations Guide**
**BADGRTechnologies LLC | Brandon Anthony Grant**
**Last updated: 2026-04-26**

---

---

# **PART 1 — SYSTEM OVERVIEW**

---

## **What This Is**

Two systems, one stack:

| System | Path | Role |
|---|---|---|
| **badgr_harness** | `/home/t0n34781/projects/badgr_harness` | Central LLM orchestration + RAG corpus + MCP host |
| **Pro Hunter** | `/home/t0n34781/projects/pro_hunter` | Job search + scoring + application automation |

**badgr_harness** runs the harness core (orchestrator → router → validator) and hosts the shared ChromaDB at `rag_db/`.

**Pro Hunter** scrapes job sites, scores against skill profiles, stores to CSV, and feeds jobs into the harness RAG. Registered as an MCP server inside badgr_harness sessions.

---

## **Shared Infrastructure**

| Resource | Location |
|---|---|
| ChromaDB | `badgr_harness/rag_db/` |
| `badgr_corpus` collection | 2087 AI/tech reference docs |
| `job_opportunities` collection | Pro Hunter job feed |
| MCP config | `badgr_harness/.mcp.json` |
| Pro Hunter venv | `pro_hunter/.venv` |
| Ollama API | `http://localhost:11434` |

---

## **Model Quick Reference**

| Model | Size | Use |
|---|---|---|
| `mistral:7b` | 4.4 GB | Parse, score, docs — **PRIMARY** |
| `nomic-embed-text` | 0.3 GB | All embeddings |
| `llama3.2:latest` | 2.0 GB | BrowserUse automation |
| `gemma2:2b` | 1.6 GB | Fast classification |
| `qwen2.5-coder:7b` | 4.7 GB | Code gen |
| `badgr-analyst:latest` | 4.4 GB | Custom analysis |
| ~~`qwen2.5:14b`~~ | 9.0 GB | **DO NOT USE in pipeline** — OOM on 16GB |

**Check what's loaded:**
```bash
curl -s http://localhost:11434/api/ps | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin).get('models',[])]"
```

**Force-unload a model:**
```bash
curl -s -X POST http://localhost:11434/api/generate -d '{"model":"MODEL_NAME","keep_alive":0}'
```

---

---

# **PART 2 — PRO HUNTER: JOB SEARCH SYSTEM**

---

## **What It Does**

```
URL / search query
    → Scrape (local Playwright → Firecrawl → BrowserUse → Agenty)
    → Parse (mistral:7b extracts title/company/location/tech/salary)
    → Score (mistral:7b fits against your skill profile)
    → Save (CSV at data/jobs.csv)
    → RAG (indexed into job_opportunities collection)
```

---

## **Quick Start**

```bash
cd /home/t0n34781/projects/pro_hunter
source .venv/bin/activate
```

---

## **Core Commands**

### **Score a single job**
```bash
.venv/bin/python -m cli.main collect-score \
  --url "https://www.usajobs.gov/job/840854000" \
  --site usajobs \
  --profile ai-sw-engineer
```

### **Run daily collection — all profiles**
```bash
.venv/bin/python -m cli.main run-daily
```

### **Run daily — specific profiles**
```bash
.venv/bin/python -m cli.main run-daily \
  --profiles ai-sw-engineer,python-automation,workmarket-contractor
```

### **List collected jobs**
```bash
# All jobs
.venv/bin/python -m cli.main list

# High scorers only
.venv/bin/python -m cli.main list --min-score 60

# Top jobs sorted by score
.venv/bin/python -m cli.main list --min-score 40 --sort score
```

### **Semantic search across collected jobs**
```bash
.venv/bin/python -m cli.main query \
  --text "Python AI engineer remote LLM" \
  --k 5

# Filter by minimum score
.venv/bin/python -m cli.main query \
  --text "automation contractor" \
  --k 10 \
  --min-score 50
```

### **Apply to a job (dry run by default)**
```bash
# Dry run — no submission
.venv/bin/python -m cli.main apply --job-id JOB_ID

# Live submit (confirm first)
.venv/bin/python -m cli.main apply --job-id JOB_ID --live
```

---

## **Skill Profiles**

| Profile Key | Role | Min Salary | Min Rate |
|---|---|---|---|
| `ai-sw-engineer` | AI Software Engineer — **PRIMARY** | $85k | $45/hr |
| `ai-agents` | AI Agent & LLM Orchestration | $90k | $50/hr |
| `devops-mlops` | DevOps & MLOps | $85k | $45/hr |
| `python-automation` | Python Automation | $80k | $40/hr |
| `full-stack-dev` | Full Stack JS/TS/React | $80k | $40/hr |
| `field-support-engineer` | Field Hardware Support | $75k | $38/hr |
| `tech-support` | Technical Support Eng II | $60k | $30/hr |
| `federal-contracts` | Federal IT (BADGRTech LLC) | $80k | $45/hr |
| `workmarket-contractor` | Freelance / Gig | — | $35/hr |

---

## **Job Sites**

| Site Key | Platform | Auth |
|---|---|---|
| `workmarket` | WorkMarket | ✓ (PRIMARY) |
| `linkedin` | LinkedIn Jobs | ✓ |
| `indeed_proton` | Indeed (antgrant4781@proton.me) | ✓ |
| `indeed_gmail` | Indeed (antgrant4781@gmail.com) | Google |
| `ziprecruiter` | ZipRecruiter | Google |
| `usajobs` | USAJobs | — |
| `remote_ok` | RemoteOK | — |
| `dice` | Dice | — |
| `wellfound` | Wellfound / AngelList | — |
| `sam_gov` | SAM.gov Federal Contracts | — |

---

## **Scraping Tiers**

Tries in order, stops at first success:

```
Tier 0: local Playwright  (headless Chromium, no key needed)
Tier 1: Firecrawl self-hosted  (localhost:3002 — deploy with docker-compose)
Tier 2: Firecrawl cloud  ($FIRECRAWL_API_KEY)
Tier 3: BrowserUse  (LLM-driven, uses llama3.2:latest)
Tier 4: Agenty  ($AGENTY_API_KEY — polls 5s interval, 2min timeout)
```

**Sites requiring auth (Tier 3+):** workmarket, linkedin, ziprecruiter, indeed accounts

---

## **Configuration Files**

| File | Purpose |
|---|---|
| `config/providers.yaml` | Scraping tier order, Ollama model config, API quotas |
| `config/sites.yaml` | Per-site URLs, strategy tiers, credential keys |
| `config/skills.yaml` | Skill profiles with keywords, must-haves, salary floors |
| `config/identity.yaml` | **LOCAL ONLY — gitignored.** Full identity + platform credentials. |

---

## **Data Output**

```
data/jobs.csv          — CRM with 50 fields, dedup by job_id
logs/                  — Pipeline logs
rag_db/job_opportunities  — ChromaDB collection (shared with harness)
```

---

## **Set Up Cron (Daily 8 AM)**

```bash
crontab -e
# Add this line:
0 8 * * * .venv/bin/python -m cli.main run-daily >> logs/daily.log 2>&1
```

---

## **Ollama Queue Troubleshooting**

If the pipeline hangs at exactly 300s, Ollama has orphaned queued requests:

```bash
# 1. Check what's loaded
curl -s http://localhost:11434/api/ps

# 2. Force-unload each loaded model
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"MODEL_NAME","keep_alive":0}'

# 3. Quick smoke test (should respond in <10s)
time curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"mistral:7b","prompt":"OK","stream":false}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('response','')[:30])"
```

---

---

# **PART 3 — BADGR HARNESS: ORCHESTRATION CORE**

---

## **What It Does**

Receives a task → classifies it → routes to the right model → validates the output → retries/falls back/escalates as needed → logs everything.

```
task input
    → router.py (keyword classify: code/classify/extract/summarize/plan)
    → models.yaml (select primary model + fallback chain)
    → worker call (local Ollama)
    → validator.py (strict JSON schema check)
    → retry once if malformed
    → fallback model if still failing
    → supervisor escalation if all paths fail
    → output + JSONL log + daily markdown report
```

---

## **Running the Harness**

```bash
cd /home/t0n34781/projects/badgr_harness

# Run a task through the orchestrator
python3 orchestrator.py

# Query the RAG knowledge base
python3 rag_query.py

# Check what's in the RAG database
/home/t0n34781/projects/pro_hunter/.venv/bin/python -c "
import chromadb
c = chromadb.PersistentClient(path='rag_db')
for col in c.list_collections():
    print(col.name, ':', col.count(), 'docs')
"

# Run tests
pytest -q
```

---

## **Key Files**

| File | Role |
|---|---|
| `orchestrator.py` | Main pipeline — dispatch, retry, fallback, escalate |
| `router.py` | Keyword classifier — picks task lane |
| `validator.py` | Strict JSON validation — strips fences, validates schema |
| `config.py` | Central settings — paths, timeouts, thresholds |
| `models.yaml` | Model registry — roles, timeouts, fallback chains |
| `prompts/` | Per-task prompt templates |
| `schemas/` | Pydantic response models |
| `logs/` | JSONL event logs (one per day) |
| `reports/` | Markdown daily reports |
| `state/` | `runtime_state.json` |

---

## **RAG Knowledge Base**

Two collections in `rag_db/`:

### **`badgr_corpus`** — 2087 docs
AI/tech reference papers, guides, validated repos. Read-only. Ingested by `corpus_harvest.py`.

```bash
# Query it
python3 rag_query.py

# Or use pro_hunter venv
/home/t0n34781/projects/pro_hunter/.venv/bin/python -c "
import chromadb
c = chromadb.PersistentClient(path='rag_db')
col = c.get_collection('badgr_corpus')
print('docs:', col.count())
results = col.query(query_texts=['Python LLM automation'], n_results=3)
for doc in results['documents'][0]:
    print('---')
    print(doc[:200])
"
```

### **`job_opportunities`** — grows with pipeline
Scored jobs from Pro Hunter. Fed automatically after each pipeline run.

```bash
# Check job count
/home/t0n34781/projects/pro_hunter/.venv/bin/python -c "
import chromadb
c = chromadb.PersistentClient(path='rag_db')
col = c.get_collection('job_opportunities')
print('jobs indexed:', col.count())
results = col.query(query_texts=['remote AI engineer'], n_results=5)
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(meta['job_title'], '|', meta['fit_score'], '/100 |', meta['source_site'])
"
```

---

## **MCP Tools (From Claude Code Session)**

Open Claude Code inside `badgr_harness/`. The `pro-hunter` MCP server auto-registers from `.mcp.json`.

Available tools in Claude:

| Tool | What it does |
|---|---|
| `job_search` | Scrape + score a URL against a profile |
| `job_query` | Semantic search over job_opportunities |
| `job_apply` | Trigger form filling for a job |
| `list_jobs` | List CSV jobs with optional score filter |
| `ingest_jobs_to_rag` | Bulk push all CSV jobs to ChromaDB |

---

## **Important Notes**

- **ChromaDB**: System python3 has a pydantic version conflict. Always use `pro_hunter/.venv/bin/python` for any RAG operations.
- **Ollama on CPU**: 16GB RAM. Keep only one large model loaded at a time. `mistral:7b` is the ceiling for reliable pipeline use.
- **identity.yaml**: Never in git. Contains EIN, UEI, platform passwords. Local only.

---

---

# **PART 4 — IDENTITY & BUSINESS**

---

## **Brandon Anthony Grant**

- **Email (primary):** antgrant4781@proton.me
- **Email (secondary):** antgrant4781@gmail.com
- **Phone:** 470-263-8217
- **LinkedIn:** linkedin.com/in/anthonyg-5b2b1a273
- **GitHub:** github.com/BADGRTech-DevTeam
- **Location:** Atlanta Metro / Lawrenceville GA 30044

## **BADGRTechnologies LLC**

- **EIN:** 33-3212015
- **DUNS:** 136411582
- **UEI:** U9GUGKVFGCA9
- **NAICS:** 541511 (Custom Computer Programming Services)
- **Founded:** 2025-02-03
- **Business Phone:** 470-223-6127
- **Business Email:** adgrant1@badgrtech.com
- **Registered Address:** 8735 Dunwoody Place STE. #7223, Atlanta GA 30350

## **Platform Credentials**

> Stored in `config/identity.yaml` — LOCAL ONLY, gitignored. See that file for passwords.

| Platform | Username | Notes |
|---|---|---|
| LinkedIn | antgrant4781@proton.me | Password in identity.yaml |
| WorkMarket | antgrant4781@proton.me | **PRIMARY** — Password in identity.yaml |
| ZipRecruiter | antgrant4781@gmail.com | Google auth |
| Indeed (USER1) | antgrant4781@proton.me | Manual login |
| Indeed (USER2) | antgrant4781@gmail.com | Google auth, pre-configured remote/tech |

---

---

# **PART 5 — TROUBLESHOOTING**

---

## **Pipeline hangs at 300s**
Ollama has orphaned queued requests from a killed process.
```bash
# Unload all models
curl -s http://localhost:11434/api/ps | python3 -c "
import sys, json, subprocess
for m in json.load(sys.stdin).get('models', []):
    subprocess.run(['curl', '-s', '-X', 'POST', 'http://localhost:11434/api/generate',
                    '-d', f'{{\"model\":\"{m[\"name\"]}\",\"keep_alive\":0}}'
                   ])
    print('unloaded', m['name'])
"
```

## **ChromaDB import fails**
```
ImportError: cannot import name 'BaseModel' from 'pydantic'
```
Use pro_hunter venv:
```bash
/home/t0n34781/projects/pro_hunter/.venv/bin/python YOUR_SCRIPT.py
```

## **LLM parse/score falls back to basic**
1. Check config was read correctly (see config_read_pattern in shn.json)
2. Confirm mistral:7b is responding: `time curl -s -X POST http://localhost:11434/api/generate -d '{"model":"mistral:7b","prompt":"OK","stream":false}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('response','')[:20])"`
3. If slow, another model may be loaded — force unload it

## **Scrape fails (captcha/block)**
Site is blocking local Playwright. Next tier (Firecrawl/BrowserUse) will be tried automatically. To force a specific tier, edit `strategy_tiers` in `config/sites.yaml`.

---

---

# **PART 6 — QUICK COMMAND REFERENCE**

---

## **Pro Hunter**
```bash
cd /home/t0n34781/projects/pro_hunter

# Single job
.venv/bin/python -m cli.main collect-score --url URL --site SITE --profile PROFILE

# Daily run
.venv/bin/python -m cli.main run-daily

# Daily — specific profiles
.venv/bin/python -m cli.main run-daily --profiles ai-sw-engineer,workmarket-contractor

# List collected jobs
.venv/bin/python -m cli.main list --min-score 50

# Search jobs by semantic query
.venv/bin/python -m cli.main query --text "remote Python AI" --k 5

# Apply (dry run)
.venv/bin/python -m cli.main apply --job-id JOB_ID
```

## **Badgr Harness**
```bash
cd /home/t0n34781/projects/badgr_harness

# Run orchestrator
python3 orchestrator.py

# Query RAG corpus
python3 rag_query.py

# Check RAG collections
/home/t0n34781/projects/pro_hunter/.venv/bin/python -c \
  "import chromadb; c=chromadb.PersistentClient(path='rag_db'); [print(col.name, col.count()) for col in c.list_collections()]"

# Run tests
pytest -q
```

## **Ollama**
```bash
# List loaded models
curl -s http://localhost:11434/api/ps

# Force unload
curl -s -X POST http://localhost:11434/api/generate -d '{"model":"MODEL","keep_alive":0}'

# Quick response test
time curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"mistral:7b","prompt":"OK","stream":false}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['response'][:20])"
```

## **Git**
```bash
# Pro Hunter
cd /home/t0n34781/projects/pro_hunter
git add FILE && git commit -m "msg" && git push origin main

# Check what's gitignored (credentials check)
git status --ignored | grep identity
```

---

*BADGRTechnologies LLC | github.com/Ch405-L9/Pro-Hunter-Agent*
