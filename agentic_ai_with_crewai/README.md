# 🚀 Campaign Intelligence Crew
### Building AI Agent with CrewAI

---

## What This Project Does

A **4-agent AI system** that generates a complete, self-reviewed product launch
campaign by coordinating specialized agents in a sequential pipeline:

**Input:** Product name, description, target market

**Output:**
- `CampaignReport` — tagline, headline, ad copy, email subjects, channel plan
- `QualityReport` — 4-dimension scores, overall score, launch readiness verdict
- `output/campaign_report.md` — full markdown report
- `output/campaign_run.json` — complete structured JSON

**Agent 1: Market Researcher**\
**Job**: Research the market.

It finds:
- Who the customers are
- Their problems
- Competitors
- Market trends
- Unique opportunities

**Output**: A research report.

**Agent 2: Campaign Strategist**\
**Job**: Create a marketing strategy.

It reads the research from Agent 1 and decides:
- Positioning statement
- Key marketing messages
- Channel strategy
- Competitive differentiation

**Output**: A campaign strategy.

**Agent 3: Copywriter**\
**Job**: Write marketing content.

It uses the strategy and creates:
- Taglines
- Headlines
- Landing page copy
- LinkedIn ads
- Email subject lines

**Output**: A structured ``CampaignReport``.

**Agent 4: QA Analyst**\
**Job**: Review everything.

It evaluates:
- Research quality
- Strategy quality
- Copy quality
- Alignment between strategy and copy
Then gives:
- Scores (1-10)
- Launch recommendation
- Suggested improvements

**Output**: A ``QualityReport``.

**Workflow**
The flow is:
```
Product Information
        │
        ▼
Market Researcher
 (Gemini Flash)
        │
        ▼
Campaign Strategist
 (Claude Sonnet)
        │
        ▼
    Copywriter
   (Claude Haiku)
        │
        ▼
    QA Analyst
  (Claude Haiku)
        │
        ▼
Final Campaign Package
```


This is defined in:
```
process=Process.sequential
```


**Each agent:**\
Has a different role\
Has a different goal\
Receives different instructions\
Performs a different task

That's the core idea of a multi-agent system.

**What is CrewAI doing here?**\
CrewAI acts as the manager.

It:
- Creates agents
- Assigns tasks
- Passes outputs between agents
- Runs them in order
- Collects final results

---

## The Scenario

**FlowDesk** — an AI-powered customer support platform — needs a full product
launch campaign. The crew researches the market, builds a strategy, writes all
copy, and then a 4th agent reviews and scores the entire campaign before launch.

The same crew can run for any product by changing the inputs in `main.py`.
`PipelineIQ` (a revenue intelligence tool) is included as a second example
for the batch run mode.

---

## Project Structure

```
my_first_crew/
├── .env                                  ← API keys (never commit this)
├── pyproject.toml                        ← Project config + CLI entry points
├── knowledge/
│   └── user_preference.txt               ← Project context for agents
└── src/my_first_crew/
    ├── crew.py                           ← Agents, Tasks, Pydantic models, Crew
    ├── main.py                           ← Entry point + 3 execution modes
    ├── config/
    │   ├── agents.yaml                   ← Agent identity (role/goal/backstory)
    │   └── tasks.yaml                    ← Task instructions + output specs
    └── tools/
        └── custom_tool.py                
```

---

## Agent Pipeline

| # | Agent | Model | Job | Output |
|---|---|---|---|---|
| 1 | `market_researcher` | Gemini 2.5 Flash | Buyer personas, competitor weaknesses, message territory | Research brief |
| 2 | `campaign_strategist` | Claude 4.5 Sonnet | Positioning statement, message pillars, channel ranking, 4-week arc | Strategy doc |
| 3 | `content_copywriter` | Claude 4.5 Haiku | Tagline, headline, subheadline, LinkedIn ad, email subjects, value prop | `CampaignReport` |
| 4 | `campaign_qa_analyst` | Claude 4.5 Haiku | Scores strategy + copy on 4 dimensions, delivers launch verdict | `QualityReport` |

---

## Setup

**1. Add your API keys to `.env`:**
```
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
```

Get your keys at:
- Anthropic → https://console.anthropic.com/
- Google → https://aistudio.google.com/app/apikey

**2. Install dependencies:**
```bash
crewai install
```

**3. Run the crew:**
```bash
crewai run
```

---

## Execution Modes

### Single run (default)
```bash
crewai run
```
Runs the full 4-agent pipeline for FlowDesk. Produces `CampaignReport` + `QualityReport`.

### Batch run — same crew, multiple products
```bash
crewai run run_batch
```
Runs the crew twice — once for FlowDesk, once for PipelineIQ. Returns 2 independent campaign packages.

### Other CLI commands
```bash
train    # Train the crew for N iterations
replay   # Replay from a specific task ID
test     # Test and evaluate crew performance
```
