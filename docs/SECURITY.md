# Security Notes

The demo accepts JSON/YAML files up to 2 MB and analyzes them locally. It does not fetch external `$ref` URLs, execute user content, call arbitrary endpoints, or persist uploaded contracts. A production service should additionally add authentication, tenant isolation, request rate limits, structured logging with redaction, file-content scanning, dependency monitoring, and strict resource budgets.
