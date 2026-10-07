from app.core import analyze_openapi, compare_reports, markdown_report


def weak_spec():
    return {"openapi":"3.1.0","info":{"title":"Orders","version":"1"},"paths":{"/orders":{"post":{"responses":{"200":{"description":"ok"}}}}}}


def strong_spec():
    return {
        "openapi":"3.1.0","info":{"title":"Orders","version":"1","description":"A practical API for creating and reading customer orders with documented recovery behavior."},
        "servers":[{"url":"https://api.example.com"}],"tags":[{"name":"Orders"}],
        "components":{"securitySchemes":{"bearer":{"type":"http","scheme":"bearer"}}},"security":[{"bearer":[]}],
        "paths":{"/orders":{"post":{"operationId":"createOrder","summary":"Create an order","description":"Creates one order using an idempotency key for safe retries.",
            "parameters":[{"name":"Idempotency-Key","in":"header","required":True,"description":"Unique retry key for this order request.","schema":{"type":"string","example":"idem_1"}}],
            "requestBody":{"content":{"application/json":{"example":{"product_id":"sku_1"}}}},
            "responses":{"201":{"description":"Created"},"400":{"description":"Bad request","content":{"application/json":{"example":{"code":"bad","request_id":"req_1"}}}},"429":{"description":"Limited","content":{"application/json":{"example":{"code":"limited"}}}}}}}},
        "webhooks":{"orderUpdated":{"post":{"description":"Verify HMAC signature and safely process retries and duplicate events.","responses":{"200":{"description":"ok"},"400":{"description":"invalid","content":{"application/json":{"example":{"code":"invalid"}}}},"429":{"description":"busy"}}}}}
    }


def test_incomplete_api_scores_lower():
    result=analyze_openapi(weak_spec())
    assert result["dx_score"] < 80
    assert result["critical_blockers"] >= 1
    assert any(f["rule"]=="missing-auth-documentation" for f in result["findings"])


def test_strong_api_scores_higher_and_generates_examples():
    weak=analyze_openapi(weak_spec()); strong=analyze_openapi(strong_spec())
    assert strong["dx_score"] > weak["dx_score"]
    assert "curl" in strong["examples"] and "python" in strong["examples"]
    assert strong["agent_readiness_score"] >= 70


def test_compare_reports_tracks_delta():
    result=compare_reports(weak_spec(),strong_spec())
    assert result["delta"] > 0
    assert result["resolved_findings"]


def test_markdown_report_is_reviewable():
    text=markdown_report(analyze_openapi(weak_spec()))
    assert "DX Orbit Report" in text and "Next action" in text and "Category scores" in text
