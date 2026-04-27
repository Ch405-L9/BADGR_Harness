#!/usr/bin/env python3
"""
corpus_harvest.py
Scans a source directory, matches filenames against a keyword list,
copies matches to a flat output folder. Files only. Fast. Stoppable.
"""

import os
import shutil
import sys
import time
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
SOURCE_DIR  = "/home/t0n34781/BADGR LLC"
DEST_DIR    = "/home/t0n34781/projects/badgr_harness/corpus_harvest"
LOG_FILE    = "/home/t0n34781/projects/badgr_harness/corpus_harvest_log.txt"
# ─────────────────────────────────────────────────────────────────────────────

KEYWORDS = [
    # Business Foundation
    "business_plan","business_plan_","business_plan_v","business_plan_2025",
    "business_plan_badgr","BADGR_Business_Plan","BADGR_Business_Plan_2025",
    "business_overview","company_overview","company_profile","company_summary",
    "company_pitch","pitch_deck","pitch_deck_badgr","pitch_deck_BADGR",
    "investor_pitch","investor_deck","mission","vision","mission_vision",
    "mission_vision_values","values","core_values","strategic_goals",
    "business_goals","business_objectives","service_offering","service_offerings",
    "service_menu","services_list","service_catalog","rate_card","rate_cards",
    "pricing_sheet","pricing_sheets","pricing_model","pricing_models",
    "pricing_strategy","pricing_plan","service_pricing","service_package",
    "service_packages","offerings","service_offering_badgr","BADGR_Services",
    "BADGR_Service_Menu","badgr_business","badgr_business_content",
    # Operations
    "sop","sops","standard_operating_procedure","standard_operating_procedures",
    "operation_manual","operations_manual","ops_manual","workflow","workflows",
    "process_document","process_documents","process_doc","process_docs",
    "business_process","business_processes","process_map","process_mapping",
    "org_structure","org_notes","organization_structure","department_breakdown",
    "department_notes","team_structure","team_notes","onboarding",
    "client_onboarding","client_onboarding_doc","client_onboarding_docs",
    "onboarding_guide","onboarding_checklist","client_checklist","client_kickoff",
    "client_kickoff_checklist","client_setup","client_setup_guide",
    "client_setup_doc","client_setup_docs","client_handbook",
    "client_handbook_badgr","operations_plan","operations_strategy",
    "ops_strategy","ops_guidelines","ops_policy","ops_policy_badgr",
    # Projects
    "project_summary","project_summaries","project_brief","project_briefs",
    "project_outline","project_outline_badgr","project_matrix","past_project",
    "past_projects","previous_project","previous_projects","completed_project",
    "completed_projects","in_progress_project","in_progress_projects",
    "abandoned_project","abandoned_projects","project_architecture",
    "project_blueprint","deliverable","deliverables","deliverable_description",
    "deliverable_descriptions","deliverables_matrix","deliverables_list",
    "deliverables_summary","case_study","case_studies","case_study_badgr",
    "results_summary","results_document","results_doc","performance_report",
    "performance_reports","project_report","project_reports","project_launch",
    "project_launch_plan","project_launch_strategy","project_launch_summary",
    "project_proposal","project_proposals","proposal","proposals",
    "client_proposal","client_proposals","client_pitch","client_pitch_deck",
    "client_pitch_doc","proposal_badgr","BADGR_Project_Proposal",
    "BADGR_Project_Proposal_","BADGR_Project_Brief","project_portfolio",
    "project_portfolio_badgr","BADGR_Project_Portfolio","BADGR_Project_Summary",
    # Technical
    "architecture","architecture_doc","architecture_docs","system_architecture",
    "system_architecture_badgr","system_blueprint","system_blueprints",
    "technical_blueprint","technical_blueprints","stack","tech_stack",
    "technology_stack","software_stack","software_stack_notes","tool_stack",
    "tool_stack_notes","API_key","API_keys","API_key_list","API_keys_list",
    "API_keys_inventory","API_integrations","API_integration_notes","API_docs",
    "API_documentation","API_guide","API_reference","API_spec","API_specification",
    "API_endpoints","infrastructure","infrastructure_notes","infrastructure_doc",
    "infrastructure_docs","infrastructure_blueprint","infrastructure_map",
    "server_setup","server_setup_notes","deployment_plan","deployment_strategy",
    "deployment_documentation","dev_ops","devops","dev_ops_notes","devops_notes",
    "devops_guide","devops_blueprint","devops_workflow","devops_pipeline",
    "CI_CD","CI_CD_pipeline","CI_CD_workflow","build_process","build_workflow",
    "build_pipeline","build_strategy","build_plan","build_notes","build_blueprint",
    "build_documentation","build_guide","build_manual","build_manual_badgr",
    "build_strategy_badgr","build_workflow_badgr","build_documentation_badgr",
    # Brand / Marketing
    "brand_guidelines","brand_guideline","brand_guide","brand_manual",
    "brand_manual_badgr","brand_book","brand_style_guide","brand_style_manual",
    "brand_identity","brand_identity_badgr","brand_voice","brand_voice_guide",
    "brand_persona","brand_persona_guide","ICP","ICP_notes","target_market",
    "target_market_notes","target_audience","target_audience_notes",
    "customer_persona","customer_personas","customer_profile","customer_profiles",
    "campaign_plan","campaign_plans","marketing_campaign","marketing_campaigns",
    "marketing_plan","marketing_plans","marketing_strategy","marketing_strategy_badgr",
    "marketing_guide","marketing_guide_badgr","marketing_blueprint",
    "marketing_blueprint_badgr","marketing_worksheet","marketing_worksheet_badgr",
    "marketing_calendar","marketing_calendars","content_calendar","content_calendars",
    "content_schedule","content_scheduling","content_plan","content_plans",
    "content_strategy","content_strategy_badgr","social_media_plan",
    "social_media_strategy","social_media_guide","social_media_guide_badgr",
    "social_media_workflow","social_media_workflow_badgr","ad_campaign",
    "ad_campaigns","ad_strategy","ad_guide","social_marketing",
    "social_marketing_prompt_ware","social_marketing_guide",
    "social_marketing_guide_badgr","social_media_prompt_ware",
    "social_media_prompt_ware_badgr",
    # Financial
    "budget","budget_outline","budget_outlines","budget_plan","budget_plans",
    "budget_document","budget_documents","budget_sheet","budget_sheets",
    "budget_summary","budget_summary_badgr","budget_guide","budget_guide_badgr",
    "revenue_goal","revenue_goals","revenue_model","revenue_models",
    "revenue_plan","revenue_plans","revenue_strategy","revenue_strategy_badgr",
    "expense","expenses","expense_category","expense_categories",
    "expense_categories_list","expense_category_list","expense_summary",
    "expense_summary_badgr","income_statement","income_statements",
    "profit_loss","profit_and_loss","cash_flow","cash_flow_statement",
    "cash_flow_statements","financial_plan","financial_plans",
    "financial_document","financial_documents","financial_summary",
    "financial_summary_badgr","financial_guide","financial_guide_badgr",
    "financial_blueprint","financial_blueprint_badgr","financial_report",
    "financial_reports","financial_report_badgr","financial_statement",
    "financial_statements","financial_statement_badgr",
    # BADGR Harness / project-specific
    "badgr_harness","harness_phase","shn","phase_report","bolt_prompt",
    "badgr_analyst","badgr_lab","badgr_pro","catalog_badgr","RAG_foundation",
]

