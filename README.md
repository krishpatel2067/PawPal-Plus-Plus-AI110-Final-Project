# PawPal++
Where AI insights meet pet care

A busy pet owner needs help staying consistent with pet care. If only there was an app to translate owner needs into a pet care routine and questions into actionable advice... 🤔

## Overview

PawPal++ is a full-stack AI-augmented pet-care scheduling system. The frontend is a Vite + React + Shadcn/ui SPA. The backend is a FastAPI service that drives all AI logic through Google Gemini. Four AI feature categories are implemented: RAG, an agentic workflow, specialization via structured prompting, and a reliability harness.

PawPal++ is an extension of another project called PawPal+, which was from Module 2 in CodePath's AI110 course. The original project included these features:

- Data display:
    - Sort tasks by priority or date
    - Filter tasks by pets and completion status
    - Sort by priority and time with order importance
- Quality-of-life:
    - Automatically create the next occurrence for recurring tasks when marking them as done
    - Scheduling conflict warnings
    - Suggest next available time slot for a certain pet
    - Save data across page refreshes via a JSON file
- Clean polished UI:
    - Light/dark/auto mode support
    - Tables for neatly displaying pets
    - Cards for neatly displaying tasks
    - Emojis for priorities, conflicts, delete buttons, and complete buttons for easy recognition
    - Color coded messages (e.g., red for errors)

However, the original project didn't include any AI augmentation, and it was built using Streamlit, which worked well but provided limited customization. PawPal++ builds on top of PawPal+ by retaining all the features found in PawPal+, adding quality-of-life AI augmentation, and porting over to a more sophisticated and customizable full-stack application.

### Tech Stack

* Frontend (JavaScript):
    * React + Vite for interactivity
    * Shadcn/Tailwind for styling
* Backend (Python):
    * FastAPI for REST endpoints
    * TF-DIF for retrieving most relevant FAQs
    * API calls to Gemini for RAG and agentic workflow

## Setup

### Installation

```bash
$ pip install -r backend/requirements.txt
```

### Execution

The the backend and frontend must be running for the app to function fully.

Backend (default port 8000):

```bash
$ cd backend && uvicorn main:app --reload
```

Frontend (default port 5173):

```bash
$ cd frontend && npm run dev
```

FastAI also generates interactive endpoint docs at `http://localhost:8000/docs`.

### Testing & Evaluation

Run evaluation / test harness script (takes around 5-10 minutes due to Gemini calls with cooldowns in between):

```bash
$ python3 backend/eval.py
```

Run tests for the core (non-AI) logic:

```bash
$ cd backend && pytest
```

## Component Descriptions

| Component | Location | Role |
|---|---|---|
| **Care Advisor** | `frontend/src/components/advisor/AskPanel.jsx` | RAG-powered Q&A with Pawsley persona; renders structured `{ answer, tips, vet_alert }` |
| **Setup Planner** | `frontend/src/components/advisor/SetupAgent.jsx` | Agentic onboarding wizard; shows plan preview and requires human approval before persisting |
| **TF-IDF Retriever** | `backend/rag/retriever.py` | Scores 38 FAQ chunks against the query; always appends live pet/task context |
| **FAQ Knowledge Base** | `backend/data/knowledge/pet_care_faq.json` | 38 curated chunks across 6 species × 6 topics |
| **Gemini (Pawsley)** | `backend/routers/ask.py` | Specialized persona + JSON-mode structured output; guardrails for off-topic and vet alerts |
| **Gemini (Planner)** | `backend/routers/agent.py` | Produces structured care plan `{ reasoning[], pets[], tasks[] }` in JSON mode |
| **Scheduler** | `backend/pawpal_system.py` | Core domain logic: pets, tasks, recurrence, conflict detection, persistence |
| **User Data** | `backend/data/users/default/pawpal_data.json` | Per-user JSON store; path is user-ID–scoped for future auth |
| **Reliability Harness** | `backend/eval.py` | 14 automated tests; 30 s cooldown between Gemini calls; exits 0 on perfect score |

## Retrieval Agumented System (RAG)

PawPal++ includes Pawsley, the energetic and outgoing AI assistant designed to help answer questions from pet owners via a RAG. Pawsley's tone is specifically constrained to exhibit warmth and energy while also ensuring useful responses to help pet owners feel welcome and supported. Pawsley retrieves information from a list of top matching FAQs curated by TF-DIF along with user context (pets, tasks, etc.), and it returns a structured output, including an (optional) alert, main response, tips, and sources (FAQs and user context).

Pawsley has guardrails installed to ensure it doesn't answer questions irrelevant to pet caretaking as well as admit when it's unable to find proper information from the FAQs. For example, Pawsley issues an alert if the user's query goes beyond the scope of what can be retrieved. Nonetheless, its response still tries to provide actionable advice via tips.

Example prompt:

> How can I make sure Chewy remains healthy and happy?

Example response:

