# Security and Privacy

## Threat model

| Threat | Control | Residual consideration |
|---|---|---|
| Unauthorized use | API-key authentication with constant-time comparison | Use a managed identity provider and scoped tokens in production |
| Credential leakage | Environment-only secrets; `.env` is ignored | Rotate keys and store them in a secret manager |
| Resource exhaustion | Request-size cap, field limits, rate limiting | Use gateway/WAF limits and a distributed limiter at scale |
| Malformed input | Strict schemas; unknown fields rejected | Add content moderation for public deployments |
| PII in logs | Structured metadata only; payloads are never logged | Configure retention and access controls |
| Container escape | Non-root user, dropped capabilities, read-only filesystem | Scan and sign production images |
| Supply-chain risk | CI checks and Dependabot | Add hash-locked dependencies and an SBOM before release |
| Prompt injection | Offline deterministic agents by default | LLM adapters must treat job descriptions as untrusted data |

## Production checklist

- Replace development API keys and terminate TLS at the ingress.
- Use OAuth2/OIDC tokens with scopes for multiple tenants.
- Store secrets in a cloud secret manager; never in the image or repository.
- Define retention, deletion, and subject-access procedures for candidate PII.
- Encrypt transport and storage and restrict observability access.
- Replace the local limiter with Redis or gateway-level enforcement.
- Add vulnerability scanning, image signing, and an SBOM to releases.

## Reporting vulnerabilities

Do not open a public issue containing exploit details or candidate data. Contact the repository owner privately with reproduction steps and impact.

