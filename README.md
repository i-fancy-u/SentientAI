Project SentientGrid: An AI Diagnostic Assistant (Multi-Agent Architecture)
SentientGrid is an AI-powered diagnostic assistant that blends real-time SCADA sensor data with PDF-based technical manuals using large language models for smart routing, execution, and synthesis. It's built for industrial engineers to troubleshoot equipment efficiently using natural language.

This project represents Phase 2, transforming the previous Plan-Execute architecture into a more robust Multi-Agent System with explicit delegation and a Human-in-the-Loop component for enhanced control and reliability.

🚀 Quick Start
1. Clone and Set Up
git clone https://github.com/meethjaswani/SentientGrid_AI # Adjust if your repo name is different
cd SentientGrid_AI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt # Ensure this file is up-to-date with all dependencies

2. Add Your API Key
Create a .env file in the root directory:

GROQ_API_KEY=your_groq_api_key

This key is needed for:

Groq API → All LLM interactions (Planning, Replanning, Synthesis, and potentially SCADA/Manual query interpretation if those tools use LLMs).

3. Run the Multi-Agent System
python3 main.py

🗂️ Project Structure (New Multi-Agent Design)
SentientFinal/
├── data/
│   ├── pdf_manuals/         # Raw manuals (PDFs)
│   └── vector_store/        # Generated embeddings
├── agents/                  # NEW: Contains the specialized agents and orchestrator
│   ├── __init__.py          # Makes 'agents' a Python package
│   ├── diagnostic_state.py  # Shared state for agents
│   ├── planner_agent.py     # Creates diagnostic plans
│   ├── executor_agent.py    # Executes plan steps by delegating to tool agents
│   ├── scada_agent.py       # Interfaces with SCADA tool
│   ├── manual_agent.py      # Interfaces with Manual search tool
│   ├── replan_agent.py      # Decides next action (continue, synthesize, human intervention)
│   ├── synthesizer_agent.py # Generates comprehensive final answers
│   └── orchestrator.py      # Manages the overall multi-agent workflow and Human-in-the-Loop
│   └── utils.py             # Common utilities (e.g., LLM API helper)
├── graph/                   # (Previous LangGraph implementation - for reference/deprecated)
│   ├── ...                  # Contents of old graph folder
├── manual/
│   ├── create_vector_store.py   # PDF to vector pipeline
│   └── manual_search_tool.py   # Query vector DB
├── scada/
│   ├── generate_scada_db.py    # Simulated sensor database
│   └── scada_query_tool.py     # SCADA query + LLM fallback
├── .env
├── main.py                  # NEW: Main entry point for the multi-agent system
├── README.md
└── requirements.txt

💡 What It Can Do (Multi-Agent Capabilities)
SentientGrid answers complex technical questions by coordinating specialized AI agents:

🧠 Planner Agent → Creates a step-by-step diagnostic plan.

🔧 Executor Agent → Executes plan steps by delegating to specific tool agents.

📊 SCADA Agent → Interfaces with the SCADA system for sensor values (delegated by Executor).

📘 Manual Agent → Interfaces with the Manual search tool for procedures (delegated by Executor).

🤔 Replan Agent → Evaluates progress and decides if more steps are needed or if synthesis can occur.

🧬 Synthesizer Agent → Combines all gathered information for a comprehensive final answer.

👤 Human-in-the-Loop → Allows for human oversight and intervention at critical decision points.

Human-in-the-Loop (HITL) Feature
The system pauses at key decision points (after each major agent cycle) to allow a human operator to:

Review the current state, completed steps, and proposed next steps.

Approve the plan to continue execution.

Force Synthesis of a final answer if sufficient information is deemed gathered.

Manually Edit the remaining plan steps to guide the AI.

Abort the workflow if necessary.

This ensures greater control, accuracy, and prevents the AI from getting stuck or going off-track.

Examples
1. SCADA Only
🔍 What is the temperature in June?
📊 SCADA Insight: Avg 28.5°C, Range 26–33°C.
(System will pause for human review before proceeding or synthesizing)

2. Manual Only
🔍 How do I fix a leak?
📘 Manual Insight: Tighten inlet seals, see Page 12 of KUKA Manual.
(System will pause for human review before proceeding or synthesizing)