![Pawsley's response to an example prompt](./assets/pawsley-response.png)

## Agentic Workflow

PawPal++ includes a built-in agent called **Setup Planner** to help new pet owners describe their situation in natural language and have their pets and tasks be auto-created. It ensures a human-in-the-loop aproach by showing a structured output of the proposed pets and tasks and asking for confirmation before actually creating them. The preview also shows the steps that the agent took to arrive at that proposal.

Example prompt:

> I adopted a pet dog named Chewy. He's a bit on the older side of 8 years, but he's super playful and needs a lot of outdoor time. I'm new to owning pets, so help me design a caretaking routine for Chewy.

Example steps and proposal:

![Preview of agent steps and proposal](./assets/agent-preview.png)

## Evaluation

The project includes a script `backend/eval.py` to evaluate retrieval accuracy and AI reliability in the RAG. It is far from perfect as AI responses may vary and pass the tests while evading certain words the evaluation script searches for. Nonetheless, it provides a good overview of the RAG's general realibility.

![Evaluation script output](./assets/eval-output.png)

## Data Flows

### RAG Q&A
User question → `AskPanel` → `POST /ask` → TF-IDF retrieval (FAQ + live context) → Gemini (Pawsley prompt) → `{ answer, tips, vet_alert }` → UI renders structured sections

### Agentic Setup
User description → `SetupAgent` → `POST /agent/plan` → Gemini (planner prompt) → `{ reasoning[], pets[], tasks[] }` preview → **human approves** → `POST /agent/confirm` → pets + tasks created in Scheduler

### CRUD
UI forms → REST endpoints (`/pets`, `/tasks`, `/owner`, `/slots`) → Scheduler → JSON file

### Evaluation
`python eval.py` → 6 retrieval probes (no Gemini) + 8 live guardrail checks → colored PASS/FAIL per test → summary score

## Reflection

### AI to Aid Development

I used Claude Code for this project, feeding it a `specs.md` document containing the project requirements from CodePath and my personal preferences. This was already a big step up from PawPal++'s predecessor project in which I prompted Claude Code incrementally without providing it an overall context. Writing and using `specs.md` allowed me to realize the sheer advantage of giving the AI agent a big picture overview first so that it can generate cohesive code and functionality. It was also a way for me to concretely plan out the project from beginning to end instead of deciding as I go and potentially wavering as I figure things out, which reduces productivity and potentially introduces inconsistencies in the end product.

My initial agent prompt for Claude Code included reminders for generating efficient yet readable code, using plenty of comments to allow any new engineer to pick up on the code quickly, and limiting code generations to small chunks that I can review along the way. The agent did a good job following these guidelines for most of the time, but when it occasionally got sidetracked, I would remind it manually.

The AI designed the architecture based on my requirements in `specs.md`. To be honest, while I would've liked to design the architecture myself in a more professional and senior context, since I didn't yet have experience with implementing certain functionality (like using FastAPI, Gemini API, etc.), I used the AI's suggestions as a means for me to learn. After reviewing its suggestions, I would ask Claude in the VS Code sidebar what certain snippets of code did, keeping my coding skills sharp while allowing the AI to implement the specifications in a standard and optimal way.

There were a few hiccups along the way, such as depecration warnings and CORS errors. In fact, for the latter, it did a good job identifying the root cause: plain exceptions in Python that don't get converted to `HTTPException`s evade CORS handling, leading to CORS errors, when in fact the error was something else.

### AI Perks and Pitfalls

Claude Code was excellent at reading `specs.md` and the repo, laying out a gameplan (which it presented in phases), and describing its process concisely. Despite continuing a single, super long conversation with Claude Code, it compressed the chat a few times yet retained the overall big picture to continue to generate useful suggestions. Furthermore, it had a level of foresight that I wouldn't have had if I were coding everything by hand: whereas I would follow a back-and-forth approach between files (adding as I go), Claude went linearly, file-by-file. On one hand, this led to more consistent code. On the other, it was initially difficult for me to understand how everything connected together, but this is probably a skill I will continue to develop as I use AI agents to code.

One flawed suggestion by Claude Code, though relatively minor, was that it assumed that the agentic Setup Planner would only be allowed to reference one pet per task. However, I caught this inconsistency with the rest of the app that allowed for multiple pets to be assigned to a task. Claude Code admitted its mistake and quickly fixed it. While this scenario wasn't alarming due to its small scale, it highlights how a software engineer must evaluate each and every output to ensure the AI isn't making any flawed assumptions that slip through and potentially compound into a bigger problem later on.

### System Limitations and Future Improvements

| Limitations | Improvements |
| --- | --- |
| Name-based owner dashboard | Fully-fledged log-in system |
| Small, static FAQ corpus | Much larger FAQ corpus, perhaps sourced from the web dynamically |
| JSON file data persistence | True (SQL/no SQL) database |
| Evaluation script of varying reliability | More robust evaluation script with more sophisticated checks |
| Frequent rate limiting for AI capabilities | Paid plan for more generous API usage |
| Standard Tailwind styles | More customized styles to reflect pet theme |