# DX Orbit Architecture

## Product boundary
DX Orbit is deliberately local-first and deterministic. The browser submits an OpenAPI object; the FastAPI layer validates transport concerns; `app/core.py` performs analysis without network access or hidden model calls.

## Core design decisions
1. **Explainable scoring over opaque scoring.** Every score reduction maps to a rule, severity, category, location, reason, and next action.
2. **Category scores before one headline score.** Teams need to know *where* the friction lives, not only that a score is 72.
3. **Agent readiness is derived from interface quality.** Clear parameters, stable operation IDs, examples, and recoverable errors benefit humans and tool-using agents.
4. **Example generation is intentionally conservative.** It uses only visible contract evidence and placeholder values.
5. **No outbound requests.** An uploaded spec is analyzed in-process and never fetched from arbitrary URLs.

## Production evolution
- persisted projects and historical baselines
- configurable organization rule packs
- OpenAPI `$ref` resolution across documents
- CI annotations and GitHub checks
- generated SDK smoke tests
- measured time-to-first-success telemetry
- role-based access and audit trail
