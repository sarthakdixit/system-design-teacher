# Azure Deployment Runbook (Bicep-driven)

End-to-end deployment of the System Design Teacher platform to Azure. Total time: **~25 minutes** for a first deployment, **~5 minutes** for subsequent redeploys (most of which is GitHub Actions building the image).

> **Approach:** Infrastructure-as-Code via Bicep. Most resources are provisioned by `az deployment group create`. A few items (Entra app registration, GitHub repo linkage, Key Vault secret values) require manual steps because they're tenant-scoped or involve secrets that can't be in source control.
>
> See [`infra/README.md`](../infra/README.md) for a deeper dive into the Bicep modules.

---

## Prerequisites

- Active Azure subscription (Pay-As-You-Go or equivalent)
- Azure CLI installed: `az --version` should print 2.50+
- Docker installed locally (for the first image push)
- Docker Hub account with an access token (Account Settings → Security → New Access Token)
- This repo pushed to GitHub with `main` as the default branch
- Local stack works (`docker compose up`, `/health/deep` returns 200)

---

## Phase 1 — One-time manual prerequisites (~10 minutes)

These can't be in Bicep because they're tenant-scoped or involve OAuth flows.

### Step 1 — Create the resource group

```bash
az login
az account show  # confirm correct subscription, switch with az account set if needed
az group create --name rg-sdt-prod --location eastus2
```

### Step 2 — Register the Microsoft Entra app

This is the OAuth identity for Microsoft sign-in. Tenant-scoped, so Bicep can't do it.

