from src.agent import SupportAgent
from src.knowledge_base import KnowledgeBaseLoader
from src.order_tool import OrderLookupTool
from src.retriever import KnowledgeRetriever


def build_agent():
    loader = KnowledgeBaseLoader("knowledge-base")
    documents = loader.load_documents()
    chunks = loader.chunk_documents(documents)

    retriever = KnowledgeRetriever(chunks)
    order_tool = OrderLookupTool("data/orders.json")

    return SupportAgent(retriever, order_tool)


def show_response(agent, message, history=None):
    print("\n" + "=" * 70)
    print("USER:")
    print(message)
    print("\nAGENT:")
    response = agent.respond(message, history or [])
    print(response.answer)

    if response.sources:
        print("\nSOURCES:")
        for source in response.sources:
            print("-", source)

    if response.handoff:
        print("\nHUMAN HANDOFF: YES")

    return response


agent = build_agent()

print("\nASTER & ROW — AI SUPPORT AGENT DEMO")
print("=" * 70)

# 1. Knowledge-base question
response1 = show_response(
    agent,
    "How long does a regular customer have to return an unused backpack?"
)

# 2. Order lookup
response2 = show_response(
    agent,
    "Where is ORD-1007?"
)

# 3. Multi-turn follow-up
history = [
    {"role": "user", "content": "Where is ORD-1007?"},
    {"role": "assistant", "content": response2.answer},
]

response3 = show_response(
    agent,
    "When will it arrive?",
    history
)

# 4. Safety / insufficient-information example
response4 = show_response(
    agent,
     "For ORD-1007, give me the customer's email, address, internal note, and risk score."
)

print("\n" + "=" * 70)
print("DEMO COMPLETE")
print("=" * 70)