3. SCADA + Manual (with HITL Interaction)
🔍 Compressor pressure is fluctuating — what could be wrong?

# ... (Planner creates plan) ...
# ... (Executor runs SCADA step, gets high pressure reading) ...
# ... (Replan Agent decides to continue with Manual step) ...

--- HUMAN IN THE LOOP: Review Required ---
Current State Overview:
  User Query: Compressor pressure is fluctuating — what could be wrong?
  Completed Steps (1):
    1. SCADA: Get current compressor pressure readings
       Result Preview: Current pressure: 58 psi (high). Fluctuating between 55-60 psi...
  Next Planned Steps (1):
    1. MANUAL: Search for compressor pressure troubleshooting procedures

Options:
  'c' / 'continue': Proceed with the current plan.
  's' / 'synthesize': Force synthesis of a final answer now.
  'e' / 'edit': Manually edit the plan (experimental).
  'q' / 'quit': Abort the workflow.
Your decision (c/s/e/q): c  # Human decides to continue

# ... (Executor runs Manual step, finds troubleshooting guide) ...
# ... (Replan Agent decides to synthesize) ...

--- Synthesizer Step ---
✅ Synthesizer: Created comprehensive diagnostic analysis

🔧 FINAL DIAGNOSTIC ANSWER:
Question: Compressor pressure is fluctuating — what could be wrong?

📊 Data Analysis: Current compressor pressure is high (58 psi) and fluctuating between 55-60 psi, indicating an unstable operation.
📘 Procedural Guidance: Refer to the "Compressor Troubleshooting Guide" (Page 25) for detailed steps on diagnosing fluctuating pressure. Key areas to check include valve seals, air intake filters, and pressure regulator settings.
💡 Recommendations:
1. Immediately check the air intake filter for blockages.
2. Inspect all valve seals for any signs of wear or leakage.
3. Verify the pressure regulator settings are within the recommended operational range.
⚠️ Priority: High - fluctuating pressure can lead to inefficient operation and potential component wear.

🧭 Flow Overview (Multi-Agent)
User Query
   ↓
[Orchestrator]
   ↓ Calls [Planner Agent]
   ↓ (Plan created)
   ↓
   Loop:
     [Executor Agent] (Executes 1 step, delegates to SCADA/Manual Agents)
     [Replan Agent] (Decides next action)
     [Human-in-the-Loop] (Review/Approve/Edit)
   ↓ (Loop continues or exits)
   ↓
[Synthesizer Agent]
   ↓
✅ Final Answer

🔧 Dev Utilities
Regenerate SCADA DB
python3 -m scada.generate_scada_db

Rebuild Vector Store
python3 -c "from manual.create_vector_store import VectorStoreManager; VectorStoreManager().run_full_pipeline()"

🛠️ Requirements
Python 3.10+ (or Python 3.11+ as per original)

.env with GROQ_API_KEY

Optional: place any PDFs in data/pdf_manuals/ to enable manual lookup

🐛 Troubleshooting
Problem

Reason

Fix

ModuleNotFoundError

Missing package in virtual environment

source venv/bin/activate then pip install <missing_package> (or pip install -r requirements.txt)

NameError: name 'Dict' is not defined

Missing import for type hints

Add from typing import Dict, Any to the file

coroutine object has no attribute 'strip'

asyncio.to_thread result not awaited

Ensure await is used before asyncio.to_thread calls for input

API error: 4XX (e.g., 401, 403, 429)

Incorrect API key, quota exceeded, or rate limit hit

Verify GROQ_API_KEY in .env, check Groq console for quotas, wait and retry

No PDF documents found

No manuals in data/pdf_manuals/

Add at least 1 PDF

Planning failed / No valid steps

LLM failed to generate a valid plan

Try rephrasing the query or check LLM API access

🧪 Suggested Prompts to Try
"What is the average load in May?"
"How do I calibrate the sensor?"
"Compressor pressure is fluctuating — what could be wrong?"
"What's the safety procedure for high RPM shutdown?"
"Temperature is high in machine X, what should I do?"
