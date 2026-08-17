# Security Posture

QuantumGrow handles real money and requires robust security practices.

## Broker Credentials

- **API Keys & Secrets**: Managed purely via environment variables.
- **`.env` Protection**: All secrets must be injected via `.env` (local) or Secret variables (Render). The repository enforces `.gitignore` rules to prevent accidental exposure of these files.
- **No Hardcoding**: Credentials, such as `CLIENT_ID`, are never hardcoded into the source code.

## Network Security

- **CORS Restriction**: CORS is tightly restricted to standard development and production domains (`localhost` and the deployed frontend domain).
- **Security Headers**: Standard security headers (HSTS, X-Content-Type-Options, X-Frame-Options, X-XSS-Protection) are applied at the middleware level.

## Authorization

- **Admin API Key**: Actions that alter system state (e.g., executing a trade, closing a trade, retraining models, switching runtime modes) are protected by an `x-admin-key` HTTP header.
- **Path Traversal Protection**: The static SPA file server explicitly prevents relative path traversals (like `../../../.env`) by strictly resolving against the `dist` boundary.

## Rate Limiting

- Mode switching endpoints are protected by in-memory rate-limiting to prevent rapid-fire state thrashing that could lead to broker connection bans or memory leaks.
