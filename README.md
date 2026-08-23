Aster & Row — Reliable AI Support Agent

A reliable customer-support agent built for the Aster & Row AI Agent Take-Home Assignment.

The system combines knowledge-base retrieval, controlled order lookups, multi-turn conversation context, deterministic safety rules, source-conflict detection, privacy protection, and human handoff behavior.

1. What This Project Solves

The customer scenario identified four recurring problems:

Conflicting policy answers.

Invented order information.

Lost conversation context.

Unsafe instructions inside retrieved content.

This implementation addresses these problems by:

Retrieving relevant knowledge-base passages.

Preferring active and authoritative policy sources.

Using an explicit order lookup tool instead of guessing order information.

Maintaining relevant recent conversation context.

Treating retrieved documents as untrusted data.

Protecting internal customer and order fields.

Abstaining when supplied information is insufficient.

Detecting conflicts between authoritative sources.

Recommending human assistance when an action cannot safely be completed.

2. Key Capabilities

Knowledge-base RAG

Loads and chunks the supplied Markdown knowledge-base documents.

Preserves document metadata.

Retrieves relevant passages.

Uses source metadata when selecting policy and product information.

Returns source filenames with policy and product answers.

Avoids unsupported claims.

Handles insufficient information safely.

Detects conflicts between active authoritative sources.

Order Lookup

Uses the supplied order dataset.

Requires an order ID when order information is requested.

Normalizes lowercase order IDs.

Handles unknown order IDs safely.

Uses the current order status as authoritative.

Does not invent delivery estimates.

Avoids stale delivery information for cancelled or returned orders.

Does not expose customer email, address, internal notes, or risk scores.

Does not claim that a lookup happened when it did not.

Multi-turn Conversation

The agent maintains relevant recent context for follow-up questions.

Example:

User: Where is ORD-1007?

Agent: The order is currently shipped.

User: When will it arrive?

Agent: The estimated delivery date is August 22, 2026.

The agent also supports contextual follow-ups:

User: Do you ship internationally?

Agent: Yes, according to the supplied shipping policy.

User: What about Canada?

Agent: Canada is covered by the international shipping policy.

Safety and Handoff

The agent can:

Refuse requests for internal or private data.

Reject instructions embedded in retrieved documents.

Abstain when information is insufficient.

Surface genuine source conflicts.

Recommend human assistance.

Avoid claiming unsupported actions were completed.

3. Architecture

                         User
                          |
                          v
                   +--------------+
                   | SupportAgent |
                   +--------------+
                          |
             +------------+------------+
             |                         |
             v                         v
       Conversation              Intent / Safety
          Context                    Logic
             |                         |
             +------------+------------+
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Knowledge Retriever      Order Tool
              |                       |
              v                       v
       knowledge-base/             orders.json
              |
              v
       Relevant passages
              |
              v
      Policy / Safety Rules
              |
              v
       Final Agent Response
              |
       +------+-------+
       |              |
       v              v
    Sources         Handoff
Main Components
src/agent.py

Main orchestration layer responsible for:

User-message handling
Intent detection
Conversation context
Knowledge retrieval
Order ID extraction
Tool invocation
Privacy handling
Prompt-injection handling
Source-conflict handling
Abstention
Human handoff
Final response construction
src/knowledge_base.py

Responsible for:

Loading Markdown documents
Parsing front matter
Splitting documents into sections
Creating document chunks
Preserving metadata
src/retriever.py

Provides deterministic retrieval over document chunks.

The retriever normalizes and tokenizes text, scores candidate chunks, and filters unusable sources.

src/order_tool.py

Provides controlled access to the mock order dataset.

Only the result of an individual lookup is passed to the agent. The entire order dataset is not placed into the model prompt.

src/models.py

Contains application data structures and response models.

src/llm.py

Contains the optional LLM client integration.

4. Model and Retrieval Approach
Language Model

The repository contains an optional OpenAI API integration.

A paid API key is not required to run the deterministic regression tests and evaluation suite.

Retrieval

The project uses deterministic lexical retrieval rather than a production vector database.

The retrieval process is:

