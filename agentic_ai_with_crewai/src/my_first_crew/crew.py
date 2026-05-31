# crew.py — Campaign Intelligence Crew
#
# PURPOSE:
# Orchestrates the multi-agent system.
# Connects agent identity (agents.yaml), task definitions (tasks.yaml),
# model configuration, structured outputs, and execution flow.
#
# ARCHITECTURE:
# - @CrewBase links this class to YAML configuration files.
#     self.agents_config → config/agents.yaml
#     self.tasks_config  → config/tasks.yaml
#
# - Structured Outputs:
#     Uses Pydantic models (CampaignReport, QualityReport)
#     to enforce predictable, production-ready results.
#
# - Lifecycle Hooks:
#     @before_kickoff  → runs before execution (validation/logging)
#     @after_kickoff   → runs after execution (saving/reporting)

from crewai import Agent, Crew, Process, Task
from crewai import LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import json
import os


# PYDANTIC OUTPUT MODEL
class DimensionScore(BaseModel):
    score: int = Field(
        description="Score from 1 (poor) to 10 (exceptional)",
        ge=1, le=10
    )
    justification: str = Field(
        description="2-sentence explanation of why this score was given"
    )


class QualityReport(BaseModel):
    research_specificity: DimensionScore = Field(
        description="How specific and named the research findings are"
    )
    strategy_differentiation: DimensionScore = Field(
        description="How uncopyable the positioning is from competitors"
    )
    copy_quality: DimensionScore = Field(
        description="How specific, human, and on-strategy the copy is"
    )
    strategy_copy_alignment: DimensionScore = Field(
        description="How well the copy executes the strategy"
    )
    overall_score: float = Field(
        description="Average of all 4 dimension scores, rounded to 1 decimal"
    )
    launch_verdict: str = Field(
        description=(
            "One of: LAUNCH READY | LAUNCH WITH MINOR REVISIONS | "
            "REVISE BEFORE LAUNCH | DO NOT LAUNCH — REBUILD REQUIRED"
        )
    )
    highest_impact_improvement: str = Field(
        description=(
            "The single most important change to improve campaign quality. "
            "Specific: what to change, why, what better looks like."
        )
    )


class CampaignReport(BaseModel):
    product_name: str = Field(
        description="Name of the product being launched"
    )
    target_audience: str = Field(
        description="Primary buyer persona in one sentence"
    )
    tagline: str = Field(
        description="Recommended tagline, max 8 words, benefit-driven"
    )
    tagline_alternative: str = Field(
        description="Alternative tagline option, max 8 words"
    )
    hero_headline: str = Field(
        description="Landing page hero headline, max 12 words, pain-led"
    )
    hero_subheadline: str = Field(
        description="1-2 sentences expanding the headline with specific outcome"
    )
    value_proposition: str = Field(
        description="One-line value prop, max 20 words, follows the template"
    )
    key_messages: List[str] = Field(
        description="List of 3 messages: primary pillar + 2 secondary messages"
    )
    recommended_channels: List[str] = Field(
        description="5 channels ranked by priority with one-line rationale each"
    )
    ad_copy: str = Field(
        description="LinkedIn ad: hook + problem + solution + CTA, max 4 sentences"
    )
    email_subject_lines: List[str] = Field(
        description="5 subject lines labeled by angle: curiosity, pain, benefit, social proof, question"
    )


# TASK CALLBACK WITH TIMING
_task_start_times: dict = {}

def task_started_tracker(task_name: str):
    _task_start_times[task_name] = datetime.now()

def task_completed_callback(output):
    agent_name = output.agent or "Unknown Agent"
    summary    = output.summary or "No summary"
    word_count = len(output.raw.split()) if output.raw else 0

    # Calculate elapsed time if we have a start time recorded
    elapsed = ""
    for task_name, start_time in _task_start_times.items():
        elapsed_sec = (datetime.now() - start_time).seconds
        elapsed = f" | ⏱  {elapsed_sec}s"
        break

    print(f"\nTask complete  |  Agent: {agent_name}{elapsed}")
    print(f"{summary}")
    print(f"Output: {word_count} words\n")
    print("  " + "─" * 58)


