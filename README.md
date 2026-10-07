# DX Orbit

**API Developer Experience Observatory.** DX Orbit analyzes an OpenAPI 3.x document and turns integration quality into an inspectable scorecard: API clarity, error recovery, authentication, SDK readiness, webhook/eventing quality, and AI-agent readiness.

## What makes this portfolio project different
DX Orbit is not a syntax validator. It asks whether a real developer can understand the contract, make a first request, recover from failure, automate against stable operation identifiers, and safely consume event-driven behavior. Every score is deterministic and every penalty is traceable to a human-readable rule.

## Included in v1
- OpenAPI JSON/YAML upload and direct JSON analysis
- Weighted DX score + integration-friction classification
- Separate category scores for clarity, recovery, security, SDK readiness, eventing, and agent readiness
- High-impact blocker count and prioritized findings
- Checks for auth, servers, descriptions, request examples, 4xx/429 contracts, idempotency, operation IDs, parameter semantics, webhooks, correlation IDs, and more
- Generated cURL, Python, and JavaScript starter examples
- Before/after report comparison API
- Markdown report export
- Premium single-page dashboard
- Health endpoint, FastAPI docs, Dockerfile, tests, and read-only GitHub Actions CI

## Quick start
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://localhost:8000` and API docs at `http://localhost:8000/docs`.

## Verify
```bash
pytest -q
python -m compileall -q app
```

## Architecture
```text
Browser dashboard
      │
      ├── POST /api/analyze
      ├── POST /api/analyze-file
      ├── POST /api/compare
      └── POST /api/report/markdown
      │
      ▼
Deterministic rule engine
      ├── operation discovery
      ├── auth + security checks
      ├── error/recovery checks
      ├── SDK/agent readiness checks
      ├── eventing/webhook checks
      ├── category scoring
      └── example generation
```

## Evidence boundary
DX Orbit does **not** claim to prove production quality, security certification, or real developer behavior. It evaluates the evidence visible in an OpenAPI contract using explicit rules. A production version would add configurable rule packs, persistent projects, team baselines, CI annotations, GitHub PR comments, custom governance policies, and measured onboarding telemetry.

## Interview story
> “I wanted to turn API quality from a vague opinion into an inspectable developer-experience review. DX Orbit parses the contract, measures six dimensions, explains every penalty, generates starter examples, and supports before/after comparison so an API team can prove that the developer experience improved.”

## Continuous integration
The Verify workflow runs the test suite and Python compilation on Python 3.12 for pushes to main and pull requests. It has read-only repository permissions. Run the tests locally with `python -m pytest`.