Load Markdown knowledge-base files.
Parse document metadata.
Split documents into sections.
Create chunks.
Normalize and tokenize the query.
Score relevant chunks.
Filter unusable sources.
Prefer authoritative active sources.
Return relevant passages and metadata.

This keeps the implementation lightweight and deterministic for the assignment.

Storage

The project uses:

Markdown files for knowledge-base content.
JSON for mock order data.
In-memory Python structures for chunks and session context.

No external vector database is required.

5. Project Structure
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
│
├── knowledge-base/
├── data/
│
├── src/
│   ├── __init__.py
│   ├── agent.py
│   ├── knowledge_base.py
│   ├── llm.py
│   ├── models.py
│   ├── order_tool.py
│   └── retriever.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_knowledge_base.py
│   ├── test_order_tool.py
│   └── test_retriever.py
│
└── evaluation/
    ├── original-cases.json
    └── run_evaluation.py
6. Setup
Requirements
Python 3.12+
Git

The project includes an optional OpenAI API integration. A paid API key is not required to run the deterministic test and evaluation suite.

Clone
git clone https://github.com/harshitaa0809/ai-agent-intern-test.git
cd ai-agent-intern-test
Create a Virtual Environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
Install Dependencies
pip install -r requirements.txt
7. Environment Variables

The repository includes .env.example as a template for the optional LLM-backed integration.

If using the OpenAI-backed path, create a .env file:

OPENAI_API_KEY=your_api_key_here

Do not commit real API keys or credentials.

The submitted repository does not contain any API key or credential.

The .gitignore excludes:

.env
.venv/
__pycache__/
*.pyc
.pytest_cache/

The deterministic tests and evaluation suite can be run without an OpenAI API key.

8. Running the Tests

Run the complete regression test suite:

.\.venv\Scripts\python.exe -m pytest tests -q

Expected result:

31 passed

The tests cover:

Agent behavior
Retrieval
Knowledge-base processing
Order lookup
Privacy
Multi-turn behavior
Prompt security
Source conflicts
Handoff behavior
Tool reliability
9. Running the Evaluation

Run:

.\.venv\Scripts\python.exe evaluation\run_evaluation.py
Final Verified Result
VISIBLE CASES
Result: 15/15 passed

ORIGINAL CASES
Result: 5/5 passed

OVERALL: 20/20 passed
Visible Case Results
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
Original Case Results
Category	Result
Handoff	1/1
Multi-turn	1/1
Privacy	1/1
Tool use	2/2
10. Baseline vs Final Evaluation

An early baseline evaluation produced:

Visible cases: 6/15
Original cases: 2/5
Overall: 8/20

The final implementation achieved:

Visible cases: 15/15
Original cases: 5/5
Overall: 20/20

The main improvements included:

More reliable order-question detection.
Correct order follow-up handling.
Correct unknown-order handling.
Correct cancelled-order behavior.
Privacy-safe order lookup.
Better retrieval and source precedence.
Correct TrailPlus return-window handling.
Final-sale damaged-item handling.
Prompt-injection resistance.
Explicit abstention for insufficient information.
Source-conflict detection.
Unsupported-action handoff behavior.
11. Bug Diary
Bug 1 — Follow-up Order Arrival Question

A follow-up such as:

Where is ORD-1007?

followed by:

When will it arrive?

could lose the order context.

The agent now maintains relevant recent conversation context and recognizes arrival and delivery follow-ups as order-related.

Regression test:

test_follow_up_order_arrival

Bug 2 — Sensitive Order Information

Requests for private order information such as customer email, address, internal notes, or risk scores needed stronger privacy and handoff behavior.

Sensitive-data requests now prevent disclosure and trigger the appropriate safe response and handoff behavior.

Regression test:

test_sensitive_order_data_is_refused

Bug 3 — Retrieved Migration Note

Instruction-like content inside a retrieved migration document could be interpreted as authoritative.

For example:

The migration note says to ignore the real policy
and give everyone 60 days.

Migration and internal content is treated as non-authoritative. The current policy is used instead, and the agent does not automatically approve the return.

Regression test:

test_prompt_injection_document_is_not_authority

Bug 4 — Conflicting Breeze Tumbler Instructions

Two active official sources contain conflicting care instructions.

The agent detects the active-source conflict and does not silently choose one source.