# Lowercase set for fast O(1) substring matching
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

    found = 0
    scanned = 0
    errors = 0
    start = time.time()

    print(f"Source : {source}")
    print(f"Dest   : {dest}")
    print(f"Log    : {LOG_FILE}")
    print(f"Keywords: {len(KEYWORDS_LOWER)} terms")
    print("─" * 60)
    print("Running — Ctrl+C to stop safely at any time.\n")

    with open(LOG_FILE, "w") as log:
        log.write(f"corpus_harvest run — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Source: {source}\nDest: {dest}\n\n")

        try:
            for root, dirs, files in os.walk(source):
                # Skip the dest dir if it somehow ends up inside source
                dirs[:] = [d for d in dirs if Path(root, d) != dest]

                for fname in files:
                    scanned += 1
                    stem = Path(fname).stem

                    if not matches(stem):
                        continue

                    src_path = Path(root) / fname

                    # Skip zero-byte files
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
                        entry = f"[{found:>5}] {src_path}  →  {dest_path.name}\n"
                        log.write(entry)
                        print(f"\r  Scanned: {scanned:,}  |  Harvested: {found:,}  |  "
                              f"Elapsed: {int(time.time()-start)}s   ", end="", flush=True)
                    except (OSError, shutil.Error) as e:
                        errors += 1
                        log.write(f"[ERR] {src_path}: {e}\n")

        except KeyboardInterrupt:
            print("\n\n[Stopped by user]")

    elapsed = int(time.time() - start)
    print(f"\n\n{'─'*60}")
    print(f"  Scanned : {scanned:,} files")
    print(f"  Harvested: {found:,} files copied to {dest}")
    print(f"  Errors  : {errors}")
    print(f"  Elapsed : {elapsed}s")
    print(f"  Log     : {LOG_FILE}")


if __name__ == "__main__":
    main()
