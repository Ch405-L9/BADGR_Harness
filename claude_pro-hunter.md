Below is a ready‑to‑paste “master prompt” you can give to Manus AI and Claude to build this end‑to‑end system. It references the tools/URLs, uses your local models when possible, and emphasizes staying on task and delivering a complete, next‑gen solution.

You can adapt the wording, but I’d start with this nearly verbatim.

Master build prompt for Manus AI / Claude
ROLE & GOAL

You are a senior AI systems engineer and full‑stack developer.
Your task is to design and implement a complete, next‑generation, AI‑assisted job search and application system for me, end‑to‑end (from web scraping to tracking and form filling).

You MUST:

Use and/or integrate the tools and projects listed below (or clearly justified upgrades).

Use my local models (Ollama) wherever reasonable, and only fall back to cloud models when necessary.

Implement a robust, multi‑tier scraping + fallback strategy (open source → self‑hosted → freemium → paid).

Produce working, well‑structured code and configs, not just high‑level ideas.

Deliver a system that I can run on my Ubuntu 24.04 workstation.

MY ENVIRONMENT
OS: Ubuntu 24.04.4 LTS, AMD Ryzen 5 5500 (12 threads), 16 GB RAM, AMD RX 6500 XT.

Local LLMs (Ollama):

nomic-embed-text:latest

kimi-k2.5:cloud

mistral:7b

qwen2.5-coder:7b

qwen2.5:14b

badgr-analyst:latest

llama3.2:latest

dmape-qwen:latest

rockn/qwen2.5-omni-7b-q4_k_m:latest

llama3.1:8b

phi3:mini

gemma2:2b

llama3.2:3b

Assume Python, virtualenv, Git, Docker, Playwright are available or can be installed.

CORE REFERENCES (YOU MUST STUDY AND LEVERAGE)
Treat these as core design references and potential dependencies:

Agenty / scrapingai – AI‑assisted scraping agents with proxies, captchas, screenshots, PDF, HTML extraction.

https://github.com/Agenty/scrapingai

Career‑Ops (AI job search system on Claude Code) – multi‑agent pipeline for job search, evaluation, and PDFs.

Overview: https://santifer.io/career-ops-system

Product page: https://www.producthunt.com/products/santifer-io

(“GitHub – santifer/career‑ops” as referenced in LinkedIn.)

BrowserUse (Python SDK) – LLM‑driven real browser automation for login, clicks, forms, etc.

https://github.com/browser-use/browser-use-python

Firecrawl – API to search, scrape, and interact with web at scale, with markdown/HTML outputs and agent mode.

OSS repo: https://github.com/firecrawl/firecrawl

Docs: https://docs.firecrawl.dev/introduction

Job‑search automation workflows – scraping + AI to mass‑customize and track applications (Medium, YouTube, etc.).

Use these as conceptual patterns; you don’t need exact URLs, just follow the “scrape → score → customize → track” pattern.

If you find clearly superior, compatible alternatives (e.g., newer browser automation, better open‑source scrapers), you may propose them, but you must explain and justify changes.

HIGH‑LEVEL SYSTEM I WANT
Build a modular job‑search agent system that:

Scrapes job opportunities from multiple sources:

Major job boards (e.g., Indeed, LinkedIn, Wellfound, etc., as legally allowed).

Company career pages.

Contract / freelance platforms.

Opportunity sources related to my new UEI / federal contracts (treat this as “government & contracting boards”; design a site‑config layer so we can plug in SAM.gov or similar later).

Uses a tiered, fallback scraping strategy per site:

Tier 0: Local open‑source stack (Requests/HTTPX, Playwright/Selenium, BeautifulSoup/Scrapy).

Tier 1: Self‑hosted Firecrawl for URL → markdown/HTML.

Tier 2: Firecrawl cloud or BrowserUse SDK for challenging interactive pages.

Tier 3: Agenty / scrapingai or other paid API as last resort for stubborn, high‑value sites.

The scraper must:

Detect and handle failures (captcha, 4xx/5xx, empty body, anti‑bot) and escalate to the next tier.

Record which method was used (scrape_method) for each job for cost/quality tuning.

Normalizes job data into a consistent schema:

Fields like: title, company, location, remote/onsite, salary, description, posting date, URL, etc.

Parses and cleans data from raw HTML/markdown (from Firecrawl / BrowserUse / Agenty outputs).

Scores jobs against my skill profiles (Career‑Ops‑style):

Uses local LLMs (e.g., qwen2.5:14b, llama3.1:8b) to:

Compute fit_score_overall, fit_score_must_have, fit_score_nice_to_have, fit_score_location.

Generate short fit_notes explaining why this job fits or doesn’t.

Supports multiple “skill modes” (e.g., python-automation, ai-agents, federal-contracts) inspired by Career‑Ops’ 14 skill modes.

Tracks applications in a CSV‑based “job CRM”:

Writes to a well‑structured CSV (and optionally SQLite/Postgres) with:

Job metadata & scores.

Workflow fields: status, priority, application_channel, resume_version, resume_customized, cover_letter_sent, application_submitted, application_date, recruiter/contact info, followup_1/2 dates and flags, last_contact, outcome.

Supports automated or assisted form filling:

For job application forms and government / contract portals:

Detect typical fields (name, address, company info, UEI, etc.).

Assist or automate filling using BrowserUse or similar browser automation.

Use structured data or a config for my company and UEI info.

Uses my local models by default:

For parsing, entity extraction, scoring, and simple reasoning:

