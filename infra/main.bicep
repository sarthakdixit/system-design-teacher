// =============================================================================
// System Design Teacher — Azure infrastructure (main.bicep)
// =============================================================================
// Single-file entry point that wires together all child modules.
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-sdt-prod \
//     --template-file infra/main.bicep \
//     --parameters infra/parameters.json
//
// Tear down everything:
//   az group delete --name rg-sdt-prod --yes

targetScope = 'resourceGroup'

// -----------------------------------------------------------------------------
// Parameters
// -----------------------------------------------------------------------------

@description('Short identifier baked into resource names (3-8 lowercase alphanumeric chars).')
@minLength(3)
@maxLength(8)
param namePrefix string

@description('Azure region for all resources except Static Web Apps.')
param location string = resourceGroup().location

@description('Region for Static Web Apps. Cannot be set to South India / East US 2 in some regions; defaults to centralus which has full free-tier coverage.')
@allowed([
  'centralus'
  'eastus2'
  'westus2'
  'westeurope'
  'eastasia'
])
param staticWebAppLocation string = 'eastus2'

@description('Object ID of the user/group/SP that should be granted Key Vault Secrets Officer role at deploy time. Find with: az ad signed-in-user show --query id -o tsv')
param deployingUserObjectId string

@description('Whether to claim the Cosmos DB free tier discount. Only one free-tier account allowed per subscription.')
param enableCosmosFreeTier bool = true

@description('Common tags applied to all resources for cost tracking.')
param tags object = {
  project: 'system-design-teacher'
  environment: 'prod'
  managedBy: 'bicep'
}

// -----------------------------------------------------------------------------
// Computed names — resource naming convention: <kind>-sdt-<prefix>
// -----------------------------------------------------------------------------

var cosmosAccountName = 'sdt-${namePrefix}-cosmos'
var keyVaultName = 'kv-sdt-${namePrefix}'
var insightsName = 'sdt-${namePrefix}-insights'
var logAnalyticsName = 'sdt-${namePrefix}-logs'
var containerAppEnvName = 'cae-sdt-${namePrefix}'
var containerAppName = 'ca-sdt-${namePrefix}'
var staticWebAppName = 'swa-sdt-${namePrefix}'

// -----------------------------------------------------------------------------
// Modules
// -----------------------------------------------------------------------------

module cosmos 'modules/cosmos.bicep' = {
  name: 'cosmos-deployment'
  params: {
    accountName: cosmosAccountName
    location: location
    enableFreeTier: enableCosmosFreeTier
    tags: tags
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault-deployment'
  params: {
    keyVaultName: keyVaultName
    location: location
    deployingUserObjectId: deployingUserObjectId
    tags: tags
  }
}

module insights 'modules/insights.bicep' = {
  name: 'insights-deployment'
  params: {
    insightsName: insightsName
    logAnalyticsName: logAnalyticsName
    location: location
    tags: tags
  }
}

module containerApps 'modules/containerapps.bicep' = {
  name: 'containerapps-deployment'
  params: {
    environmentName: containerAppEnvName
    appName: containerAppName
    location: location
    keyVaultName: keyVaultName
    appInsightsConnectionString: insights.outputs.connectionString
    tags: tags
  }
  dependsOn: [
    keyVault
    insights
  ]
}

module staticWebApp 'modules/staticwebapp.bicep' = {
  name: 'staticwebapp-deployment'
  params: {
    staticWebAppName: staticWebAppName
    location: staticWebAppLocation
    tags: tags
  }
}

// -----------------------------------------------------------------------------
// Grant the Container App's Managed Identity read access to Key Vault
// (deferred to a separate module so it runs after both KV and CA exist)
// -----------------------------------------------------------------------------

resource keyVaultRef 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
  dependsOn: [
    keyVault
  ]
}

@description('Built-in role: Key Vault Secrets User')
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource containerAppKvAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVaultRef
  name: guid(keyVaultName, containerAppName, keyVaultSecretsUserRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: containerApps.outputs.managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

@description('Cosmos DB connection string (placeholder — fetched at runtime by the app via Key Vault).')
output cosmosAccountName string = cosmos.outputs.accountName

@description('Cosmos DB primary connection string. Save to Key Vault as MONGO-URI.')
@secure()
output cosmosConnectionString string = cosmos.outputs.primaryConnectionString

@description('Key Vault URL — set as AZURE_KEYVAULT_URL env var on the Container App.')
output keyVaultUrl string = keyVault.outputs.vaultUri

@description('App Insights connection string — set as APPINSIGHTS_CONNECTION_STRING env var.')
output appInsightsConnectionString string = insights.outputs.connectionString

@description('Container App URL — frontend points VITE_API_BASE_URL here.')
output containerAppUrl string = containerApps.outputs.appUrl

@description('Container App Managed Identity principal ID.')
output containerAppPrincipalId string = containerApps.outputs.managedIdentityPrincipalId

@description('Static Web App URL — also used as a CORS origin for the backend.')
output staticWebAppUrl string = staticWebApp.outputs.defaultHostname

@description('Static Web App deployment token. Add to GitHub Actions secrets as AZURE_STATIC_WEB_APPS_API_TOKEN.')
@secure()
output staticWebAppApiToken string = staticWebApp.outputs.apiToken