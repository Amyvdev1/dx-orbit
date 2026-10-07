# Contributing

Thanks for reviewing this portfolio project. The repository is intentionally small and inspectable.

## Development workflow
1. Create a branch.
2. Keep one change focused on one product or engineering concern.
3. Add or update tests for behavior changes.
4. Run the verification commands in `README.md`.
5. Open a pull request that explains the user impact, implementation choice, and tradeoffs.

## Engineering standards
- Prefer explicit, deterministic behavior over hidden magic.
- Keep demo claims inside the evidence boundary documented in the README.
- Never commit production secrets, personal data, or real customer data.
- Keep CI read-only: verification workflows must not write back to the repository.
