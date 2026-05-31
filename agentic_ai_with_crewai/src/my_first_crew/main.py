# main.py — Campaign Intelligence Crew
#
# PURPOSE:
# Entry point for running the crew.
# Provides runtime inputs, chooses the execution mode, and displays results.
#
# KEY CONCEPTS:
# - kickoff(inputs={}) injects dynamic values into agents.yaml + tasks.yaml
# - Execution modes: sync run, batch run, async run
# - Output inspection: CrewOutput (.tasks_output, .token_usage) + Pydantic fields


import sys
import warnings
import asyncio
from datetime import datetime
from my_first_crew.crew import CampaignCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# DISPLAY HELPERS — CrewOutput + TaskOutput inspection

def display_campaign_output(crew_result):
    """
    Shows how to access CrewOutput and TaskOutput objects.

    This function teaches three output access patterns:
      Pattern 1: result.pydantic          → Pydantic object
      Pattern 2: result["field_name"]     → dict-style indexing
      Pattern 3: result.pydantic.model_dump() → Python dict for DB/API
    """
    print("CREW OUTPUT INSPECTION")
    print(f"  Tasks completed : {len(crew_result.tasks_output)}")
    print(f"  Token usage     : {crew_result.token_usage}")

    # Individual TaskOutput per task
    print("  📋  TaskOutput — Per-Task Results")
    task_labels = ["Research Task", "Strategy Task", "Copy Task", "QA Review Task"]
    for i, task_out in enumerate(crew_result.tasks_output):
        label = task_labels[i] if i < len(task_labels) else f"Task {i+1}"
        print(f"\n  [{label}]")
        print(f"    .agent   = {task_out.agent}")
        print(f"    .summary = {task_out.summary}")
        print(f"    .raw     = {len(task_out.raw.split())} words")

    # CampaignReport (copy_task Pydantic output)
    print("  🎯  CAMPAIGN REPORT (CampaignReport Pydantic Object)")
    # Access pattern: the second-to-last task output has .pydantic
    campaign = None
    for task_out in crew_result.tasks_output:
        if task_out.pydantic and hasattr(task_out.pydantic, 'tagline'):
            campaign = task_out.pydantic
            break

    if campaign:
        print(f"\n  Product     : {campaign.product_name}")
        print(f"  Audience    : {campaign.target_audience}")

        print(f"\n TAGLINE (recommended)")
        print(f"      {campaign.tagline}")
        print(f" TAGLINE (alternative)")
        print(f"      {campaign.tagline_alternative}")

        print(f"\n  HERO HEADLINE")
        print(f"      {campaign.hero_headline}")
        print(f"\n  HERO SUBHEADLINE")
        print(f"      {campaign.hero_subheadline}")
        print(f"\n  VALUE PROPOSITION")
        print(f"      {campaign.value_proposition}")

        print(f"\n  KEY MESSAGES:")
        for i, msg in enumerate(campaign.key_messages, 1):
            print(f"      {i}. {msg}")

        print(f"\n  EMAIL SUBJECT LINES:")
        for i, subj in enumerate(campaign.email_subject_lines, 1):
            print(f"      {i}. {subj}")

        print(f"\n  CHANNELS (by priority):")
        for ch in campaign.recommended_channels:
            print(f"      • {ch}")

        # Pattern 2: dict-style access
        print(f"\n  Dict access: crew_result['tagline']")
        try:
            print(f"      → '{crew_result['tagline']}'")
        except Exception:
            print(f"      → Use task_out.pydantic.tagline instead")

        # Pattern 3: model_dump()
        print(f"\n  .model_dump() keys (for DB / API use):")
        print(f"      {list(campaign.model_dump().keys())}")

    else:
        print("\n  CampaignReport not found in task outputs.")
        print(f"  Raw output:\n{crew_result.raw[:400]}...")

    # QualityReport (qa_review_task Pydantic output)
    print("  QUALITY REVIEW (QualityReport Pydantic Object)")
    qa = None
    for task_out in crew_result.tasks_output:
        if task_out.pydantic and hasattr(task_out.pydantic, 'overall_score'):
            qa = task_out.pydantic
            break

    if qa:
        print(f"\n  Dimension Scores:")
        print(f"  ├─ Research Specificity    : {qa.research_specificity.score}/10")
        print(f"  │    {qa.research_specificity.justification[:80]}...")
        print(f"  ├─ Strategy Differentiation: {qa.strategy_differentiation.score}/10")
        print(f"  │    {qa.strategy_differentiation.justification[:80]}...")
        print(f"  ├─ Copy Quality            : {qa.copy_quality.score}/10")
        print(f"  │    {qa.copy_quality.justification[:80]}...")
        print(f"  └─ Strategy-Copy Alignment : {qa.strategy_copy_alignment.score}/10")
        print(f"       {qa.strategy_copy_alignment.justification[:80]}...")

        print(f"\n  ┌─ OVERALL SCORE    : {qa.overall_score}/10")
        print(f"  └─ LAUNCH VERDICT   : {qa.launch_verdict}")

        print(f"\n  HIGHEST-IMPACT IMPROVEMENT:")
        print(f"      {qa.highest_impact_improvement}")

    else:
        print("\n  QualityReport not found — check qa_review_task output.")

    print("\n  Files saved:")
    print("      output/campaign_report.md  (full markdown report)")
    print("      output/campaign_run.json   (structured JSON)")
    print("=" * 62 + "\n")