Use local Ollama models (qwen2.5:14b, mistral:7b, llama3.x, etc.).

Only fall back to cloud models (e.g., Claude, OpenAI, Kimi) for tasks where local models clearly underperform or latency is acceptable.

Provide a clear configuration file to choose which model is used for:

Extraction

Scoring

Resume/cover letter customization

Code generation (for new site scrapers)

Implements a cost‑aware, quality‑aware strategy:

Prioritize open‑source and self‑hosted tools (local stack, Firecrawl self‑hosted) for the bulk of scraping.

Use freemium/paid tiers sparingly, preferably only for:

High‑priority companies.

Government / contracting sites where missing an opportunity is expensive.

Include config for:

Daily/monthly call quotas per provider.

Per‑site strategy and allowed tiers.

Is production‑ready and maintainable:

Clean project structure.

Clear config files for:

Sites and selectors.

Skill profiles.

Provider credentials and strategy ordering.

Logging, error handling, and simple observability (e.g., logs for failures and method usage).

Basic tests for core parsers and fit‑scoring logic.

CSV SCHEMA REQUIREMENTS (JOB CRM)
Design and implement a CSV schema similar to this (you may refine and extend):

job_id (unique)

source_site

job_title

company_name

company_website

job_url

location_raw

location_type (onsite/hybrid/remote)

country

posted_date

scraped_date

employment_type

salary_raw

salary_min

salary_max

salary_currency

salary_period

tech_stack (tags)

seniority

description_snippet

Fit / scoring:

skill_profile

fit_score_overall

fit_score_must_have

fit_score_nice_to_have

fit_score_location

fit_notes

Workflow / schedule‑keeper:

status (backlog, shortlisted, to_apply, applied, interviewing, offer, rejected, archived)

priority

application_channel

resume_version

resume_customized (yes/no)

cover_letter_sent (yes/no)

application_submitted (yes/no)

application_date

recruiter_name

recruiter_email

recruiter_linkedin

followup_1_due_date

followup_1_done

followup_1_notes

followup_2_due_date

followup_2_done

followup_2_notes

last_contact_date

last_contact_type

outcome

scrape_method (local, firecrawl_self_hosted, firecrawl_cloud, browseruse, agenty, etc.)

The system must be able to create, append, and update this CSV reliably.

ARCHITECTURE & MODULES
Please propose and then implement a concrete repo layout. For example (you can refine):

config/

sites.yaml – per‑site configuration, search URLs, selectors, strategy tiers.

providers.yaml – API keys, quotas, tier ordering.

skills.yaml – one or more skill profiles and constraints.

identity.yaml – my personal + business info (including UEI, etc.) for form filling.

scrapers/

base.py – base interfaces & data models.

local_playwright.py

firecrawl_client.py (self‑hosted + cloud).

browseruse_client.py.

agenty_client.py.

strategy.py – tiered fallback logic per URL/site.

parsers/

job_parser.py – transforms raw HTML/markdown into normalized job objects.

form_parser.py – detects and maps form fields for application pages.

llm/

client_ollama.py – wrappers for local models.

client_cloud.py – wrappers for Claude/other models where needed.

scoring.py – fit scoring, skill mode handling.

resume_customizer.py – generates tailored resume/cover letter snippets.

pipeline/

collector.py – builds search URLs, queues jobs.

runner.py – orchestrates scraping, parsing, scoring, CSV updates.

scheduler.py – logic for periodic runs (you can just design it; I can wire cron later).

storage/

csv_io.py – read/write/update CSV with schema above.

Optionally: db.py – SQLite/Postgres integration.

cli/

Command‑line entry points:

collect-jobs

score-jobs

update-csv

apply-job (to trigger form‑filling workflows).

docs/

SETUP.md – clear setup instructions for Ubuntu 24.04.

USAGE.md – how to run the pipeline, change configs, add new sites.

ARCHITECTURE.md – overview of modules, data flow, and extensibility.

FORM FILLING & GOVERNMENT / CONTRACTING
You must:

Design a generic form‑filling subsystem using BrowserUse or similar that can:

Log in (where appropriate), navigate to application pages.

Detect standard fields (name, address, company info, UEI, etc.).

Fill them from identity.yaml + job‑specific info (company, position, job ID).

Allow a “dry‑run/preview” mode before actually submitting.

Anticipate integrating federal/contracting sites:

Provide a pattern for site‑specific adapters (e.g., sam_gov_adapter.py) that plug into the same pipeline.

Ensure the architecture is flexible enough to add those later without rewrites.

QUALITY, “NEXT‑GEN” REQUIREMENTS
Use modern Python, type hints, and clean abstractions.

Aim for robustness: defensive coding, clear error messages, and timeouts.

Keep scraping respectful (rate limits, backoff, robots.txt awareness where applicable).

Make it easy to:

Add new job sources.

Add or tweak a skill mode.

Swap the default LLM model.

If using cloud services or paid tools, label clearly where they are used and provide configuration switches to disable them.

WHAT I EXPECT FROM YOU
A clear, step‑by‑step architecture proposal based on the above.

Then, actual code and config files implementing the core pipeline:

Scraping with tiered fallback.

Normalization into job objects.

Fit scoring with local models.

CSV writing/updating with the full schema.

Documentation so I can:

Set up the environment.

Add/edit sites and skill profiles.

Run daily/weekly job searches.

Use the form‑filling feature safely.

Stay on task. Do not get lost in unrelated frameworks. The priority is a working, maintainable system that combines these tools into a coherent, production‑grade job search and application engine tailored to my skill set and my contracting/UEI context.
