# 07 — Deployment

The AI assistant follows the same GitOps flow used by all other code in this system. No manual server commands are needed for code changes.

## Full Deployment Flow

```
Developer edits code locally (C:/erp/prime/)
         ↓
git commit + git push → AyoubDahir/prime (GitHub)
         ↓
Update CACHE_BUSTER in C:/erp/argocd/erpnext-build/Dockerfile
git commit + git push → AyoubDahir/argocd (GitHub)
         ↓
GitHub Actions triggered (push to main, path: erpnext-build/Dockerfile)
         ↓
Job 1: Build Docker image
  - Clones all apps from apps.json (including AyoubDahir/prime main branch)
  - pip installs all requirements.txt from each app
    → anthropic>=0.40.0 installed here
  - Runs bench build (compiles JS/CSS assets)
  - Pushes image: ghcr.io/ayoubdahir/erpnext-custom:theme-<sha>
         ↓
Job 2: Update GitOps
  - Updates erpnext-gitops/environments/erpnext/values.yaml with new image tag
  - Commits: "ci: deploy erpnext-custom:theme-<sha>"
  - Pushes to AyoubDahir/argocd main branch
         ↓
ArgoCD detects values.yaml change (auto-sync every 3 min)
         ↓
ArgoCD PreSync: job-configure-bench
  - bench migrate --skip-failing   ← REGISTERS THE NEW PAGE
  - bench clear-cache
  - materializes assets
         ↓
ArgoCD deploys new pods with new image
  - erpnext-dev-gunicorn (new)
  - erpnext-dev-worker-* (new)
         ↓
New AI assistant page live at /app/ai-assistant
Total time: ~7-10 minutes
```

## What Triggers the Rebuild

The GitHub Actions workflow only runs on push to main when specific files change:

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'erpnext-build/Dockerfile'
      - 'erpnext-build/apps.json'
      - '.github/workflows/build-deploy.yml'
```

Pushing prime code alone does **not** trigger the build — only changes to the argocd repo trigger it. This is why we update the `CACHE_BUSTER` in the Dockerfile when deploying prime changes: it touches a file in the path list, triggering the workflow, and forces Docker to re-clone the prime app (otherwise Docker layer caching would use the old clone).

## CACHE_BUSTER Explained

```dockerfile
ARG CACHE_BUSTER=ai-assistant-v1
```

Docker caches each `RUN` layer. If the commands haven't changed, Docker reuses the cached layer — which means it would NOT re-clone the prime app from GitHub. The `CACHE_BUSTER` arg is passed to the bench init command:

```dockerfile
RUN set -e && \
  echo "Cache buster: ${CACHE_BUSTER}" && \
  bench init ...
```

When `CACHE_BUSTER` changes (e.g., from `launchpad-fullwidth-v2` to `ai-assistant-v1`), Docker sees a different ARG value and invalidates the cache for that layer and all subsequent layers. This forces a fresh `bench init` which re-clones `AyoubDahir/prime` and picks up the latest code.

**Rule:** Every time you push prime code and want it deployed, change the `CACHE_BUSTER` value in `erpnext-build/Dockerfile` to something new.

## The anthropic Package

`anthropic>=0.40.0` is in `prime/requirements.txt`. During `bench init --apps_path=apps.json`, bench installs each app and its `requirements.txt`. So when the Docker image is built, `pip install anthropic` runs automatically — no manual installation needed.

The `requirements.txt` is already committed and pushed to GitHub, so all future image rebuilds will include the package automatically.

## API Key Configuration

The Anthropic API key is **not** in git. It is set directly in `site_config.json` on the server:

```bash
kubectl exec -it erpnext-dev-gunicorn-<pod-id> -n erpnext-dev -- \
  bench --site alihsans.com set-config anthropic_api_key "sk-ant-..."
```

This writes to:
```
/home/frappe/frappe-bench/sites/alihsans.com/site_config.json
```

This file lives on the persistent NVMe volume (`erpnext-sites-pv`) and survives pod restarts and image updates. Setting it once is permanent until you change it.

## bench migrate and Page Registration

When `bench migrate` runs (in the ArgoCD PreSync job), Frappe:
1. Reads all `*.json` files in `page/` directories of all installed apps
2. Syncs them to the database (creates or updates the Page doctype record)
3. The page becomes accessible at `/app/ai-assistant`

This is why no SQL command is needed to register the page — Frappe handles it via migrate.

## Verifying Deployment

After the CI/CD pipeline completes, verify on the server:

```bash
# Check new pod is running
kubectl get pods -n erpnext-dev | grep gunicorn

# Check the page exists in DB
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com execute \
  "print(frappe.db.exists('Page', 'ai-assistant'))"
# Should print: ai-assistant

# Check anthropic is installed
kubectl exec -it erpnext-dev-gunicorn-<pod> -n erpnext-dev -- \
  bench --site alihsans.com execute \
  "import anthropic; print(anthropic.__version__)"
```

## Rollback

If the new image causes issues, ArgoCD can roll back by reverting the `values.yaml` image tag commit in the argocd repo:

```bash
cd C:/erp/argocd
git revert HEAD
git push origin main
```

ArgoCD will auto-sync to the previous image within minutes.
