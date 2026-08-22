import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT))

from src.agent import SupportAgent
from src.knowledge_base import KnowledgeBaseLoader
from src.order_tool import OrderLookupTool
from src.retriever import KnowledgeRetriever


def build_agent() -> SupportAgent:
    loader = KnowledgeBaseLoader(
        ROOT / "knowledge-base"
    )

    documents = loader.load_documents()

    chunks = loader.chunk_documents(
        documents
    )

    retriever = KnowledgeRetriever(
        chunks
    )

    order_tool = OrderLookupTool(
        ROOT / "data" / "orders.json"
    )

    return SupportAgent(
        retriever=retriever,
        order_tool=order_tool,
    ) 


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if "cases" in data:
        return data["cases"]

    return data


def run_case(
    agent: SupportAgent,
    case: dict,
) -> tuple[bool, list[str]]:

    messages = case["messages"]
    expected = case["expect"]

    history = []
    response = None

    for message in messages:
        response = agent.respond(
            message["content"],
            history=history,
        )

        history.append(
            {
                "role": "user",
                "content": message["content"],
            }
        )

        history.append(
            {
                "role": "assistant",
                "content": response.answer,
            }
        )

    assert response is not None

    answer = response.answer.lower()
    failures = []

    for required in expected.get("must_include", []):
        if required.lower() not in answer:
            failures.append(
                f"missing required text: {required!r}"
            )

    for forbidden in expected.get("must_not_include", []):
        if forbidden.lower() in answer:
            failures.append(
                f"contains forbidden text: {forbidden!r}"
            )

    for required in expected.get("must_include_concepts", []):
        words = required.lower().split()

        if not all(word in answer for word in words):
            failures.append(
                f"missing concept: {required!r}"
            )

    for forbidden in expected.get("must_not_invent", []):
        if forbidden.lower() in answer:
            failures.append(
                f"contains invented information: {forbidden!r}"
            )

    for required_source in expected.get(
        "required_sources",
        [],
    ):
        if required_source not in response.sources:
            failures.append(
                f"missing source: {required_source!r}"
            )

    expected_handoff = expected.get("handoff")

    if (
        expected_handoff is not None
        and response.handoff != expected_handoff
    ):
        failures.append(
            f"handoff expected {expected_handoff}, "
            f"got {response.handoff}"
        )

    expected_tool = expected.get("tool")

    if expected_tool == "not_called":
        if response.tool_called is not None:
            failures.append(
                f"unexpected tool call: "
                f"{response.tool_called!r}"
            )

    elif expected_tool == "not_called_without_id":
        if response.tool_called is not None:
            failures.append(
                f"unexpected tool call without ID: "
                f"{response.tool_called!r}"
            )

    elif expected_tool:
        if response.tool_called != expected_tool:
            failures.append(
                f"expected tool {expected_tool!r}, "
                f"got {response.tool_called!r}"
            )

    expected_arguments = expected.get(
        "tool_arguments"
    )

    if expected_arguments:
        if response.tool_arguments != expected_arguments:
            failures.append(
                "tool arguments mismatch: "
                f"expected {expected_arguments!r}, "
                f"got {response.tool_arguments!r}"
            )

    return not failures, failures


def run_file(
    agent: SupportAgent,
    path: Path,
) -> list[dict]:

    cases = load_cases(path)
    results = []

    for case in cases:
        passed, failures = run_case(
            agent,
            case,
        )

        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "passed": passed,
                "failures": failures,
            }
        )

    return results


def print_results(
    title: str,
    results: list[dict],
) -> None:

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(
            f"[{status}] "
            f"{result['category']}: "
            f"{result['id']}"
        )

        for failure in result["failures"]:
            print(f"       - {failure}")

    total = len(results)
    passed = sum(
        result["passed"]
        for result in results
    )

    print()
    print(
        f"Result: {passed}/{total} passed"
    )

    categories = {}

    for result in results:
        category = result["category"]

        if category not in categories:
            categories[category] = {
                "passed": 0,
                "total": 0,
            }

        categories[category]["total"] += 1

        if result["passed"]:
            categories[category]["passed"] += 1

    print()
    print("Category results:")

    for category, stats in sorted(
        categories.items()
    ):
        print(
            f"  {category}: "
            f"{stats['passed']}/{stats['total']}"
        )


def main() -> int:

    agent = build_agent()

    visible_path = (
        ROOT
        / "evaluation"
        / "visible-cases.json"
    )

    original_path = (
        ROOT
        / "evaluation"
        / "original-cases.json"
    )

    visible_results = run_file(
        agent,
        visible_path,
    )

    original_results = run_file(
        agent,
        original_path,
    )

    print_results(
        "VISIBLE CASES",
        visible_results,
    )

    print_results(
        "ORIGINAL CASES",
        original_results,
    )

    all_results = (
        visible_results
        + original_results
    )

    failed = [
        result
        for result in all_results
        if not result["passed"]
    ]

    print()
    print("=" * 70)
    print(
        f"OVERALL: "
        f"{len(all_results) - len(failed)}"
        f"/{len(all_results)} passed"
    )
    print("=" * 70)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())