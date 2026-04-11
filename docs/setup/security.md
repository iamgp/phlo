# Security Setup Guide

This guide covers enterprise security configuration for Phlo, including authentication, authorization, encryption, and audit logging.

## Overview

Phlo's underlying services (Trino, Nessie, MinIO, PostgreSQL) support enterprise security features. This guide explains how to enable and configure them, and where Phlo's audit-log support stops and operator-owned controls begin.

| Feature | Trino | Nessie | MinIO | PostgreSQL |
|---------|-------|--------|-------|------------|
| LDAP Auth | Yes | No | Yes | No |
| OAuth2/OIDC | Yes | Yes | Yes | No |
| TLS/HTTPS | Yes | Yes | Yes | Yes |
| Access Control | Yes | Yes | Yes (IAM) | Yes (RLS) |
| Audit Logging | Query history and logs | Server logs | Webhook audit events | Operator-managed `pgaudit` |

## Quick Start

For a minimal secure setup, configure these environment variables in your `.phlo/.env.local`:

```bash
# Strong passwords (required)
POSTGRES_PASSWORD=<generate-strong-password>
MINIO_ROOT_PASSWORD=<generate-strong-password>

# Enable TLS (recommended for production)
POSTGRES_SSL_MODE=require
MINIO_SERVER_URL=https://minio.example.com

# Enable authentication (choose based on your IdP)
NESSIE_OIDC_ENABLED=true
NESSIE_OIDC_SERVER_URL=https://auth.example.com/realms/phlo
```

Generate strong passwords:

```bash
openssl rand -base64 32
```

## Audit-Log Posture

Phlo does not treat every log line as an audit record. Use this distinction:

- **Operational logs** are for debugging and service health.
- **Security and audit logs** capture authentication, authorization, and administrative events.
- **Query and access trails** show who read or queried data.

The supported production posture is:

| Surface | What You Get | Ownership |
|---------|---------------|-----------|
| `phlo-api` / Observatory | Structured application audit events and denials | Phlo-owned logging path |
| MinIO | Storage access audit events through webhook delivery | Phlo-owned configuration surface |
| Trino | Query history and coordinator logs | Shared, with retention/operator export left external |
| PostgreSQL | `pgaudit` or equivalent database audit controls | Operator-managed |
| Nessie | Server logs for catalog access visibility | Operator-managed retention |

Use [Audit Logging](../operations/audit-logging.md) as the source of truth for routing, retention, and production checklist expectations.

## Authentication

### Phlo Reverse Proxy Authentication

If you put Phlo behind a trusted reverse proxy, configure the app to accept asserted identity
headers only from that proxy and bind those headers into a shared-secret signature:

```bash
# .phlo/.env.local
PHLO_AUTH_PROXY_ENABLED=true
PHLO_AUTH_PROXY_TRUSTED_PROXIES=127.0.0.1/32,10.0.0.0/8
PHLO_AUTH_PROXY_SHARED_SECRET=<generate-strong-random-secret>
PHLO_AUTH_PROXY_HEADER_SUBJECT=X-Remote-User
PHLO_AUTH_PROXY_HEADER_EMAIL=X-Remote-Email
PHLO_AUTH_PROXY_HEADER_GROUPS=X-Remote-Groups
```

When `PHLO_AUTH_PROXY_SHARED_SECRET` is set, the proxy must sign the timestamp, remote address,
request path, and asserted identity headers so downstream header changes are rejected.

### Option 1: LDAP Authentication

LDAP works with Trino and MinIO. Configure your LDAP server details:

#### Trino LDAP

```bash
# .phlo/.env.local
TRINO_AUTH_TYPE=PASSWORD
TRINO_LDAP_URL=ldaps://ldap.example.com:636
TRINO_LDAP_USER_BIND_PATTERN=${USER}@example.com
```

Users authenticate with their LDAP credentials when connecting to Trino.

#### MinIO LDAP

```bash
# .phlo/.env.local
MINIO_LDAP_SERVER=ldap.example.com:636
MINIO_LDAP_BIND_DN=cn=admin,dc=example,dc=com
MINIO_LDAP_BIND_PASSWORD=ldap-admin-password
MINIO_LDAP_USER_BASE_DN=ou=users,dc=example,dc=com
MINIO_LDAP_USER_FILTER=(uid=%s)
```

### Option 2: OAuth2/OIDC Authentication

OIDC works with all services and is recommended for unified SSO.

#### Prerequisites

1. An OIDC provider (Keycloak, Auth0, Okta, Azure AD, etc.)
2. Create clients for each service:
   - `nessie` - for Nessie catalog
   - `minio` - for MinIO storage
   - `trino` - for Trino query engine

#### Nessie OIDC

