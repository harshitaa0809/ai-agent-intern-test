from src.order_tool import OrderLookupTool


def build_tool():
    return OrderLookupTool("data/orders.json")


def test_valid_order_lookup_returns_customer_safe_data():
    tool = build_tool()

    result = tool.lookup("ORD-1007")

    assert result.found is True
    assert result.order_id == "ORD-1007"
    assert result.data["status"] == "shipped"
    assert result.data["carrier"] == "UPS"
    assert result.data["estimated_delivery"] == "2026-08-22"


def test_order_id_normalization():
    tool = build_tool()

    result = tool.lookup("  ord-1007. ")

    assert result.found is True
    assert result.order_id == "ORD-1007"


def test_unknown_order_is_not_invented():
    tool = build_tool()

    result = tool.lookup("ORD-9999")

    assert result.found is False
    assert result.handoff is True
    assert result.data == {}


def test_cancelled_order_does_not_expose_stale_eta():
    tool = build_tool()

    result = tool.lookup("ORD-1004")

    assert result.found is True
    assert result.data["status"] == "cancelled"
    assert result.data["estimated_delivery"] is None
    assert result.data["carrier"] is None
    assert result.data["tracking_number"] is None


def test_shipped_order_without_eta_does_not_invent_one():
    tool = build_tool()

    result = tool.lookup("ORD-1011")

    assert result.found is True
    assert result.data["status"] == "shipped"
    assert result.data["carrier"] == "Canada Post"
    assert result.data["estimated_delivery"] is None


def test_exception_order_requires_handoff():
    tool = build_tool()

    result = tool.lookup("ORD-1010")

    assert result.found is True
    assert result.data["status"] == "exception"
    assert result.handoff is True


def test_sensitive_customer_data_is_never_returned():
    tool = build_tool()

    result = tool.lookup("ORD-1007")

    forbidden = {
        "name",
        "email",
        "shipping_address",
        "internal",
        "risk_score",
        "warehouse_note",
        "support_tags",
    }

    assert forbidden.isdisjoint(result.data.keys())