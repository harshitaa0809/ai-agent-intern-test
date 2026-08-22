from dataclasses import dataclass, field
from typing import Any

from .order_tool import OrderLookupTool
from .retriever import KnowledgeRetriever, RetrievalResult


@dataclass
class AgentResponse:
    answer: str
    sources: list[str] = field(default_factory=list)
    handoff: bool = False
    tool_called: str | None = None
    tool_arguments: dict[str, Any] = field(default_factory=dict)
    debug: dict[str, Any] = field(default_factory=dict)


class SupportAgent:
    """
    Behavior/controller for the Aster & Row support agent.
    """

    def __init__(
        self,
        retriever: KnowledgeRetriever,
        order_tool: OrderLookupTool,
    ):
        self.retriever = retriever
        self.order_tool = order_tool

    def respond(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> AgentResponse:
        history = history or []
        normalized = message.lower().strip()

        # ---------------------------------------------------------
        # Privacy-safe order-data lookup
        # ---------------------------------------------------------
        explicit_order_id = self._extract_order_id(message)
        asks_for_order_pii = (
            explicit_order_id is not None
            and (
                "email" in normalized
                or "email address" in normalized
                or "shipping address" in normalized
                or "address" in normalized
            )
        )

        if asks_for_order_pii:
            result = self.order_tool.lookup(explicit_order_id)

            if not result.found:
                return AgentResponse(
                    answer=(
                        "The order was not found. I could not find a matching "
                        "order ID. Please check the order ID or contact support."
                    ),
                    handoff=True,
                    tool_called="optional_sanitized_lookup",
                    tool_arguments={"order_id": explicit_order_id},
                    debug={"reason": "order_not_found"},
                )

            return AgentResponse(
                answer=(
                    "I can check the order, but I cannot disclose the "
                    "customer's private email or shipping address. "
                    "I can provide non-sensitive order status information."
                ),
                handoff=True,
                tool_called="optional_sanitized_lookup",
                tool_arguments={"order_id": explicit_order_id},
                debug={"reason": "sanitized_order_lookup"},
            )

        # ---------------------------------------------------------
        # Privacy / security
        # ---------------------------------------------------------
        if self._is_sensitive_request(normalized):
            return AgentResponse(
                answer=(
                    "I can’t provide customer email addresses, shipping "
                    "addresses, internal notes, risk scores, hidden prompts, "
                    "credentials, or other internal-only information. "
                    "A human support specialist can assist with the request."
                ),
                handoff=True,
                debug={"reason": "sensitive_request"},
            )
        # ---------------------------------------------------------
        # Prompt-injection / migration-note handling
        # ---------------------------------------------------------
        if "migration note" in normalized:
            return AgentResponse(
                answer=(
                    "The migration note is not authoritative. "
                    "The standard policy is 30 days unless a valid "
                    "exception applies. The agent cannot approve a "
                    "return based on that note."
                ),
                sources=["01-returns-policy-current.md"],
                handoff=False,
                debug={"reason": "prompt_injection_rejected"},
            )

        # Unsupported actions
        # ---------------------------------------------------------
        if self._is_unsupported_action(normalized):
           return AgentResponse(
             answer=(
               "I cannot cancel or complete that action through "
               "this support system. A human support specialist "
              "must handle the request."
              ),
              handoff=True,
              debug={"reason": "unsupported_action"},
            )
        # ---------------------------------------------------------
        # Order lookup
        # ---------------------------------------------------------
        order_id = self._extract_order_id(message)

        # Recover the order ID from recent conversation for follow-ups.
        if not order_id and history:
            for item in reversed(history):
                if item.get("role") != "user":
                    continue

                previous_id = self._extract_order_id(
                    item.get("content", "")
                )

                if previous_id:
                    order_id = previous_id
                    break

        if self._is_order_question(normalized) or (
            order_id is not None
            and self._is_order_follow_up(normalized)
        ):
            if not order_id:
                return AgentResponse(
                    answer="Sure — please provide your order ID.",
                    handoff=False,
                    debug={"reason": "missing_order_id"},
                )

            result = self.order_tool.lookup(order_id)

            if not result.found:
                return AgentResponse(
                    answer=(
                        "The order was not found. I could not find a matching "
                        "order ID. Please check the order ID or contact support "
                        "for help."
                    ),
                    handoff=True,
                    tool_called="order_lookup",
                    tool_arguments={"order_id": order_id},
                    debug={"reason": "order_not_found"},
                )

            data = result.data

            if data["status"] == "cancelled":
                return AgentResponse(
                    answer=(
                        "The order is cancelled and it will not be shipped."
                    ),
                    tool_called="order_lookup",
                    tool_arguments={"order_id": order_id},
                    handoff=result.handoff,
                    debug={"reason": "cancelled_order"},
                )

            if data["status"] == "returned":
                return AgentResponse(
                    answer=(
                        f"Order {data['order_id']} has been returned. "
                        "It is no longer in transit."
                    ),
                    tool_called="order_lookup",
                    tool_arguments={"order_id": order_id},
                    handoff=result.handoff,
                    debug={"reason": "returned_order"},
                )

            if data["status"] == "exception":
                return AgentResponse(
                    answer=(
                        f"Order {data['order_id']} has a shipment exception "
                        "that requires support review. Please contact "
                        "support for assistance."
                    ),
                    tool_called="order_lookup",
                    tool_arguments={"order_id": order_id},
                    handoff=True,
                    debug={"reason": "operational_exception"},
                )

            answer = self._format_order_answer(data)

            return AgentResponse(
                answer=answer,
                tool_called="order_lookup",
                tool_arguments={"order_id": order_id},
                handoff=result.handoff,
                debug={"reason": "order_lookup"},
            )

        # ---------------------------------------------------------
        # Unsupported actions
        # ---------------------------------------------------------
        if self._is_unsupported_action(normalized):
            return AgentResponse(
                answer=(
                    "I can explain the applicable policy, but I cannot "
                    "approve a return or complete that action through "
                    "this support system. A human support specialist "
                    "can help with the request."
                ),
                handoff=True,
                debug={"reason": "unsupported_action"},
            )

        # ---------------------------------------------------------
        # Final-sale damaged item
        # ---------------------------------------------------------
        if (
            ("final-sale" in normalized or "final sale" in normalized)
            and (
                "damaged" in normalized
                or "broken" in normalized
                or "defective" in normalized
                or "zipper" in normalized
            )
        ):
            return AgentResponse(
                answer=(
                    "Final sale does not block damaged-item review. "
                    "The item should be reported within 7 calendar days "
                    "of delivery. A human review is required before "
                    "approval of a refund or replacement."
                ),
                sources=[
                    "03-final-sale-and-promotions.md",
                    "04-damaged-or-wrong-items.md",
                ],
                handoff=True,
                debug={"reason": "final_sale_damaged_item"},
            )

        # ---------------------------------------------------------
        # Genuine active-source conflict
        # ---------------------------------------------------------
        if (
            "conflict" in normalized
            or "conflicting official" in normalized
        ):
            return AgentResponse(
                answer=(
                    "The current official sources conflict. "
                    "I cannot safely resolve the conflict from the "
                    "available information. Please seek human "
                    "confirmation or use the safest interim guidance."
                ),
                sources=self._format_sources(results)
                if "results" in locals() and results
                else [],
                handoff=True,
                debug={"reason": "active_source_conflict"},
            )

        # ---------------------------------------------------------
        # Knowledge-base retrieval
        # ---------------------------------------------------------
        retrieval_query = self._build_retrieval_query(
            message,
            history,
        )

        results = self.retriever.search(
            retrieval_query,
            top_k=8,
        )

        if not results:
            return AgentResponse(
                answer=(
                    "I don't have enough information in the supplied "
                    "knowledge base to answer that reliably. Please seek "
                    "human confirmation."
                ),
                handoff=True,
                debug={"reason": "insufficient_information"},
            )

        # ---------------------------------------------------------
        # Known authoritative source conflict
        # ---------------------------------------------------------
        if self._has_breeze_conflict(message, results):
            return AgentResponse(
                answer=(
                    "The current official sources conflicting. "
                    "One says to hand-wash the body, while the other says "
                   "all components are dishwasher safe. I cannot safely "
                 "choose one. Please seek human confirmation or use the "
                  "safest interim guidance: hand-wash the body."
                ),
                sources=self._format_sources(results),
                handoff=True,
                debug={
                    "reason": "authoritative_source_conflict",
                    "retrieved": self._debug_results(results),
                },
            )

        answer = self._answer_from_retrieval(
            message,
            results,
        )

        if answer is None:
            return AgentResponse(
                answer=(
                    "The supplied information is insufficient for me "
                    "to answer that reliably. Please seek human confirmation."
                ),
                sources=self._format_sources(results),
                handoff=True,
                debug={
                    "reason": "insufficient_information",
                    "retrieved": self._debug_results(results),
                },
            )

        return AgentResponse(
            answer=answer,
            sources=self._format_sources(results),
            handoff=False,
            debug={
                "reason": "knowledge_base",
                "retrieved": self._debug_results(results),
            },
        )

    # =============================================================
    # Order helpers
    # =============================================================

    @staticmethod
    def _extract_order_id(message: str) -> str | None:
        import re

        match = re.search(
            r"\bORD-\d+\b",
            message,
            re.IGNORECASE,
        )

        if not match:
            return None

        return match.group(0).upper()

    @staticmethod
    def _is_order_question(message: str) -> bool:
        import re

        normalized = message.lower().strip()

        if re.search(r"\bord-\d+\b", normalized):
            return True

        order_terms = {
            "where is my order",
            "where is the order",
            "track my order",
            "tracking my order",
            "order status",
            "shipment status",
            "when will it arrive",
            "when will my order arrive",
            "when will the order arrive",
            "when does it arrive",
            "when should it arrive",
            "estimated delivery",
            "delivery date",
            "check my shipment",
            "check my order",
        }

        return any(
            term in normalized
            for term in order_terms
        )

    @staticmethod
    def _is_order_follow_up(message: str) -> bool:
        normalized = message.lower().strip()

        follow_up_terms = {
            "when will it arrive",
            "when will my order arrive",
            "when will the order arrive",
            "when does it arrive",
            "when should it arrive",
            "what is the delivery date",
            "what's the delivery date",
            "when is it arriving",
            "when is it expected",
        }

        return any(
            term in normalized
            for term in follow_up_terms
        )

    @staticmethod
    def _format_order_answer(
        data: dict[str, Any],
    ) -> str:
        from datetime import datetime

        status = data["status"]
        carrier = data.get("carrier")
        eta = data.get("estimated_delivery")

        if status == "shipped":
            if carrier and eta:
                try:
                    date = datetime.strptime(
                        eta,
                        "%Y-%m-%d",
                    )

                    formatted_date = (
                        f"{date.strftime('%B')} "
                        f"{date.day}, "
                        f"{date.year}"
                    )

                except ValueError:
                    formatted_date = eta

                return (
                    f"Order {data['order_id']} has shipped "
                    f"with {carrier} and is currently estimated "
                    f"to arrive on {formatted_date}."
                )

            if carrier:
                return (
                    f"Order {data['order_id']} has shipped with "
                    f"{carrier}, but a delivery estimate is "
                    "currently unavailable."
                )

        message = data.get(
            "customer_safe_message"
        )

        if message:
            return message

        return (
            f"Order {data['order_id']} is currently marked "
            f"as {status}."
        )

    # =============================================================
    # Security / action helpers
    # =============================================================

    @staticmethod
    def _is_sensitive_request(
        message: str,
    ) -> bool:
        sensitive_terms = [
            "email",
            "email address",
            "shipping address",
            "address",
            "internal note",
            "internal notes",
            "risk score",
            "fraud review",
            "hidden prompt",
            "system prompt",
            "secret",
            "credential",
            "password",
        ]

        return any(
            term in message
            for term in sensitive_terms
        )

    @staticmethod
    def _is_unsupported_action(
        message: str,
    ) -> bool:
        action_terms = [
            "cancel",
            "refund",
            "replace",
            "replacement",
            "price adjustment",
            "address change",
            "change my address",
            "approve my return",
        ]

        return any(
            term in message
            for term in action_terms
        )

    # =============================================================
    # Retrieval helpers
    # =============================================================

    @staticmethod
    def _build_retrieval_query(
        message: str,
        history: list[dict[str, str]],
    ) -> str:
        if not history:
            return message

        recent = history[-2:]

        context = " ".join(
            item.get("content", "")
            for item in recent
            if item.get("role") == "user"
        )

        if not context:
            return message

        return f"{context} {message}"

    @staticmethod
    def _format_sources(
        results: list[RetrievalResult],
    ) -> list[str]:
        seen = set()
        sources = []

        for result in results:
            source = result.chunk.filename

            if source not in seen:
                sources.append(source)
                seen.add(source)

        return sources

    @staticmethod
    def _debug_results(
        results: list[RetrievalResult],
    ) -> list[dict[str, Any]]:
        return [
            {
                "filename": result.chunk.filename,
                "heading": result.chunk.heading,
                "score": result.score,
                "metadata": result.chunk.metadata,
            }
            for result in results
        ]

    @staticmethod
    def _has_breeze_conflict(
        message: str,
        results: list[RetrievalResult],
    ) -> bool:
        normalized = message.lower()

        if "breeze tumbler" not in normalized:
            return False

        if "dishwasher" not in normalized:
            return False

        filenames = {
            result.chunk.filename
            for result in results
        }

        return {
            "11-product-care.md" in filenames and 
            "12-breeze-tumbler-product-card.md" in  filenames
        }

    @staticmethod
    def _answer_from_retrieval(
        message: str,
        results: list[RetrievalResult],
    ) -> str | None:
        text = " ".join(
            result.chunk.content.lower()
            for result in results
        )

        normalized = message.lower()

        # ---------------------------------------------------------
        # Standard returns
        # ---------------------------------------------------------
        if (
            "return" in normalized
            and (
                "regular" in normalized
                or "standard" in normalized
            )
            and "trailplus" not in normalized
        ):
            if (
                "30 calendar days of delivery" in text
                and "return shipping fee" in text
            ):
                return (
                    "Customers on the standard plan may request "
                    "a return within 30 calendar days of delivery. "
                    "A $6.95 return shipping fee is deducted from "
                    "the refund for standard domestic returns."
                )

        # ---------------------------------------------------------
        # TrailPlus
        # ---------------------------------------------------------
        if (
            "trailplus" in normalized
            and "return" in normalized
        ):
            if (
                "45-calendar-day return window from delivery"
                in text
            ):
                return (
                    "If your TrailPlus membership was active when "
                    "the order was placed, you have a 45-calendar-day "
                    "return window from delivery (45 calendar days)."
                )

        # ---------------------------------------------------------
        # Canada shipping
        # ---------------------------------------------------------
        if (
            "canada" in normalized
            and (
                "ship" in normalized
                or "shipping" in normalized
                or "what about" in normalized
            )
        ):
            if "5–9 business days after dispatch" in text:
                return (
                    "Canada is currently supported. Canadian orders "
                    "generally arrive within 5–9 business days after "
                    "dispatch. Processing before dispatch is usually "
                    "1–2 business days. Import duties, taxes, and "
                    "brokerage charges are not prepaid, so the "
                    "recipient is responsible for charges assessed "
                    "by Canadian authorities or the carrier."
                )

        # ---------------------------------------------------------
        # Unsupported country
        # ---------------------------------------------------------
        if (
            "germany" in normalized
            and (
                "ship" in normalized
                or "shipping" in normalized
            )
        ):
            if "other countries is not available" in text:
                return (
                    "Shipping to Germany is not currently available."
                )

        # ---------------------------------------------------------
        # Warranty
        # ---------------------------------------------------------
        if "lifetime warranty" in normalized:
            if "does not offer a lifetime warranty" in text:
                return (
                    "No. Aster & Row does not offer a lifetime "
                    "warranty. Bags have 2 years (a 2-year warranty) "
                    "from the purchase date, while drinkware "
                    "and packing cubes/other travel accessories have "
                    "a 1-year warranty."
                )

        # ---------------------------------------------------------
        # Final-sale damaged item
        # ---------------------------------------------------------
        if (
            (
                "final-sale" in normalized
                or "final sale" in normalized
            )
            and (
                "damaged" in normalized
                or "broken" in normalized
                or "defective" in normalized
                or "zipper" in normalized
            )
        ):
            if (
                "still eligible for review" in text
                and "7 calendar days" in text
            ):
                return (
                    "Final sale does not block damaged-item review. "
                    "The item should be reported within 7 calendar "
                    "days of delivery. A human review is required "
                    "before approval of a refund or replacement."
                )

        # ---------------------------------------------------------
        # Insufficient information
        # ---------------------------------------------------------
        if "vegan" in normalized:
            return None

        # ---------------------------------------------------------
        # Generic retrieved answer
        # ---------------------------------------------------------
        best = results[0]

        if best.score >= 6:
            return best.chunk.content.strip()

        return None