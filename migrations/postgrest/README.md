# PostgREST Setup

⚠️ **This directory is deprecated** - PostgREST setup is now part of the Phlo package.

## New Way (Recommended)

```bash
# Setup PostgREST authentication infrastructure
phlo api setup-postgrest
```

This command (part of the Phlo package) sets up:
- PostgreSQL extensions (pgcrypto)
- Auth schema and users table
- JWT signing/verification functions
- Database roles (anon, authenticated, analyst, admin)
- Row-Level Security policies

## Domain-Specific Views

The core Phlo setup does **NOT** create API views for your data - that's your responsibility.

See `examples/` directory for glucose-monitoring examples showing how to:
- Create API views exposing your mart data
- Create PostgreSQL functions for computed endpoints

**You should create similar views for YOUR domain/data.**

## Migration from Old Scripts

If you were using the old `apply_migrations.sh` script:

**Before:**
```bash
cd migrations/postgrest
./apply_migrations.sh
```

**After:**
```bash
phlo api setup-postgrest
```

The new command is:
- ✅ Part of the Phlo package
- ✅ Idempotent (safe to run multiple times)
- ✅ Properly separated (core infrastructure vs. domain-specific views)
- ✅ Can be used programmatically from Python

## Location

Core infrastructure SQL files are now in:
```
src/phlo/api/postgrest/sql/
├── 001_extensions.sql
├── 002_auth_schema.sql
├── 003_jwt_functions.sql
└── 004_roles.sql
```

These are bundled with the Phlo package and managed via `phlo api setup-postgrest`.