# RUN MODE 1: Single Campaign — kickoff()

def run():
    inputs = {
        "product_name"        : "FlowDesk",
        "product_description" : (
            "an AI-powered customer support platform that reduces ticket "
            "resolution time by 60% through automated triage, smart reply "
            "suggestions, and real-time sentiment detection for support teams"
        ),
        "target_market"       : "B2B SaaS companies with 50-500 employees",
        "current_year"        : str(datetime.now().year),
    }

    try:
        result = CampaignCrew().crew().kickoff(inputs=inputs)
        display_campaign_output(result)

    except ValueError as e:
        # Pydantic schema mismatch — LLM output didn't match the model
        print(f"\n Pydantic schema mismatch: {e}")
        print(f"  Fix: Check CampaignReport / QualityReport field definitions.")
        print(f"  Check that task expected_output matches the model structure.")

    except Exception as e:
        print(f"\n  ❌  Unexpected error: {type(e).__name__}: {e}")

    finally:
        print("Run attempt finished.\n")


# RUN MODE 2: Batch — kickoff_for_each()
def run_batch():
    print("\n" + "=" * 62)
    print("  BATCH RUN — kickoff_for_each()")
    print("  Same crew, 2 products, 2 independent campaign packages.")
    print("=" * 62 + "\n")

    batch_inputs = [
        {
            "product_name"        : "FlowDesk",
            "product_description" : (
                "an AI-powered customer support platform that reduces ticket "
                "resolution time by 60% through automated triage and smart replies"
            ),
            "target_market"       : "B2B SaaS companies with 50-500 employees",
            "current_year"        : str(datetime.now().year),
        },
        {
            "product_name"        : "PipelineIQ",
            "product_description" : (
                "a revenue intelligence tool that predicts deal close probability "
                "and surfaces real-time coaching cues for sales managers"
            ),
            "target_market"       : "Sales teams at mid-market B2B companies (100-1000 employees)",
            "current_year"        : str(datetime.now().year),
        },
    ]

    try:
        results = CampaignCrew().crew().kickoff_for_each(inputs=batch_inputs)

        print(f"\n  ✅  Batch complete — {len(results)} campaigns generated.\n")

        for i, (inp, result) in enumerate(zip(batch_inputs, results), 1):
            print(f"  [{i}] {inp['product_name']}")

            # Find CampaignReport in task outputs
            for task_out in result.tasks_output:
                if task_out.pydantic and hasattr(task_out.pydantic, 'tagline'):
                    c = task_out.pydantic
                    print(f"       Tagline  : {c.tagline}")
                    print(f"       Headline : {c.hero_headline}")
                    break

            # Find QualityReport in task outputs
            for task_out in result.tasks_output:
                if task_out.pydantic and hasattr(task_out.pydantic, 'overall_score'):
                    q = task_out.pydantic
                    print(f"       QA Score : {q.overall_score}/10 — {q.launch_verdict}")
                    break

            print()

    except Exception as e:
        print(f"\n  ❌  Batch run error: {type(e).__name__}: {e}")


# RUN MODE 3: Async — kickoff_async()
async def run_async():
    print("\n" + "=" * 62)
    print("  ⚡  ASYNC RUN — kickoff_async()")
    print("=" * 62 + "\n")

    inputs = {
        "product_name"        : "FlowDesk",
        "product_description" : "an AI-powered customer support platform",
        "target_market"       : "B2B SaaS companies with 50-500 employees",
        "current_year"        : str(datetime.now().year),
    }

    try:
        result = await CampaignCrew().crew().kickoff_async(inputs=inputs)
        print(f"\n  ✅  Async run complete.")

        for task_out in result.tasks_output:
            if task_out.pydantic and hasattr(task_out.pydantic, 'tagline'):
                print(f"  Tagline: {task_out.pydantic.tagline}")
                break

    except Exception as e:
        print(f"\n  ❌  Async error: {type(e).__name__}: {e}")


# CLI FUNCTIONS (train / replay / test)
def train():
    inputs = {
        "product_name"        : "FlowDesk",
        "product_description" : "an AI-powered customer support platform",
        "target_market"       : "B2B SaaS companies with 50-500 employees",
        "current_year"        : str(datetime.now().year),
    }
    try:
        CampaignCrew().crew().train(
            n_iterations=int(sys.argv[1]),
            filename=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"Training error: {e}")


def replay():
    try:
        CampaignCrew().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"Replay error: {e}")


def test():
    inputs = {
        "product_name"        : "FlowDesk",
        "product_description" : "an AI-powered customer support platform",
        "target_market"       : "B2B SaaS companies",
        "current_year"        : str(datetime.now().year),
    }
    try:
        CampaignCrew().crew().test(
            n_iterations=int(sys.argv[1]),
            eval_llm=sys.argv[2],
            inputs=inputs
        )
    except Exception as e:
        raise Exception(f"Test error: {e}")


def run_batch_sync():
    run_batch()

# ENTRY POINT
if __name__ == "__main__":
    run()