# DX Orbit — Code Tour

## Product surface
`app/static/index.html`, `styles.css`, and `app.js` provide the browser demo. The frontend intentionally stays dependency-light so reviewers can inspect the behavior quickly.

## HTTP boundary
`app/main.py` exposes the FastAPI routes, validates request models, and delegates product behavior to the core module rather than hiding domain rules inside route handlers.

## Domain logic
`app/core.py` contains the deterministic scoring, evaluation, simulation, or analytics logic. This is the best place to start a technical review.

## Verification
`tests/` covers the core behavior and API contract. `fixtures/` contains reproducible inputs for demos and regression tests. GitHub Actions runs tests and compile checks with read-only repository permissions.

## Design principle
**Developer Experience Observatory for OpenAPI contracts.** The project separates product UI, API boundary, and deterministic logic so the reasoning remains easy to inspect and defend in an interview.