1. Portal → **Microsoft Entra ID** → **App registrations** → **+ New registration**.
2. Fill in:
   - **Name**: `system-design-teacher`
   - **Supported account types**: **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts"**
   - **Redirect URI**: leave blank (we'll add the Static Web App URL in Phase 4)
3. Click **Register**.
4. From the Overview pane, **save these two values** (you'll paste them into Key Vault later):
   - **Application (client) ID** → save as `MICROSOFT_CLIENT_ID`
   - **Directory (tenant) ID** → save as `MICROSOFT_TENANT_ID` (or use the literal string `common` for multi-tenant)
5. Left sidebar → **Authentication** → **+ Add a platform** → **Single-page application**.
6. **Redirect URIs**: temporarily add `http://localhost:5173`. We'll add the production URL in Phase 4.
7. **Implicit grant and hybrid flows**: leave both unchecked.
8. Click **Configure**.

### Step 3 — Create a service principal for GitHub Actions

```bash
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az ad sp create-for-rbac \
  --name "github-actions-sdt" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-sdt-prod \
  --json-auth
```

**Copy the entire JSON output.** You'll need it in Phase 5. The `clientSecret` cannot be retrieved later — save the JSON now.

### Step 4 — Get your object ID

For the Bicep parameter file (grants you Key Vault Secrets Officer role).

```bash
az ad signed-in-user show --query id -o tsv
```

Save the output.

✅ **Phase 1 done.** You should have:

- Resource group `rg-sdt-prod` created
- Entra app's client ID + tenant ID
- Service principal JSON for GitHub Actions
- Your own object ID

---

## Phase 2 — Run Bicep (~10 minutes)

This provisions every Azure resource in one command.

### Step 5 — Configure Bicep parameters

```bash
cd infra
cp parameters.example.json parameters.json
```

Edit `parameters.json`:

- Set `deployingUserObjectId.value` to your object ID from Step 4
- Verify `namePrefix.value` is `sk` (or whatever you chose)
- Verify `location.value` is `eastus2`

> ⚠️ **`parameters.json` is gitignored.** Don't commit it. Only `parameters.example.json` should be in source control.

### Step 6 — Validate and preview

```bash
# Validate (catches syntax errors before deploying)
az deployment group validate \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json

# Preview what will be created
az deployment group what-if \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json
```

Validate should print `"provisioningState": "Succeeded"`. What-if should list ~12 resources to be created.

### Step 7 — Deploy

```bash
az deployment group create \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json \
  --name sdt-deploy-$(date +%Y%m%d-%H%M%S)
```

Takes **8–12 minutes**. Cosmos DB is the slowest (~7 min); everything else is faster.

### Step 8 — Capture outputs

```bash
DEPLOY_NAME=$(az deployment group list \
  --resource-group rg-sdt-prod \
  --query "[?contains(name, 'sdt-deploy')] | sort_by(@, &properties.timestamp) | [-1].name" \
  -o tsv)

az deployment group show \
  --resource-group rg-sdt-prod \
  --name "$DEPLOY_NAME" \
  --query "properties.outputs" \
  -o json > outputs.json

cat outputs.json
```

Save the values:

- `cosmosConnectionString.value` → goes into Key Vault as `MONGO-URI`
- `keyVaultUrl.value` → already wired into Container App env vars by Bicep (informational)
- `appInsightsConnectionString.value` → already wired (informational)
- `containerAppUrl.value` → save as `BACKEND_URL` (frontend `VITE_API_BASE_URL`)
- `staticWebAppUrl.value` → save as `FRONTEND_URL`
- `staticWebAppApiToken.value` → save for GitHub Actions secret

> ⚠️ `outputs.json` contains the Cosmos connection string and SWA token. **Delete after capturing values:**
>
> ```bash
> rm outputs.json
> ```

✅ **Phase 2 done.** All Azure resources exist. The Container App is running a placeholder Microsoft hello-world image. The Static Web App exists but isn't connected to GitHub yet.

---

## Phase 3 — Populate Key Vault secrets (~3 minutes)

Bicep created the Key Vault but didn't put values in it (we don't put secrets in source control). The deployer (you) was granted Secrets Officer role, so you can populate via CLI.

```bash
KV_NAME=$(az keyvault list --resource-group rg-sdt-prod --query "[0].name" -o tsv)

az keyvault secret set --vault-name $KV_NAME --name OPENAI-API-KEY \
  --value "sk-..."

az keyvault secret set --vault-name $KV_NAME --name JWT-SECRET \
  --value "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"

az keyvault secret set --vault-name $KV_NAME --name MONGO-URI \
  --value "<paste from outputs.json>"

az keyvault secret set --vault-name $KV_NAME --name MICROSOFT-CLIENT-ID \
  --value "<from Step 2.4>"

az keyvault secret set --vault-name $KV_NAME --name MICROSOFT-TENANT-ID \
  --value "common"
```

✅ **Phase 3 done.** Key Vault is populated. The Container App's Managed Identity already has read access (Bicep granted this).

---

## Phase 4 — First image push & Static Web App linkage (~5 minutes)

### Step 9 — Build and push the Docker image (one time only)

After this initial push, GitHub Actions handles all future pushes automatically.

```bash
cd "/path/to/system-design-teacher"

docker login

docker build -f Dockerfile.functions \
  -t $YOUR_DOCKERHUB_USERNAME/sdt-backend:latest .

docker push $YOUR_DOCKERHUB_USERNAME/sdt-backend:latest
```

### Step 10 — Update Container App to use your image

```bash
APP_NAME=$(az containerapp list --resource-group rg-sdt-prod --query "[0].name" -o tsv)

az containerapp update \
  --name $APP_NAME \
  --resource-group rg-sdt-prod \
  --image $YOUR_DOCKERHUB_USERNAME/sdt-backend:latest
```

Wait ~30 seconds, then test:

```bash
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group rg-sdt-prod \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

curl https://$APP_URL/health
# Expected: 200 with {"status": "ok"}

curl https://$APP_URL/health/deep | python -m json.tool
# Expected: 200 with every component "ok"
```

If `/health/deep` reports any component as `not ok`, check **Container App → Log stream** in the portal.

### Step 11 — Connect Static Web App to GitHub

The Bicep created the Static Web App resource shell. Linking it to your GitHub repo (the OAuth flow + build pipeline) is a portal step.

1. Portal → your Static Web App → **Overview**.
2. Click **Manage deployment token** → copy the **Deployment token** if not already saved.
3. Left sidebar → **Deployment Center**.
4. **Source**: GitHub
5. Sign in to GitHub if prompted, then:
   - **Organization**: your GitHub username
   - **Repository**: `system-design-teacher` (or your repo name)
   - **Branch**: `main`
6. **Build presets**: **Custom**
   - **App location**: `/frontend`
   - **Api location**: leave empty
   - **Output location**: `dist`
7. Click **Save**. This commits a `.github/workflows/azure-static-web-apps-{...}.yml` file to your repo and triggers the first build.

### Step 12 — Configure frontend environment variables

In your Static Web App → **Configuration** → **+ Add**, for each:

| Setting name               | Value                           |
| -------------------------- | ------------------------------- |
| `VITE_API_BASE_URL`        | from Step 8 (`containerAppUrl`) |
| `VITE_AUTH_MODE`           | `msal`                          |
| `VITE_MICROSOFT_CLIENT_ID` | from Step 2.4                   |
| `VITE_MICROSOFT_TENANT_ID` | from Step 2.4 (or `common`)     |

Click **Save**.

Re-run the latest GitHub Actions workflow on your repo to pick up the new env vars (they're baked into the build). Or push any commit to `main`.

### Step 13 — Update CORS and Entra redirect URI

Now that the Static Web App URL is real, the backend's CORS allow-list and the Entra app's redirect URIs need to know about it.

**Update backend CORS:**

```bash
APP_NAME=$(az containerapp list --resource-group rg-sdt-prod --query "[0].name" -o tsv)
SWA_URL=$(az staticwebapp list --resource-group rg-sdt-prod --query "[0].defaultHostname" -o tsv)

az containerapp update \
  --name $APP_NAME \
  --resource-group rg-sdt-prod \
  --set-env-vars "CORS_ALLOWED_ORIGINS=[\"https://$SWA_URL\",\"http://localhost:5173\"]"
```

**Update Entra redirect URI:**

1. Portal → your Entra app registration (Step 2) → **Authentication**.
2. Under **Single-page application** redirect URIs, click **Add URI**.
3. Paste `https://<your-swa-hostname>` (the SWA URL from above, with `https://`).
4. Click **Save**.

✅ **Phase 4 done.** Backend is running your image, frontend is deployed, CORS is open for the production URL, and Microsoft sign-in will redirect correctly.

---

## Phase 5 — Wire up CI/CD (~3 minutes)

Now make every future deploy automatic.

### Step 14 — Add GitHub Actions secrets

In your GitHub repo: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

| Secret name                | Value                                                                    |
| -------------------------- | ------------------------------------------------------------------------ |
| `AZURE_CREDENTIALS`        | the entire JSON from Step 3                                              |
| `DOCKERHUB_USERNAME`       | your Docker Hub username                                                 |
| `DOCKERHUB_TOKEN`          | Docker Hub access token (Account Settings → Security → New Access Token) |
| `AZURE_CONTAINER_APP_NAME` | from Step 10 (`$APP_NAME`)                                               |
| `AZURE_RESOURCE_GROUP`     | `rg-sdt-prod`                                                            |

The `AZURE_STATIC_WEB_APPS_API_TOKEN_*` secret was added automatically when you linked the SWA to GitHub in Step 11.

### Step 15 — Verify CI/CD works

Push any change to `backend/`:

```bash
git checkout -b test/cicd-verification
echo "# CI/CD verification" >> backend/README.md
git add backend/README.md
git commit -m "test: verify CI/CD"
git push origin test/cicd-verification
```

Open the PR on GitHub. The **CI** workflow (`.github/workflows/ci.yml`) should run with three jobs: backend, frontend, bicep. All should be green.

Merge the PR. The **Deploy** workflow (`.github/workflows/deploy.yml`) should run, build the image, push to Docker Hub, and update the Container App.

---

## Phase 6 — Final smoke test (~2 minutes)

### Step 16 — Set up the budget alert

1. Portal → **Cost Management + Billing** → **Cost Management** → **Budgets**.
2. **+ Add**:
   - **Scope**: your subscription
   - **Name**: `sdt-monthly-budget`
   - **Reset period**: `Billing month`
   - **Amount**: `5` USD
   - **Action group**: create one with email action → your email
   - **Alert thresholds**: 50%, 80%, 100%
3. **Save**.

### Step 17 — End-to-end smoke test

1. Open `https://<your-swa-hostname>` in a browser.
2. Click **Sign in with Microsoft**, authenticate with any Microsoft account.
3. Land on the home page logged in.
4. Try a small situation question.
5. Try a small design canvas submission.

If both succeed, **production is fully live**.

✅ **Deployment complete.** From here, every push to `main` rebuilds and redeploys the backend automatically. Frontend redeploys on the same push via the auto-generated SWA workflow.

---

## Subsequent deployments

Once Phases 1–5 are done, redeploys are essentially free:

- **Backend code change**: `git push origin main` → CI/CD rebuilds image, updates Container App. ~5 minutes.
- **Frontend code change**: Same push triggers SWA's workflow. Build + deploy ~3 minutes.
- **Infrastructure change**: Edit Bicep, run via Actions UI: **Actions** tab → **Deploy** workflow → **Run workflow** with `force_full_redeploy: true`. ~10 minutes.

---

## Common issues

### Bicep deploy fails with "Free tier already enabled on another account"

- One Cosmos free-tier account allowed per subscription. Either delete the existing one, or set `enableCosmosFreeTier: false` in `parameters.json` (this Cosmos costs ~$24/month).

### `/health/deep` returns 503 with `secrets: false`

- The Container App's Managed Identity hasn't propagated. Wait 2 minutes after Bicep finishes and try again.
- If still failing: portal → Container App → **Revisions** → **Restart** the active revision. Forces re-init of `DefaultAzureCredential`.

### "401 Unauthorized" on first sign-in

- The Static Web App URL isn't in the Entra app's redirect URIs. Re-do Step 13.
- Or `MICROSOFT_CLIENT_ID` in Key Vault doesn't match the Entra Application (client) ID.

### "CORS blocked" in browser console

- The Static Web App URL isn't in `CORS_ALLOWED_ORIGINS` on the Container App. Re-do Step 13's first half.
- JSON array format must be exact: `["https://...","http://localhost:5173"]` — no spaces, double quotes only.

### Container App keeps showing the placeholder Microsoft hello-world page

- You ran Bicep but skipped Step 10. Bicep deploys with a placeholder image; you have to push your real image and update the app.

### Cosmos `Request rate is large` (429)

- Free tier caps at 1000 RU/s. Check **Cosmos → Metrics → Throttled Requests**.
- Reduce write volume or pay for more RU/s (~$24/month for 1000 RU/s extra above free tier).

### CI workflow fails on `mypy`

- Type errors don't block PR merge (`continue-on-error: true` on the mypy step). Look at the run output for what to fix; treat as advisory.

### Deploy workflow fails on "Wait for new revision to be ready"

- New revision is in error state. Portal → Container App → **Log stream** for the traceback.
- Most common cause: a Key Vault secret is missing, malformed, or the Managed Identity lost its role assignment.

---

## Tearing down

Single command nukes everything inside the resource group:

```bash
az group delete --name rg-sdt-prod --yes
```

The Entra app registration is in a separate scope — delete it manually:

```bash
APP_ID="<your-client-id>"
az ad app delete --id $APP_ID
```

The auto-generated `azure-static-web-apps-{...}.yml` in your repo can be deleted too once the SWA is gone.

You can re-deploy from scratch in ~25 minutes by following Phases 1–6 again.

---

## What this runbook does NOT cover

- **Custom domains** for backend (Container Apps) or frontend (SWA). Both support custom domains with SSL; details are out of MVP scope.
- **Multi-environment** (dev/staging/prod). For real multi-env, parameterize `parameters.json` per environment and deploy to separate resource groups.
- **Production hardening**: WAF, private endpoints, network restrictions, vault firewall rules.
- **Cosmos backup strategy beyond defaults** (point-in-time restore, geo-redundancy).

These are reasonable next steps if the project moves past portfolio scope.