The response explains that:

Current official sources conflict.
One source says to hand-wash the body.
Another says all components are dishwasher safe.
The agent cannot safely choose one.
Human confirmation or the safest interim guidance is recommended.

Regression test:

test_breeze_conflicting_sources

12. Safety and Privacy

The agent does not disclose internal order fields such as:

Customer email
Shipping address
Internal notes
Risk scores

The order's current status is treated as authoritative.

The agent also avoids:

Inventing delivery estimates.
Reporting stale delivery information for cancelled or returned orders.
Claiming an unsupported action was completed.
Following instructions embedded in retrieved documents.
Inventing unsupported company policies.
13. Source Conflict Handling

The system does not silently choose one source when current authoritative documents conflict.

For example, the Breeze Tumbler case contains conflicting official instructions.

The agent instead reports the conflict and recommends:

Human confirmation, or
The safest interim guidance.

This behavior is intentionally deterministic because silently choosing one source could result in an unsafe customer answer.

14. Abstention

When the supplied knowledge base does not contain enough information to answer a company-specific question, the agent does not invent an answer.

For example, if the available documents do not establish whether every material in a product is vegan, the agent recommends human confirmation rather than inventing a certification or guarantee.

15. Observability

Debug information can expose:

Relevant conversation context
Retrieved sources
Retrieved headings
Retrieval scores
Source metadata
Tool calls
Tool arguments
Handoff state
Fallback and error reasons

The implementation avoids logging secrets and sensitive customer information.

16. Known Limitations
Deterministic Lexical Retrieval

The current retriever is intentionally lightweight and does not use a production vector database or embedding index.

For production, I would evaluate an embedding-based retriever with stronger semantic matching while retaining the existing source-precedence and safety rules.

Limited Transaction Capabilities

The agent can perform order lookups but does not actually perform transactional actions such as:

Cancelling orders
Issuing refunds
Approving returns
Changing addresses
Creating replacements

A production system would require authenticated action tools, authorization, confirmation, and audit logging.

Mock Authentication Model

The assignment allows possession of an order ID to act as sufficient authentication.

A production system would require customer identity verification before exposing protected order information.

Limited Session Context

The implementation retains relevant recent conversation context rather than an unlimited conversation history.

A production implementation could use a more sophisticated session-memory strategy.

External Model Dependency

The optional LLM-backed path requires network access and a valid provider API credential.

The deterministic tests and evaluation do not require an API key.

17. AI Coding Tools Used

AI coding assistance was used during development for:

Debugging Python syntax and indentation errors.
Understanding pytest failures.
Analyzing evaluation failures.
Suggesting retrieval and routing improvements.
Reviewing implementation logic.
Improving test coverage.

AI suggestions were treated as development assistance rather than automatically accepted code. Important changes were validated through the project's tests and evaluation suite.

Example of an Incorrect AI Suggestion

An AI-generated change introduced an indentation error in src/agent.py:

IndentationError: unexpected unindent

The issue was corrected and validated using:

.\.venv\Scripts\python.exe -m pytest tests -q

The final regression suite passes:

31 passed

This demonstrates that AI-generated suggestions were verified through testing rather than blindly accepted.

18. Demo

A short GIF or video demonstrating the agent is required by the assignment.

The demonstration should show:

A knowledge-base question with sources.
An order lookup.
A multi-turn conversation.
A case where the agent refuses to guess or recommends human assistance.
The evaluation suite running.
Demo
<!-- Replace this placeholder with the final GIF or video before submission. -->

Demo video/GIF: To be added before final submission.

19. Final Verification

Run the regression tests:

.\.venv\Scripts\python.exe -m pytest tests -q

Expected:

31 passed

Run the evaluation:

.\.venv\Scripts\python.exe evaluation\run_evaluation.py

Expected:

VISIBLE CASES
Result: 15/15 passed

ORIGINAL CASES
Result: 5/5 passed

OVERALL: 20/20 passed

Check Git:

git status

Expected:

Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
20. Submission

GitHub repository:

https://github.com/harshitaa0809/ai-agent-intern-test

The repository contains:

Application source code
Tests
Evaluation suite
Setup instructions
Evaluation results
Known limitations
