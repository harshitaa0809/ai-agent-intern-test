# Aster & Row — Reliable AI Support Agent

A reliable customer-support agent built for the Aster & Row AI Agent Take-Home Assignment.

The agent uses knowledge-base retrieval, controlled order lookups, conversation context, privacy protection, safety rules, source-conflict detection, and human handoff.

## What This Project Solves

The project addresses four main customer-support problems:

1. Conflicting policy answers.
2. Invented order information.
3. Lost conversation context.
4. Unsafe instructions inside retrieved content.

## Key Features

### Knowledge Base Retrieval

- Retrieves relevant information from the supplied knowledge base.
- Uses authoritative and active sources.
- Returns source information with answers.
- Handles insufficient information safely.
- Detects conflicts between official sources.

### Order Lookup

- Uses the supplied order dataset.
- Requires an order ID for order-specific questions.
- Supports lowercase order IDs.
- Handles unknown orders safely.
- Uses current order status.
- Does not invent delivery dates.
- Does not expose private customer information.
- Does not expose internal notes or risk scores.

### Multi-turn Conversation

The agent remembers relevant recent conversation context.

Example:

**User:** Where is ORD-1007?

**Agent:** The order is currently shipped.

**User:** When will it arrive?

**Agent:** The estimated delivery date is August 22, 2026.

### Safety and Handoff

The agent:

- Refuses private-data requests.
- Rejects prompt-injection instructions in retrieved documents.
- Abstains when information is insufficient.
- Detects conflicting official sources.
- Uses human handoff when necessary.
- Does not claim unsupported actions were completed.

## Architecture

The main flow is:

```text
User
  |
  v
SupportAgent
  |
  v
Intent and Safety Logic
  |
  +----------------------+
  |                      |
  v                      v
Knowledge Retriever   Order Tool
  |                      |
  +----------+-----------+
             |
             v
      Policy / Safety Rules
             |
             v
       Final Response
             |
       +-----+-----+
       |           |
       v           v
    Sources     Handoff

```
##Project Structure

The repository contains:

src/agent.py — main support-agent logic
src/knowledge_base.py — knowledge-base loading
src/retriever.py — deterministic retrieval
src/order_tool.py — controlled order lookup
src/models.py — application models
src/llm.py — optional LLM integration
tests/ — regression tests
evaluation/ — evaluation suite
knowledge-base/ — supplied knowledge documents
data/ — supplied order data
##Setup
###Requirements
Python 3.12+
Git
###Clone the Repository
git clone https://github.com/harshitaa0809/ai-agent-intern-test.git
cd ai-agent-intern-test
###Install Dependencies
pip install -r requirements.txt
##Environment Variables

The project contains an optional OpenAI integration.

An OpenAI API key is not required to run the deterministic tests and evaluation suite.

If the optional LLM integration is used, create a .env file:
```
OPENAI_API_KEY=your_api_key_here
```
Do not commit real API keys or credentials.

The repository uses .gitignore to exclude .env, .venv, Python cache files, and pytest cache files.

##Running the Tests

Run the regression test suite:
```
.\.venv\Scripts\python.exe -m pytest tests -q
```
Final result:
```
31 passed
```
The tests cover:

Agent behavior
Retrieval
Knowledge-base processing
Order lookup
Privacy
Multi-turn conversation
Prompt security
Source conflicts
Handoff behavior
Tool reliability
##Running the Evaluation

Run:
```
.\.venv\Scripts\python.exe evaluation\run_evaluation.py
```
Final verified result:
```
VISIBLE CASES
Result: 15/15 passed

ORIGINAL CASES
Result: 5/5 passed

OVERALL: 20/20 passed
```
###Evaluation Categories
Category	Result
Abstention	1/1
Conversation	1/1
Groundedness	2/2
Multi-source grounding	1/1
Privacy	1/1
Prompt security	1/1
Retrieval	2/2
Source conflict	1/1
Tool reliability	3/3
Tool use	2/2
Handoff	1/1
Multi-turn	1/1
##Baseline vs Final

The early baseline evaluation produced:
```
Visible cases: 6/15
Original cases: 2/5
Overall: 8/20
```
The final implementation achieved:
```
Visible cases: 15/15
Original cases: 5/5
Overall: 20/20
```
The main improvements included:

More reliable order-question detection.
Correct order follow-up handling.
Correct unknown-order handling.
Correct cancelled-order handling.
Privacy-safe order lookup.
Better retrieval and source precedence.
Correct TrailPlus return-window handling.
Prompt-injection resistance.
Abstention for insufficient information.
Source-conflict detection.
Unsupported-action handoff behavior.
##Safety and Privacy

The agent does not:

Invent order information.
Expose customer email or shipping address.
Expose internal notes or risk scores.
Invent unsupported company policies.
Follow instructions embedded in untrusted retrieved documents.
Claim unsupported actions were completed.
Silently choose one source when authoritative sources conflict.

When information is insufficient, the agent recommends human confirmation instead of inventing an answer.

##Known Limitations
###Deterministic Retrieval

The current retriever uses lightweight lexical retrieval instead of a production vector database.

A production implementation could use embeddings or a vector database while retaining the current source-precedence and safety rules.

###Transactional Actions

The agent can perform order lookups but does not perform transactional actions such as:

Cancelling orders
Issuing refunds
Approving returns
Changing addresses
Creating replacements

These actions would require authenticated tools, authorization, confirmation, and audit logging.

###Authentication

The assignment uses an order ID for the mock lookup flow.

A production system would require stronger customer authentication before exposing protected order information.

###Session Context

The implementation retains relevant recent conversation context rather than an unlimited conversation history.

##AI Coding Assistance

AI coding assistance was used during development for:

Debugging Python errors.
Understanding pytest failures.
Analyzing evaluation failures.
Improving routing and retrieval logic.
Reviewing implementation ideas.

AI suggestions were not blindly accepted. Important changes were validated using the regression tests and evaluation suite.

Final verification:
```
31 tests passed
20/20 evaluation cases passed
```
##Demo

The assignment requires a short GIF or video showing the agent working.

The demo should show:

A knowledge-base question.
An order lookup.
A multi-turn conversation.
A safety or human-handoff case.
The evaluation suite passing.

Demo: Add the final GIF or video here before submission.

##Final Verification

Run:
```
.\.venv\Scripts\python.exe -m pytest tests -q
```
Expected:
```
31 passed
```
Run:
```
.\.venv\Scripts\python.exe evaluation\run_evaluation.py
```
Expected:
```
OVERALL: 20/20 passed
```
Check Git:
```
git status
```
Expected:
```
nothing to commit, working tree clean
```
##Repository

https://github.com/harshitaa0809/ai-agent-intern-test

The repository contains:

Application source code
Tests
Evaluation suite
Setup instructions
Evaluation results
Known limitations
