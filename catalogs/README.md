# Catalog Management

Each environment has its own complete catalog file:

```
catalogs/
  catalog-dev.yaml    # Development environment
  catalog-uat.yaml    # User acceptance testing
  catalog-prod.yaml   # Production
```

## How it works

**Stable environments** (dev, uat, prod) — the build selects the right file via the `MONIKER_ENV` env var. The config resolves `./catalogs/catalog-${MONIKER_ENV}.yaml`.

**Sandboxes** (dynamic, per-branch) — the build copies the branch's root `catalog.yaml` directly. Developers edit it freely on their feature branch.

## Editing a catalog

Edit the YAML file for the target environment, commit, and the environment rebuilds with the updated catalog.

For example, if UAT feedback says a node's source binding is wrong:

1. Edit `catalogs/catalog-uat.yaml`
2. Commit and push
3. UAT rebuilds with the fix

## Promoting between environments

When a catalog is ready to move up (e.g. UAT -> prod):

```bash
cp catalogs/catalog-uat.yaml catalogs/catalog-prod.yaml
# Review the diff, adjust any env-specific bindings, commit
```

## Sandbox builds

Sandbox images are built from feature branches. The Dockerfile copies the branch's root `catalog.yaml`:

```dockerfile
# Sandbox (feature branch):
COPY catalog.yaml /app/catalog.yaml

# Stable env (main):
ARG MONIKER_ENV=dev
COPY catalogs/catalog-${MONIKER_ENV}.yaml /app/catalog.yaml
```

The service always reads `catalog.yaml` — it doesn't know which environment it's in.
