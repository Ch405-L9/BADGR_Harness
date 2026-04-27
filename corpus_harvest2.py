#!/usr/bin/env python3
"""
corpus_harvest2.py — Second pass, tight keyword list only.
Drops into same corpus_harvest/ folder. Ctrl+C safe.
"""

import os, shutil, time
from pathlib import Path

SOURCE_DIR = "/home/t0n34781/BADGR LLC"
DEST_DIR   = "/home/t0n34781/projects/badgr_harness/corpus_harvest"
LOG_FILE   = "/home/t0n34781/projects/badgr_harness/corpus_harvest2_log.txt"

KEYWORDS = [
    # Project names / proper nouns — safe
    "soram", "heckles", "kerry",
    # CRM
    "crm", "crm_integration", "crm_setup", "crm_workflow", "crm_guide",
    # Comms tools — specific
    "telegram", "rocket_chat", "rocketchat", "rocket.chat",
    # Business structure
    "answering_service", "answering service",
    "enterprise_llm", "enterprise llm",
    "solutions_engineering", "solutions engineering",
    "workstation", "badgr_workstation",
    "badgr_llc", "llc_filing", "llc_docs", "llc_formation",
    # Funnels / leads — compound only
    "sales_funnel", "lead_funnel", "funnel_strategy", "funnel_plan",
    "lead_generation", "lead_gen", "lead generation",
    "lead_nurture", "lead_capture", "lead_magnet",
    # ROI / financials — compound only
    "roi_report", "roi_analysis", "roi_plan",
    "return_on_investment", "return on investment",
    # Automation — compound only
    "automate_workflow", "automation_plan", "automation_guide",
    "automation_strategy", "automation_blueprint",
    # Content / posting — compound only
    "content_creation", "content creator", "content_creator",
    "posting_schedule", "post_schedule", "posting schedule",
    # Media — compound only
    "video_strategy", "video_plan", "video_guide", "video_content",
    "audio_content", "audio_strategy", "audio_guide",
    # Contracts — compound only
    "badgr_contract", "client_contract", "service_contract",
    "contract_template", "contract_guide",
    # Alerts / calendar — compound only
    "badgr_alert", "alert_system", "alert_workflow",
    "badgr_calendar", "calendar_strategy", "calendar_plan",
    # MCP / RAG — compound only
    "mcp_setup", "mcp_integration", "mcp_guide", "mcp_workflow",
    "rag_setup", "rag_pipeline", "rag_guide", "rag_strategy",
    "rag_corpus", "rag_foundation",
    # Isolation — compound only
    "isolate_workflow", "isolation_plan", "isolation_strategy",
    # Facebook / social — compound only
    "facebook_ads", "facebook_strategy", "facebook_plan",
    "facebook_guide", "facebook_campaign",
    # Resources / assets — compound only
    "badgr_resources", "resource_guide", "resource_library",
    "badgr_assets", "asset_library", "asset_guide",
    # Subpage
    "subpage", "sub_page", "subpage_template",
    # Portfolio / profile — tighter than pass 1
    "badgr_portfolio", "badgr_profile", "portfolio_guide",
]

KEYWORDS_LOWER = [k.lower() for k in KEYWORDS]


def matches(stem: str) -> bool:
    s = stem.lower()
    return any(kw in s for kw in KEYWORDS_LOWER)


def safe_dest_path(dest_dir: Path, filename: str) -> Path:
    target = dest_dir / filename
    if not target.exists():
        return target
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = dest_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def main():
    source = Path(SOURCE_DIR)
    dest   = Path(DEST_DIR)
    dest.mkdir(parents=True, exist_ok=True)

    found = scanned = errors = 0
    start = time.time()

    print(f"Source  : {source}")
    print(f"Dest    : {dest}")
    print(f"Keywords: {len(KEYWORDS_LOWER)} terms (pass 2 — tight)")
    print("─" * 60)
    print("Running — Ctrl+C to stop safely.\n")

    with open(LOG_FILE, "w") as log:
        log.write(f"corpus_harvest2 — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Source: {source}\nDest: {dest}\n\n")

        try:
            for root, dirs, files in os.walk(source):
                dirs[:] = [d for d in dirs if Path(root, d) != dest]

                for fname in files:
                    scanned += 1
                    stem = Path(fname).stem

                    if not matches(stem):
                        continue

                    src_path = Path(root) / fname
                    try:
                        if src_path.stat().st_size == 0:
                            continue
                    except OSError:
                        errors += 1
                        continue

                    dest_path = safe_dest_path(dest, fname)
                    try:
                        shutil.copy2(src_path, dest_path)
                        found += 1
                        log.write(f"[{found:>5}] {src_path}  →  {dest_path.name}\n")
                        print(f"\r  Scanned: {scanned:,}  |  Harvested: {found:,}  |  "
                              f"Elapsed: {int(time.time()-start)}s   ", end="", flush=True)
                    except (OSError, shutil.Error) as e:
                        errors += 1
                        log.write(f"[ERR] {src_path}: {e}\n")

        except KeyboardInterrupt:
            print("\n\n[Stopped by user]")

    elapsed = int(time.time() - start)
    print(f"\n\n{'─'*60}")
    print(f"  Scanned  : {scanned:,} files")
    print(f"  Harvested: {found:,} → {dest}")
    print(f"  Errors   : {errors}")
    print(f"  Elapsed  : {elapsed}s")
    print(f"  Log      : {LOG_FILE}")


if __name__ == "__main__":
    main()
