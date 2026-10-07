from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable
from urllib.parse import urlparse

SEVERITY_PENALTY = {"critical": 18, "high": 11, "medium": 6, "low": 3}
CATEGORY_WEIGHTS = {
    "clarity": 0.24,
    "recovery": 0.22,
    "security": 0.18,
    "sdk_readiness": 0.16,
    "eventing": 0.10,
    "agent_readiness": 0.10,
}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    category: str
    location: str
    message: str
    why_it_matters: str
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _operations(spec: dict[str, Any]) -> Iterable[tuple[str, str, dict[str, Any]]]:
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "patch", "delete", "options", "head"):
            op = path_item.get(method)
            if isinstance(op, dict):
                yield str(path), method.upper(), op


def _add(findings: list[Finding], rule: str, severity: str, category: str, location: str,
         message: str, why: str, next_action: str) -> None:
    findings.append(Finding(rule, severity, category, location, message, why, next_action))


def _has_example(media: Any) -> bool:
    if not isinstance(media, dict):
        return False
    return "example" in media or bool(media.get("examples"))


def _schema_has_example(schema: Any) -> bool:
    return isinstance(schema, dict) and any(k in schema for k in ("example", "examples", "default", "enum"))


def _all_parameters(op: dict[str, Any], path_item: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for source in ((path_item or {}).get("parameters") or [], op.get("parameters") or []):
        if isinstance(source, list):
            items.extend(x for x in source if isinstance(x, dict))
    return items


def _endpoint_sample(path: str, method: str, op: dict[str, Any], spec: dict[str, Any]) -> dict[str, str]:
    server_url = "https://api.example.com"
    servers = op.get("servers") or spec.get("servers") or []
    if servers and isinstance(servers[0], dict) and servers[0].get("url"):
        server_url = str(servers[0]["url"]).rstrip("/")
    concrete_path = path
    for p in op.get("parameters") or []:
        if isinstance(p, dict) and p.get("in") == "path" and p.get("name"):
            value = p.get("example") or (p.get("schema") or {}).get("example") or f"demo-{p['name']}"
            concrete_path = concrete_path.replace("{" + str(p["name"]) + "}", str(value))
    url = f"{server_url}{concrete_path}"
    headers = {"Accept": "application/json"}
    schemes = (spec.get("components") or {}).get("securitySchemes") or {}
    if schemes:
        headers["Authorization"] = "Bearer $API_TOKEN"
    body: dict[str, Any] | None = None
    request_body = op.get("requestBody") or {}
    content = request_body.get("content") or {}
    json_media = content.get("application/json") if isinstance(content, dict) else None
    if isinstance(json_media, dict):
        body = json_media.get("example")
        if body is None:
            schema = json_media.get("schema") or {}
            props = schema.get("properties") or {}
            if isinstance(props, dict):
                body = {}
                for key, definition in list(props.items())[:5]:
                    if isinstance(definition, dict):
                        body[key] = definition.get("example") or definition.get("default") or _placeholder_for_type(definition.get("type"))
    header_args = " ".join(f"-H '{k}: {v}'" for k, v in headers.items())
    curl = f"curl -X {method} '{url}' {header_args}"
    if body is not None:
        import json
        curl += " -H 'Content-Type: application/json' -d '" + json.dumps(body) + "'"
    py_headers = repr(headers)
    js_headers = repr(headers).replace("'", '"')
    python = f"import requests\nresponse = requests.{method.lower()}('{url}', headers={py_headers}"
    javascript = f"const response = await fetch('{url}', {{\n  method: '{method}',\n  headers: {js_headers}"
    if body is not None:
        import json
        body_json = json.dumps(body, indent=2)
        python += f", json={repr(body)}"
        javascript += f",\n  body: JSON.stringify({body_json})"
    python += ")\nresponse.raise_for_status()\nprint(response.json())"
    javascript += "\n});\nif (!response.ok) throw new Error(await response.text());\nconsole.log(await response.json());"
    return {"curl": curl, "python": python, "javascript": javascript}


def _placeholder_for_type(t: Any) -> Any:
    return {"integer": 1, "number": 1.0, "boolean": True, "array": [], "object": {}}.get(str(t), "example")


def analyze_openapi(spec: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    info = spec.get("info") or {}
    title = str(info.get("title") or "Untitled API")
    version = str(info.get("version") or "unknown")

    if not spec.get("openapi"):
        _add(findings, "missing-openapi-version", "critical", "clarity", "openapi",
             "OpenAPI version is missing.", "Tooling cannot reliably parse the document without a declared specification version.",
             "Add openapi: 3.0.x or 3.1.x at the document root.")
    if not info.get("title") or not info.get("version"):
        _add(findings, "incomplete-api-metadata", "medium", "clarity", "info",
             "API title or version is missing.", "Developers need stable product and version context before integrating.",
             "Add both info.title and info.version.")
    if len(str(info.get("description") or "").split()) < 8:
        _add(findings, "thin-api-description", "low", "clarity", "info.description",
             "The API-level description is very short or missing.", "A concise purpose statement helps developers know whether they are in the right API.",
             "Explain the API purpose, primary resource, and integration boundary in 2–4 sentences.")

    servers = spec.get("servers") or []
    if not servers:
        _add(findings, "missing-server-url", "medium", "clarity", "servers",
             "No server URL is documented.", "Copy-paste examples are incomplete without a base URL.",
             "Add at least one server entry, ideally a sandbox or local development URL.")
    else:
        for i, server in enumerate(servers):
            url = str(server.get("url") or "") if isinstance(server, dict) else ""
            if url and not urlparse(url.replace("{", "").replace("}", "")).scheme:
                _add(findings, "ambiguous-server-url", "low", "clarity", f"servers[{i}]",
                     "Server URL is relative or ambiguous.", "Developers benefit from an explicit protocol and host when onboarding.",
                     "Use an absolute HTTPS URL or clearly document server variables.")

    components = spec.get("components") or {}
    schemes = components.get("securitySchemes") or {}
    if not schemes and not spec.get("security"):
        _add(findings, "missing-auth-documentation", "high", "security", "components.securitySchemes",
             "No authentication scheme is documented.", "Authentication ambiguity is one of the fastest ways to block a first API call.",
             "Document authentication and include one working authenticated request example.")

    operations = list(_operations(spec))
    if not operations:
        _add(findings, "no-operations", "critical", "clarity", "paths",
             "No API operations were found.", "A developer cannot evaluate or integrate an API with no documented endpoints.",
             "Add at least one operation under paths.")

    operation_ids: list[str] = []
    example_bundle: dict[str, str] | None = None
    for path, method, op in operations:
        location = f"{method} {path}"
        operation_id = str(op.get("operationId") or "")
        if operation_id:
            operation_ids.append(operation_id)
        else:
            _add(findings, "missing-operation-id", "medium", "sdk_readiness", location,
                 "operationId is missing.", "Stable operation identifiers improve SDK generation and agent/tool discovery.",
                 "Add a unique, stable operationId.")
        if len(str(op.get("summary") or "").strip()) < 5:
            _add(findings, "missing-operation-summary", "low", "clarity", location,
                 "Operation summary is missing or too vague.", "Scanning a reference is faster when every operation has an action-oriented summary.",
                 "Add a concise verb-led summary such as 'Create an order'.")
        if len(str(op.get("description") or "").split()) < 6:
            _add(findings, "thin-operation-description", "low", "clarity", location,
                 "Operation description lacks behavioral context.", "Developers need preconditions, side effects, and important constraints beyond a method name.",
                 "Document intent, important constraints, and side effects.")

        params = _all_parameters(op)
        for param in params:
            name = str(param.get("name") or "parameter")
            if len(str(param.get("description") or "").split()) < 4:
                _add(findings, "weak-parameter-description", "low", "agent_readiness", f"{location} → {name}",
                     f"Parameter '{name}' has little or no description.", "Humans and agents both make fewer argument errors when parameter semantics are explicit.",
                     "Describe accepted values, units/format, and how the parameter changes behavior.")
            schema = param.get("schema") or {}
            if param.get("required") and not (param.get("example") or _schema_has_example(schema)):
                _add(findings, "required-parameter-no-example", "low", "sdk_readiness", f"{location} → {name}",
                     f"Required parameter '{name}' has no example.", "Examples shorten time-to-first-success and improve generated snippets.",
                     "Add an example or default that is safe to copy.")

        request_body = op.get("requestBody") or {}
        if method in {"POST", "PUT", "PATCH"} and not request_body:
            _add(findings, "write-operation-no-request-body", "medium", "clarity", location,
                 "Write operation has no documented request body.", "Developers cannot confidently construct a mutation request without a payload contract.",
                 "Document requestBody with a schema and at least one example.")
        if isinstance(request_body, dict):
            content = request_body.get("content") or {}
            json_media = content.get("application/json") if isinstance(content, dict) else None
            if json_media and not (_has_example(json_media) or _schema_has_example(json_media.get("schema"))):
                _add(findings, "request-body-no-example", "medium", "sdk_readiness", location,
                     "Request body has no concrete example.", "A realistic payload is one of the highest-value onboarding artifacts.",
                     "Add an example request that passes validation.")

        responses = op.get("responses") or {}
        if not responses:
            _add(findings, "missing-responses", "high", "recovery", location,
                 "No responses are documented.", "An endpoint without response contracts is difficult to integrate and impossible to recover from predictably.",
                 "Document at least one success and one recoverable failure response.")
            continue
        success_codes = [str(c) for c in responses if str(c).startswith("2")]
        if not success_codes:
            _add(findings, "missing-success-response", "high", "clarity", location,
                 "No 2xx success response is documented.", "Developers need a concrete success contract to know what to parse and persist.",
                 "Document the expected 2xx response and example payload.")
        error_codes = [str(c) for c in responses if str(c).startswith("4")]
        if not error_codes:
            _add(findings, "missing-error-response", "high", "recovery", location,
                 "No 4xx response is documented.", "Developers need a recovery contract, not only a happy path.",
                 "Document realistic 400/401/403/404/409 responses as applicable.")
        if "429" not in {str(c) for c in responses}:
            _add(findings, "missing-rate-limit-response", "medium", "recovery", location,
                 "429 Too Many Requests is not documented.", "Clients cannot implement safe retry behavior without rate-limit semantics.",
                 "Document 429 behavior, rate-limit headers, and retry guidance.")
        for code, response in responses.items():
            if not isinstance(response, dict):
                continue
            if not str(response.get("description") or "").strip():
                _add(findings, "response-description-missing", "low", "clarity", f"{location} → {code}",
                     "Response description is missing.", "Status codes alone rarely explain the actual domain meaning.",
                     "Add a short description that explains the outcome.")
            if str(code).startswith(("4", "5")):
                content = response.get("content") or {}
                if content and not any(_has_example(media) for media in content.values()):
                    _add(findings, "missing-error-example", "medium", "recovery", f"{location} → {code}",
                         "The error response has no concrete example.", "Examples make error handling faster and reduce support requests.",
                         "Add an error payload with stable code, message, and next-action fields.")

        if method == "POST":
            params_by_name = {str(p.get("name") or "").lower() for p in params}
            headers = {x for x in params_by_name if x}
            if not any("idempot" in h for h in headers) and "idempot" not in str(op.get("description") or "").lower():
                _add(findings, "idempotency-undocumented", "medium", "recovery", location,
                     "POST idempotency behavior is not documented.", "Retries can create duplicate side effects unless clients know how duplicate requests are handled.",
                     "Document idempotency semantics and an idempotency-key header if supported.")

        if example_bundle is None:
            example_bundle = _endpoint_sample(path, method, op, spec)

    if len(operation_ids) != len(set(operation_ids)):
        _add(findings, "duplicate-operation-id", "high", "sdk_readiness", "paths",
             "Duplicate operationId values were found.", "SDK generators and agent tool registries require stable unique operation identifiers.",
             "Rename operationId values so each operation is unique.")

    if not spec.get("tags"):
        _add(findings, "missing-tags", "low", "clarity", "tags",
             "No top-level API tags are defined.", "Large references become easier to navigate when operations are grouped by domain.",
             "Define tags and assign them consistently to operations.")

    webhook_count = len(spec.get("webhooks") or {})
    if webhook_count == 0:
        _add(findings, "webhooks-not-described", "low", "eventing", "webhooks",
             "No webhook contract is described.", "Event-driven integrations benefit from explicit delivery and verification contracts.",
             "If the product emits events, document event payloads, verification, retries, and ordering.")
    else:
        raw = str(spec.get("webhooks") or {}).lower()
        if not any(term in raw for term in ("signature", "hmac", "verify")):
            _add(findings, "webhook-verification-unclear", "high", "eventing", "webhooks",
                 "Webhook verification guidance is not discoverable.", "Unsigned or ambiguously verified webhooks create security and developer-support risk.",
                 "Document signing algorithm, timestamp/replay window, header names, and verification example.")
        if not any(term in raw for term in ("retry", "duplicate", "idempot")):
            _add(findings, "webhook-delivery-semantics-missing", "medium", "eventing", "webhooks",
                 "Webhook retry/duplicate behavior is not documented.", "Receivers need to know whether events can retry, duplicate, or arrive out of order.",
                 "Document retry schedule, duplicate expectations, ordering, and idempotency guidance.")

    raw_spec = str(spec).lower()
    if not any(term in raw_spec for term in ("request id", "request_id", "correlation", "trace")):
        _add(findings, "correlation-id-undocumented", "low", "recovery", "responses",
             "No correlation/request ID convention is discoverable.", "Support and debugging are faster when client and server can discuss the same request identifier.",
             "Document a request/correlation ID header or field and show it in error examples.")

    category_penalties = {k: 0 for k in CATEGORY_WEIGHTS}
    for f in findings:
        category_penalties[f.category] = category_penalties.get(f.category, 0) + SEVERITY_PENALTY[f.severity]
    category_scores = {k: max(0, 100 - min(100, p)) for k, p in category_penalties.items()}
    base_score = round(sum(category_scores[k] * w for k, w in CATEGORY_WEIGHTS.items()))
    critical = sum(1 for f in findings if f.severity in {"critical", "high"})
    dx_score = max(0, base_score - critical * 4)
    friction = "low" if dx_score >= 85 else "medium" if dx_score >= 65 else "high"
    agent_score = round((category_scores["agent_readiness"] * .55) + (category_scores["sdk_readiness"] * .3) + (category_scores["recovery"] * .15))
    sorted_findings = sorted(findings, key=lambda f: (-(SEVERITY_PENALTY[f.severity]), f.category, f.location))

    return {
        "api": {"title": title, "version": version},
        "dx_score": dx_score,
        "agent_readiness_score": agent_score,
        "integration_friction": friction,
        "critical_blockers": critical,
        "operation_count": len(operations),
        "webhook_count": webhook_count,
        "category_scores": category_scores,
        "findings": [f.to_dict() for f in sorted_findings],
        "examples": example_bundle or {},
        "summary": _executive_summary(dx_score, critical, len(operations), agent_score),
    }


def _executive_summary(score: int, blockers: int, operations: int, agent_score: int) -> str:
    if score >= 85:
        posture = "strong developer experience with a small number of targeted improvements"
    elif score >= 65:
        posture = "workable developer experience with meaningful onboarding friction"
    else:
        posture = "high-friction developer experience that is likely to create support and integration delays"
    return (f"This API documents {operations} operation(s) and currently presents {posture}. "
            f"DX score is {score}/100 with {blockers} high-impact blocker(s); agent readiness is {agent_score}/100.")


def compare_reports(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    b = analyze_openapi(before)
    a = analyze_openapi(after)
    before_rules = {f["rule"] + "|" + f["location"] for f in b["findings"]}
    after_rules = {f["rule"] + "|" + f["location"] for f in a["findings"]}
    return {
        "before_score": b["dx_score"],
        "after_score": a["dx_score"],
        "delta": a["dx_score"] - b["dx_score"],
        "resolved_findings": sorted(before_rules - after_rules),
        "new_findings": sorted(after_rules - before_rules),
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        f"# DX Orbit Report — {result['api']['title']}", "",
        f"- **DX score:** {result['dx_score']}/100",
        f"- **Agent readiness:** {result['agent_readiness_score']}/100",
        f"- **Integration friction:** {result['integration_friction']}",
        f"- **High-impact blockers:** {result['critical_blockers']}",
        "", result["summary"], "", "## Category scores", "",
    ]
    for name, score in result["category_scores"].items():
        lines.append(f"- {name.replace('_', ' ').title()}: {score}/100")
    lines += ["", "## Findings", ""]
    for f in result["findings"]:
        lines += [f"### [{f['severity'].upper()}] {f['message']}", f"`{f['location']}` · `{f['rule']}` · {f['category']}", "", f["why_it_matters"], "", f"**Next action:** {f['next_action']}", ""]
    return "\n".join(lines)