# CREW CLASS
@CrewBase
class CampaignCrew():
    agents: List[BaseAgent]
    tasks: List[Task]

    # BEFORE / AFTER KICKOFF DECORATORS
    @before_kickoff
    def before_run(self, inputs: dict):
        """Runs before the crew starts. Validates inputs and prints config."""
        print("\n" + "=" * 62)
        print("  🚀  CAMPAIGN INTELLIGENCE CREW — STARTING")
        print("=" * 62)
        print(f"  Product     : {inputs.get('product_name', 'N/A')}")
        print(f"  Market      : {inputs.get('target_market', 'N/A')}")
        print(f"  Year        : {inputs.get('current_year', 'N/A')}")
        print(f"  Agents      : 4  (Researcher → Strategist → Copywriter → QA)")
        print(f"  Started at  : {datetime.now().strftime('%H:%M:%S')}")

        # Record crew start time for total elapsed tracking
        _task_start_times['_crew_start'] = datetime.now()
        return inputs

    @after_kickoff
    def after_run(self, output):
        elapsed = ""
        if '_crew_start' in _task_start_times:
            total_sec = (datetime.now() - _task_start_times['_crew_start']).seconds
            elapsed = f"{total_sec // 60}m {total_sec % 60}s"

        print("\n" + "=" * 62)
        print("  🏁  CREW RUN COMPLETE")
        print("=" * 62)
        print(f"  Total time   : {elapsed}")
        print(f"  Tasks run    : {len(output.tasks_output)}")
        print(f"  Token usage  : {output.token_usage}")

        # Save full structured output to JSON
        os.makedirs("output", exist_ok=True)
        output_data = {
            "run_timestamp" : datetime.now().isoformat(),
            "elapsed"       : elapsed,
            "tasks_completed": len(output.tasks_output),
            "raw_output"    : output.raw,
        }
        if output.pydantic:
            output_data["structured_output"] = output.pydantic.model_dump()

        with open("output/campaign_run.json", "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"  Report saved : output/campaign_report.md")
        print(f"  JSON saved   : output/campaign_run.json")
        print("=" * 62 + "\n")
        return output

    # CONFIGURE LLM MODELS
    @property
    def gemini_flash(self) -> LLM:
        return LLM(
            model="gemini-2.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.4,
            max_tokens=1000
        )

    @property
    def claude_sonnet(self) -> LLM:
        return LLM(
            model="claude-sonnet-4-5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3,
            max_tokens=1400
        )

    @property
    def claude_haiku(self) -> LLM:
        return LLM(
            model="claude-haiku-4-5",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.5,
            max_tokens=1200
        )

    # DEFINE AGENTS
    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['market_researcher'], 
            llm=self.gemini_flash,
            verbose=True
        )

    @agent
    def campaign_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['campaign_strategist'],  
            llm=self.claude_sonnet,
            verbose=True
        )

    @agent
    def content_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config['content_copywriter'],  
            llm=self.claude_haiku,
            verbose=True
        )

    @agent
    def campaign_qa_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['campaign_qa_analyst'], 
            llm=self.claude_haiku,
            verbose=True
        )

    # DEFINE TASKS 
    @task
    def research_task(self) -> Task:
        task_started_tracker("research_task")
        return Task(
            config=self.tasks_config['research_task'],  
            callback=task_completed_callback
        )

    @task
    def strategy_task(self) -> Task:
        task_started_tracker("strategy_task")
        return Task(
            config=self.tasks_config['strategy_task'],  
            callback=task_completed_callback
        )

    @task
    def copy_task(self) -> Task:
        task_started_tracker("copy_task")
        return Task(
            config=self.tasks_config['copy_task'], 
            output_pydantic=CampaignReport,
            callback=task_completed_callback
        )

    @task
    def qa_review_task(self) -> Task:
        task_started_tracker("qa_review_task")
        return Task(
            config=self.tasks_config['qa_review_task'],  
            output_pydantic=QualityReport,
            callback=task_completed_callback
        )

    # ASSEMBLE THE CREW
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
