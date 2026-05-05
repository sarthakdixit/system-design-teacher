# Infrastructure (Bicep IaC)

Provisions all Azure resources for the System Design Teacher platform. One command spins everything up; one command tears everything down.

> See [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md) for the full end-to-end deployment runbook (manual prerequisites, Bicep deploy, post-Bicep config). This README covers just the Bicep portion.

---

## File layout

```
infra/
├── README.md                   ← this file
├── main.bicep                  ← entry point; wires modules together
├── parameters.example.json     ← copy to parameters.json and edit
├── parameters.json             ← gitignored; your actual deploy values
└── modules/
    ├── cosmos.bicep            ← Cosmos DB free tier + Mongo API
    ├── keyvault.bicep          ← Key Vault with RBAC
    ├── insights.bicep          ← App Insights + Log Analytics
    ├── containerapps.bicep     ← Container Apps Environment + Container App
    └── staticwebapp.bicep      ← Static Web App
```

---

## What Bicep provisions

| Resource                                                                              | Free tier                           | Cost cap                         |
| ------------------------------------------------------------------------------------- | ----------------------------------- | -------------------------------- |
| Cosmos DB account (Mongo API, 5.0)                                                    | ✅ 1000 RU/s + 25 GB                | Capped at 1000 RU/s account-wide |
| 5 Mongo collections (users, questions, attempts, feedback_cache, rate_limit_counters) | shared 400 RU/s                     | within free tier                 |
| Key Vault (RBAC mode)                                                                 | ✅ 10k transactions/month           | —                                |
| Log Analytics workspace                                                               | ✅ 5 GB/month                       | capped at 1 GB/day               |
| Application Insights (workspace-based)                                                | ✅ rides on Log Analytics free tier | —                                |
| Container Apps Environment (Consumption plan)                                         | ✅ 180k vCPU-sec + 360k GB-sec/mo   | —                                |
| Container App (0.25 vCPU, 0.5 GB, scale-to-zero)                                      | ✅ within env free tier             | min 0 / max 2 replicas           |
| Static Web App (Free SKU)                                                             | ✅ 100 GB bandwidth/month           | —                                |
| Role assignments                                                                      | Free                                | —                                |

**Expected steady-state cost: $0/month** for portfolio-scale usage.

---

## What Bicep does NOT provision

These are out of scope for resource-group-level Bicep and must be done manually:

1. **Microsoft Entra app registration** (tenant-scope, not subscription-scope)
2. **Service principal for GitHub Actions** (created via `az ad sp create-for-rbac`)
3. **Key Vault secret VALUES** (we don't put real secrets in IaC)
4. **GitHub Actions secrets** (not Azure resources)
5. **Linking Static Web App to GitHub** (OAuth flow doesn't fit declarative IaC)
6. **Pushing the initial Docker image** (handled separately, then CI/CD)

The full sequence (with the manual steps interleaved) is in [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md).

---

## Quick start

### 1. Prerequisites

- Azure CLI: `az --version` should print 2.50+
- Logged in: `az login` and `az account show` should print your subscription
- Docker installed (for building the image, post-Bicep)

### 2. Get your object ID

```bash
az ad signed-in-user show --query id -o tsv
```

Save the output. You'll paste it into `parameters.json`.

### 3. Create the resource group (one-time)

```bash
az group create --name rg-sdt-prod --location eastus2
```

### 4. Copy and edit the parameters file

```bash
cd infra
cp parameters.example.json parameters.json
```

Open `parameters.json` and:

- Set `deployingUserObjectId.value` to the output from step 2
- Adjust `namePrefix.value` if you want something other than `sk`
- Adjust `location.value` if not `eastus2`

> ⚠️ Don't commit `parameters.json`. It's gitignored.

### 5. Validate the Bicep (catches syntax / reference errors before deploying)

```bash
az deployment group validate \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json
```

Expect `"provisioningState": "Succeeded"` in the output.

### 6. Preview what will be deployed

```bash
az deployment group what-if \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json
```

Should list ~12 resources with `+ Create` next to each.

### 7. Deploy

```bash
az deployment group create \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json \
  --name sdt-deploy-$(date +%Y%m%d-%H%M%S)
```

Takes **8–12 minutes**. Cosmos DB is the slowest resource (~7 minutes); everything else completes in 1–2.

### 8. Capture the outputs

```bash
az deployment group show \
  --resource-group rg-sdt-prod \
  --name <deployment-name-from-step-7> \
  --query "properties.outputs" \
  -o json > outputs.json
```

This file contains:

- `cosmosConnectionString` — paste into Key Vault as `MONGO-URI`
- `keyVaultUrl` — for the Container App env var (already set by Bicep)
- `appInsightsConnectionString` — same
- `containerAppUrl` — frontend's `VITE_API_BASE_URL`
- `containerAppPrincipalId` — the Container App's Managed Identity (already granted KV access by Bicep)
- `staticWebAppUrl` — your frontend URL
- `staticWebAppApiToken` — for GitHub Actions secret

> ⚠️ `outputs.json` contains secrets. Don't commit it. Delete after capturing values:
> `rm outputs.json`

### 9. Populate Key Vault secrets

```bash
KEY_VAULT_NAME="kv-sdt-sk"  # or whatever your namePrefix produced

az keyvault secret set --vault-name $KEY_VAULT_NAME --name OPENAI-API-KEY --value "sk-..."
az keyvault secret set --vault-name $KEY_VAULT_NAME --name JWT-SECRET --value "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name MONGO-URI --value "<paste from outputs.json>"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name MICROSOFT-CLIENT-ID --value "<from Entra app registration>"
az keyvault secret set --vault-name $KEY_VAULT_NAME --name MICROSOFT-TENANT-ID --value "common"
```

### 10. Continue with `docs/DEPLOYMENT.md`

The rest (Docker image push, Container App image swap, Static Web App linkage, smoke test) is covered in the main deployment runbook.

---

## Modifying infrastructure later

Bicep is idempotent. Make a change, re-run `az deployment group create`, and Bicep figures out what to update.

```bash
# Change something in main.bicep or a module, then:
az deployment group create \
  --resource-group rg-sdt-prod \
  --template-file main.bicep \
  --parameters parameters.json \
  --name sdt-update-$(date +%Y%m%d-%H%M%S)
```

Use `--what-if` first to preview changes before applying.

### Common changes

- **Bump max replicas:** edit `parameters.json` to add a `containerApps` override, or modify `containerapps.bicep` directly.
- **Change region:** edit `location.value` in `parameters.json` and re-deploy. Most resources can't be moved between regions — Bicep will replace them, which means data loss for Cosmos. Don't do this casually.
- **Switch to always-on Container App:** set `minReplicas: 1` in `containerapps.bicep`. Adds ~$10/mo, eliminates cold start.

---

## Tearing down

```bash
az group delete --name rg-sdt-prod --yes
```

Deletes everything in the resource group in one shot. Soft-deleted Key Vault stays around for 7 days (you set `softDeleteRetentionInDays: 7` in `keyvault.bicep`); after that it's purged automatically.

The Entra app registration lives outside the resource group — delete it separately:

```bash
APP_ID="<your client id>"
az ad app delete --id $APP_ID
```

---

## Troubleshooting

### "Free tier already enabled on another account"

Cosmos DB's free tier limit is one per subscription. Either:

- Find and delete the other free-tier account, or
- Set `enableCosmosFreeTier: false` in `parameters.json` (the new account costs ~$24/month minimum)

### "The principal does not have permission..."

The user running `az deployment group create` doesn't have `Owner` or `User Access Administrator` on the resource group. Bicep needs to create role assignments, which require those roles. Add yourself or use a Privileged Identity Management role.

### "ResourceProvider not registered"

First-time use of Container Apps in a subscription. Register:

```bash
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.DocumentDB --wait
```

Then retry the deploy.

### Static Web App in `southindia` / `centralindia` etc

SWA's region pool is `centralus, eastus2, westus2, westeurope, eastasia`. The Bicep parameter `staticWebAppLocation` enforces this. If you set it to an unsupported region, validation fails before the deploy starts.

### Deployment hangs at Cosmos for >15 minutes

Normal Cosmos provisioning takes 5–10 min. If it's still going at 20+ min, check the Activity Log in the portal. Most common: subscription quota for Cosmos accounts (default 5 per region) hit. Request a quota increase or pick a different region.

---

## What's next

After Bicep runs successfully and you've worked through the rest of `docs/DEPLOYMENT.md`:

1. **Confirm the smoke test passes** (sign in, submit a design)
2. **CI/CD workflows** in `.github/workflows/` (Group C of Batch 5) take over from there — every push to `main` rebuilds and redeploys automatically
