# Specs

Most of the wording is directly from the project directions and rubric from CodePath AI110 Final Project.

## Current Project
The current project is called PawPal+, which is a Streamlit app designed to help pet owners manage and take care of their pets. The app allows them to enter their name, add their pets (name, species, age, notes), add tasks (name, description, start time, duration, frequency, priority, pets assigned), filter their tasks (by complete or incomplete), and sort their tasks (by priority or date & time). The app stores data in a JSON file that persists even after the page is refreshed. The app also has a quasi-intelligent feature: it can suggest the next available time slot when creating a task.

## Extension Introduction
This current project must be extended into a fully applied AI system. In addition to evolving the earlier prototype into a polished, professional artifact, the app must use AI in some way to support the app's core purpose, solves meaningful problem, or automates a reasoning task.

The feature should be fully integrated into the main application logic. It is not enough to have standalone script; the feature must meaningfully change how the system behaves or processes information. For example, if you add RAG, your AI should actively use the retrieved data to formulate its response rather than just printing the data alongside a standard answer.

## Examples

The extended app should do something useful with AI. For example:

* Summarize text or documents
* Retrieve information or data from a source
* Plan and complete a step-by-step task
* Help debug, classify, or explain something

| Extension Idea	| Added AI Components |
|---|---|
| Add retrieval of external documentation and automated validation of answers |	RAG + testing + guardrails |
| Integrate agentic planning and error-logging into the existing workflow	| Agentic loop + logging |
| Extend explanation module with bias detection and evaluation metrics	| RAG + validation |
| Add reliability scoring or self-critique loop	| Testing + confidence scoring |

The app must include at least one of the following AI features:

| Feature |	What It Means |	Example |
|---|---|---|
| Retrieval-Augmented Generation (RAG)	| Your AI looks up or retrieves information before answering.	| A study bot that searches notes before generating a quiz question. |
| Agentic Workflow	| Your AI can plan, act, and check its own work.	| A coding assistant that writes, tests, and then fixes code automatically. |
| Fine-Tuned or Specialized Model	| You use a model that’s been trained or adjusted for a specific task.	| A chatbot tuned to respond in a company’s tone of voice. |
| Reliability or Testing System	| You include ways to measure or test how well your AI performs.	| A script that checks if your AI gives consistent answers. |

## Requirements

These requirements apply while keeping in mind that the spirit of the original project is preserved since this is an extension. 

Substantial new AI feature:
* At least one substantial AI feature such as RAG, a multi-step agent or planning workflow, specialized behavior (mini fine-tune or structured prompting), or a reliability harness (evaluation loop, guardrails, self-checking).
* Feature is integrated into the working system (not an isolated demo).
* Feature is functional and produces meaningful changes in system behavior.

System architecture diagram:
* Diagram shows major components (UI/CLI, retrieval, agent, evaluator, database, etc.).
* Diagram clearly illustrates data flow (input → processing steps → output).
* Diagram matches actual project implementation (not theoretical).

Functional end-to-end system
* Working script or UI that demonstrates full system workflow.
* System runs end-to-end using the new AI feature.
* System responds consistently to at least 2-3 example inputs.

Reliability, evaluation, and guardrails:
* System includes a reliability mechanism such as input validation, output guardrails, self-critique or multi-model agreement, or an evaluation script that tests sample inputs.
* Mechanism is functional and meaningfully improves reliability.
* Guardrail/evaluator behavior can be easily shown in demostration.

Enhanced RAG: custom indexing or multi-source retrieval:
* Retrieval is extended to include custom documents, sections, or multi-source retrieval.
* The impact on output quality is demonstrated.

Agentic workflow enhancement:
* Multi-step reasoning with tool-calls, planning steps, or a decision-making chain is implemented.
* The agent's intermediate steps are observable in output.

Fine-tuning or specialization behavior:
* Specialized model behavior (few-shot patterns, synthetic datasets, or constrained tone/style) is demonstrated.
* Output measurably differs from baseline responses.

Test harness or evaluation script
* A script that evaluates the system on multiple predefined inputs is built and runs successfully.
* The script prints a summary of results (pass/fail score, confidence, or similar).

User experience and front-end:
* The app must be stylish yet simple.
* The app must be intuitive to use and follow common design paradigms.
* The app must adapt to accessbility settings (reduced transparency, animations, etc.).
* The app supports light, dark, and auto mode.
* The app includes a footer with the content:
    * PawPal++ - Where AI insights meet pet care
    * CodePath AI110 Final Project
    * Created by Krish A. Patel alongside Claude Code in April 2026
    * Powered by Google Gemini

## Diagram

Show how the app is organized by creating a short system diagram that includes:

* The main components (like retriever, agent, evaluator, or tester).
* How data flows through the system (input → process → output).
* Where humans or testing are involved in checking AI results.

## Testing

It must be proven that the AI in the app works, not just seem like it does. Include at least one way to test or measure its reliability, such as:

* Automated tests (e.g., unit tests or simple checks for key functions).
* Confidence scoring (the AI rates how sure it is).
* Logging and error handling (your code records what failed and why).
* Human evaluation (you or a peer review the AI's output).

## Implementation

* The app must use Vite + React.
* The app must use Shadcn + Tailwind.
* Most of the current Streamlit code can be directly converted into JavaScript.
* Python should be reserved for driving the core AI logic and manage API calls.
* There should be a clear bridge of communication between Python and JavaScript.

## Code Guidelines

* All code (both in Python and JavaScript) must be readable yet also performant.
* The code must be commented (unless the functionality is quickly obvious) to the point that a new engineer can easily pick up on what it is doing.
* The code must be modular, allowing for easy extentions in the future (such as full deployment, log-in system, etc.).
* The code must be robust and foolproof.
* Any errors must be gracefully handled and logged to the console.