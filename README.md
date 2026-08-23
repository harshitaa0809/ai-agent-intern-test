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

User: Where is ORD-1007?

Agent: The order is currently shipped.

User: When will it arrive?

Agent: The estimated delivery date is August 22, 2026.

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

User  
↓  
SupportAgent  
↓  
Intent and Safety Logic  
↓  
Knowledge Retriever / Order Tool  
↓  
Policy and Safety Rules  
↓  
Final Response  
↓  
Sources and Handoff

## Project Structure

The repository contains:

- `src/agent.py` — main support-agent logic
- `src/knowledge_base.py` — knowledge-base loading
- `src/retriever.py` — deterministic retrieval
- `src/order_tool.py` — controlled order lookup
- `src/models.py` — application models
- `src/llm.py` — optional LLM integration
- `tests/` — regression tests
- `evaluation/` — evaluation suite
- `knowledge-base/` — supplied knowledge documents
- `data/` — supplied order data

## Setup

### Requirements

- Python 3.12+
- Git

### Install

Clone the repository:

```text
git clone https://github.com/harshitaa0809/ai-agent-intern-test.git
cd ai-agent-intern-test
