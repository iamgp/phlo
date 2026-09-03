# phlo-oauth2-proxy

OAuth2/OIDC authentication proxy for Phlo services.

## Overview

`phlo-oauth2-proxy` provides a forward-authentication gateway using [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/). When paired with `phlo-traefik`, it protects `phlo-api` and other surfaces behind SSO authentication.

## Service Metadata

| Field | Value |
|-------|-------|
| Name | `oauth2-proxy` |
| Category | `auth` |
| Profile | `proxy` |
| Default | `false` (opt-in) |
| Image | `quay.io/oauth2-proxy/oauth2-proxy:v7.7.1` |

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH2_PROXY_PROVIDER` | `oidc` | OAuth2 provider type (oidc, google, github, etc.) |
| `OAUTH2_PROXY_OIDC_ISSUER_URL` | - | OIDC issuer URL (required for oidc provider) |
| `OAUTH2_PROXY_CLIENT_ID` | - | OAuth2 client ID from your identity provider |
| `OAUTH2_PROXY_CLIENT_SECRET` | - | OAuth2 client secret |
| `OAUTH2_PROXY_COOKIE_SECRET` | - | Random 32-byte base64 string for cookie encryption |
| `OAUTH2_PROXY_COOKIE_SECURE` | `false` | Set to `true` when using HTTPS |
| `OAUTH2_PROXY_REDIRECT_URL` | `http://api.phlo.localhost/oauth2/callback` | OAuth2 callback URL |
| `OAUTH2_PROXY_EMAIL_DOMAINS` | `*` | Comma-separated list of allowed email domains |

### Generate Cookie Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Usage

### 1. Configure IdP Credentials

Add to `.phlo/.env.local`:

```env
OAUTH2_PROXY_OIDC_ISSUER_URL=https://your-idp.example.com
OAUTH2_PROXY_CLIENT_ID=your-client-id
OAUTH2_PROXY_CLIENT_SECRET=your-client-secret
OAUTH2_PROXY_COOKIE_SECRET=<generated-secret>
```

### 2. Start with Proxy Profile

```bash
phlo services start --profile proxy
```

## Architecture

```
browser -> traefik -> oauth2-proxy (auth check) -> phlo-api -> phlo authorization
```

When a request hits Traefik for `api.<domain>`:

1. Traefik's `forwardAuth` middleware sends a subrequest to `oauth2-proxy`
2. If not authenticated, `oauth2-proxy` redirects to the IdP login page
3. After successful authentication, `oauth2-proxy` returns 202 with identity headers
4. Traefik forwards the request to `phlo-api` with identity headers:
   - `X-Forwarded-User`
   - `X-Forwarded-Email`
   - `X-Forwarded-Groups`
5. `phlo-api`'s `proxy` authentication provider reads these headers

## Security Notes

- `oauth2-proxy` is internal-only (no `traefik.enable` label)
- Only reachable within the Docker network
- Direct access to `phlo-api` on port 4000 bypasses proxy auth
- In regulated deployments, restrict direct port access

## Troubleshooting

### Redirect loop

Check that `OAUTH2_PROXY_REDIRECT_URL` matches exactly what your IdP expects (including protocol and trailing slashes).

### 401 after login

Verify `OAUTH2_PROXY_EMAIL_DOMAINS` includes the authenticated user's email domain.

### Headers not reaching phlo-api

Verify Traefik's `trustForwardHeader: true` is set and `authResponseHeaders` includes all three headers.
