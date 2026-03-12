from spark_app.parsing import extract_action_type, extract_endpoint


def test_extract_action_type_basic():
    assert extract_action_type(None) is None
    assert extract_action_type("") is None
    assert extract_action_type("no bracket") is None


def test_extract_action_type_tokens():
    assert extract_action_type("[INFO] GET /api/v1/users") == "GET"
    assert extract_action_type("[WARN] - POST /api/v1/orders") == "POST"


def test_extract_endpoint():
    assert extract_endpoint(None) is None
    assert extract_endpoint("[INFO] GET /api/v1/users 200") == "/api/v1/users"
    assert extract_endpoint("[INFO] POST /orders?id=1") == "/orders?id=1"
    assert extract_endpoint("[INFO] something else") is None

