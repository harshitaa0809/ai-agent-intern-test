import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OrderLookupResult:
    found: bool
    order_id: str
    data: dict[str, Any]
    handoff: bool = False
    error: str | None = None


class OrderLookupTool:
    """
    Customer-safe lookup over the supplied mock orders dataset.

    The raw orders file never leaves this class. Only sanitized,
    minimum-required fields are returned.
    """

    CUSTOMER_SAFE_FIELDS = {
        "order_id",
        "membership_tier",
        "items",
        "placed_at",
        "status",
        "status_updated_at",
        "shipped_at",
        "delivered_at",
        "carrier",
        "tracking_number",
        "estimated_delivery",
        "customer_safe_message",
    }

    def __init__(self, orders_path: str | Path):
        self.orders_path = Path(orders_path)

        with self.orders_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        self.snapshot_at = payload.get("snapshot_at")
        self.orders = payload.get("orders", [])

        self._orders_by_id = {
            order["order_id"]: order
            for order in self.orders
            if isinstance(order, dict) and "order_id" in order
        }

    def lookup(self, order_id: str) -> OrderLookupResult:
        normalized_id = self._normalize_order_id(order_id)

        if not normalized_id:
            return OrderLookupResult(
                found=False,
                order_id="",
                data={},
                error="Order ID is required.",
            )

        order = self._orders_by_id.get(normalized_id)

        if order is None:
            return OrderLookupResult(
                found=False,
                order_id=normalized_id,
                data={},
                handoff=True,
                error="Order was not found.",
            )

        safe_data = self._sanitize_order(order)

        return OrderLookupResult(
            found=True,
            order_id=normalized_id,
            data=safe_data,
            handoff=order.get("status") == "exception",
        )

    @staticmethod
    def _normalize_order_id(order_id: str) -> str:
        """
        Normalize harmless formatting differences only.

        Examples:
        ' ord-1007 ' -> 'ORD-1007'
        'ORD-1007.' -> 'ORD-1007'
        'ord-1007' -> 'ORD-1007'
        """

        if not isinstance(order_id, str):
            return ""

        normalized = order_id.strip().upper()

        # Remove ordinary surrounding punctuation only.
        normalized = re.sub(r"^[^\w-]+|[^\w-]+$", "", normalized)

        # Do not guess substantially different IDs.
        if not re.fullmatch(r"ORD-\d+", normalized):
            return ""

        return normalized

    def _sanitize_order(self, order: dict[str, Any]) -> dict[str, Any]:
        """
        Return only customer-safe fields and apply status precedence.
        """

        status = order.get("status")

        safe: dict[str, Any] = {
            "order_id": order.get("order_id"),
            "membership_tier": order.get("membership_tier"),
            "items": [
                {
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "final_sale": item.get("final_sale"),
                }
                for item in order.get("items", [])
            ],
            "placed_at": order.get("placed_at"),
            "status": status,
            "status_updated_at": order.get("status_updated_at"),
            "shipped_at": order.get("shipped_at"),
            "delivered_at": order.get("delivered_at"),
            "customer_safe_message": order.get("customer_safe_message"),
        }

        # Status is authoritative.
        if status in {"cancelled", "returned"}:
            safe["carrier"] = None
            safe["tracking_number"] = None
            safe["estimated_delivery"] = None

        else:
            safe["carrier"] = order.get("carrier")
            safe["tracking_number"] = order.get("tracking_number")
            safe["estimated_delivery"] = order.get("estimated_delivery")

        return {
            key: value
            for key, value in safe.items()
            if key in self.CUSTOMER_SAFE_FIELDS
        }