```bash
# .phlo/.env.local
NESSIE_OIDC_ENABLED=true
NESSIE_OIDC_SERVER_URL=https://auth.example.com/realms/phlo
NESSIE_OIDC_CLIENT_ID=nessie
NESSIE_OIDC_CLIENT_SECRET=your-client-secret
```

#### MinIO OIDC

```bash
# .phlo/.env.local
MINIO_OIDC_CONFIG_URL=https://auth.example.com/realms/phlo/.well-known/openid-configuration
MINIO_OIDC_CLIENT_ID=minio
MINIO_OIDC_CLIENT_SECRET=your-client-secret
MINIO_OIDC_CLAIM_NAME=policy
```

The `policy` claim in the JWT should contain the MinIO policy name(s) to assign.

#### Trino OAuth2

```bash
# .phlo/.env.local
TRINO_AUTH_TYPE=OAUTH2
TRINO_OAUTH2_ISSUER=https://auth.example.com/realms/phlo
TRINO_OAUTH2_CLIENT_ID=trino
TRINO_OAUTH2_CLIENT_SECRET=your-client-secret
```

### Keycloak Example Setup

If using Keycloak as your identity provider:

1. Create a realm called `phlo`
2. Create clients:

```json
{
  "clientId": "nessie",
  "protocol": "openid-connect",
  "publicClient": false,
  "standardFlowEnabled": true,
  "serviceAccountsEnabled": true
}
```

3. Create users and assign roles
4. Map roles to policies in MinIO

## Authorization

Phlo's canonical authorization workflow starts in `.phlo/authorization/` and
then compiles into backend-native enforcement. Define roles and policies there
first, validate them with `phlo authz validate`, preview with `phlo authz plan`,
apply with `phlo authz sync`, and use the service-specific setup below to make
those compiled artifacts effective in each backend.

Use [Canonical RBAC](../reference/canonical-rbac.md) for the source-of-truth
model, command behavior, and backend support limits.

### Trino Access Control

Create an access control rules file:

```json
{
  "catalogs": [
    {
      "catalog": "iceberg",
      "allow": "all"
    }
  ],
  "schemas": [
    {
      "catalog": "iceberg",
      "schema": "raw",
      "owner": false
    }
  ],
  "tables": [
    {
      "catalog": "iceberg",
      "schema": ".*",
      "table": ".*",
      "privileges": ["SELECT"],
      "filter": "department = current_user_department()"
    }
  ]
}
```

Enable in `.phlo/.env.local`:

```bash
TRINO_ACCESS_CONTROL_TYPE=file
TRINO_ACCESS_CONTROL_CONFIG_FILE=/etc/trino/access-control.json
```

Mount the rules file in your service configuration.

Canonical RBAC note:

- Trino currently has the strongest `phlo authz verify` coverage because the
  compiler can compare desired grants with current managed grants exposed by the
  governance backend.

### Nessie Authorization

Enable authorization:

```bash
NESSIE_AUTHZ_ENABLED=true
```

Nessie authorization rules are configured through the Nessie server. See [Nessie Authorization](https://projectnessie.org/features/authz/) for details.

Canonical RBAC note:

- `phlo authz` can compile Nessie authorization rules, but current verify
  coverage does not introspect live Nessie state for drift yet.

### MinIO IAM Policies

Create IAM policies for fine-grained access:

```bash
# Create a read-only policy
mc admin policy create local readonly-lake - <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::lake/*", "arn:aws:s3:::lake"]
    }
  ]
}
EOF

# Attach to user
mc admin policy attach local readonly-lake --user analyst
```

Canonical RBAC note:

- `phlo authz` can compile MinIO IAM policy documents for object access, but you
  still need principal-to-policy attachment through MinIO IAM or OIDC claims.

### PostgreSQL Row-Level Security

Phlo does not generate row-level policies for PostgREST API views. Generated `api.*`
views get `GRANT` statements only. When you need row-level enforcement, enable RLS on
the underlying tables and make sure your JWT/session context exposes the claims your
policies read:

```sql
-- Enable RLS on a table
ALTER TABLE marts.customers ENABLE ROW LEVEL SECURITY;

-- Create policy for analysts (see only their region)
CREATE POLICY analyst_region ON marts.customers
  FOR SELECT
  TO analyst
  USING (region = current_setting('app.user_region'));

-- Create policy for admins (see everything)
CREATE POLICY admin_all ON marts.customers
  FOR ALL
  TO admin
  USING (true);
```

For PostgREST-backed APIs, the JWT token must include the role and any custom claim
values your table policies depend on.

## Encryption

### TLS/HTTPS

#### PostgreSQL SSL

```bash
# .phlo/.env.local
POSTGRES_SSL_MODE=require
```

For certificate verification:

```bash
POSTGRES_SSL_MODE=verify-full
POSTGRES_SSL_CA_FILE=/path/to/ca.pem
```

#### MinIO TLS

1. Place certificates in `./volumes/minio-certs/`:
   - `public.crt` - Server certificate
   - `private.key` - Private key
   - `CAs/` - CA certificates (optional)

2. Enable TLS:

```bash
MINIO_SERVER_URL=https://minio.example.com:9000
```

#### Trino HTTPS

1. Create a Java keystore:

```bash
keytool -genkeypair -alias trino -keyalg RSA -keysize 2048 \
  -keystore keystore.jks -validity 365 \
  -dname "CN=trino.example.com"
```

2. Enable HTTPS:

```bash
TRINO_HTTPS_ENABLED=true
TRINO_HTTPS_KEYSTORE_PATH=/etc/trino/keystore.jks
TRINO_HTTPS_KEYSTORE_PASSWORD=your-keystore-password
```

### Encryption at Rest

#### MinIO Server-Side Encryption

```bash
MINIO_AUTO_ENCRYPTION=on
```

This encrypts all objects automatically using MinIO's built-in encryption.

For KMS-based encryption, configure a KMS provider:

```bash
MINIO_KMS_KES_ENDPOINT=https://kes.example.com:7373
MINIO_KMS_KES_KEY_FILE=/path/to/kes-key.key
MINIO_KMS_KES_CERT_FILE=/path/to/kes-cert.crt
MINIO_KMS_KES_KEY_NAME=my-key
```

## Audit Logging

### MinIO Audit Logs

Phlo supports MinIO audit webhook wiring directly through the bundled service package. Send those audit logs to a durable backend:

```bash
MINIO_AUDIT_ENABLED=on
MINIO_AUDIT_ENDPOINT=http://loki:3100/loki/api/v1/push
```

Or configure for Kafka:

```bash
MINIO_AUDIT_KAFKA_ENABLE=on
MINIO_AUDIT_KAFKA_BROKERS=kafka:9092
MINIO_AUDIT_KAFKA_TOPIC=minio-audit
```

### PostgreSQL Audit Logging

PostgreSQL audit logging remains operator-managed today. Enable `pgaudit` on a PostgreSQL build that includes the extension:

```sql
-- In PostgreSQL
CREATE EXTENSION IF NOT EXISTS pgaudit;
ALTER SYSTEM SET pgaudit.log = 'all';
SELECT pg_reload_conf();
```

### Trino Query Logging

Trino query history is available by default in the coordinator UI, but long-term retention and centralized export are still operator-managed:

```properties
# coordinator config
query.max-history=10000
```

If Trino query evidence is part of your compliance boundary, pair that history with an external retention path rather than relying on container-local logs alone.

## Existing Security Features

Phlo already includes these security features that you can use:

### PostgREST JWT Authentication

Located in `packages/phlo-postgrest/src/phlo_postgrest/sql/`:

- `003_jwt_functions.sql` - JWT signing and verification
- `004_roles.sql` - Role-based access control

Usage:

```bash
# Get a JWT token
curl -X POST http://localhost:10018/rpc/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token for authenticated requests
curl http://localhost:10018/customers \
  -H "Authorization: Bearer <token>"
```

### Hasura Permissions

Located in `packages/phlo-hasura/src/phlo_hasura/permissions.py`:

- Hasura itself supports row-level and column-level permissions across select, insert, update, and delete operations
- Phlo's packaged permission sync automates select, insert, update, and delete permission definitions from config
- Configure permissions either through the Hasura console/API directly or via Phlo's permission sync workflow

### Observatory Token Auth

Enable UI authentication:

```bash
OBSERVATORY_AUTH_ENABLED=true
OBSERVATORY_AUTH_TOKEN=your-secure-token
```

## Production Checklist

Before going to production, ensure:

- [ ] All default passwords changed
- [ ] TLS enabled for all services
- [ ] Authentication configured (LDAP or OIDC)
- [ ] Access control rules defined
- [ ] Audit logging enabled
- [ ] Secrets stored securely (not in git)
- [ ] Network segmentation (services not exposed publicly)
- [ ] Regular credential rotation policy

## Troubleshooting

### OIDC Token Issues

```bash
# Decode JWT to inspect claims
echo "<token>" | cut -d. -f2 | base64 -d | jq
```

### LDAP Connection Issues

```bash
# Test LDAP connection
ldapsearch -x -H ldaps://ldap.example.com:636 \
  -D "cn=admin,dc=example,dc=com" \
  -W -b "dc=example,dc=com" "(uid=testuser)"
```

### Certificate Issues

```bash
# Verify certificate
openssl s_client -connect minio.example.com:9000 -showcerts

# Check certificate dates
openssl x509 -in cert.pem -noout -dates
```

## Next Steps

- [Configuration Reference](../reference/configuration-reference.md) - All security variables
- [Operations Guide](../operations/operations-guide.md) - Deployment and operations guide
- [Observability Setup](observability.md) - Monitoring and logging
