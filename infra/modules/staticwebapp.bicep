// =============================================================================
// Azure Static Web App — frontend hosting
// =============================================================================
// Free tier: 100 GB bandwidth/month, 250 MB storage, custom domains supported.
//
// This module creates the resource shell. The actual build pipeline (linking
// the GitHub repo, configuring build commands) is wired up post-Bicep via:
//   - Portal: Step "Configure deployment" in the SWA portal page, OR
//   - CLI:    az staticwebapp connect-to-github
//
// Bicep can't easily encode the GitHub OAuth flow, so this is the cleanest split.

@description('Static Web App name (3-60 chars, alphanumeric + hyphens).')
@minLength(3)
@maxLength(60)
param staticWebAppName string

@description('Region. Static Web Apps has a smaller pool than other services.')
@allowed([
  'centralus'
  'eastus2'
  'westus2'
  'westeurope'
  'eastasia'
])
param location string

@description('Tags applied to the resource.')
param tags object

resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: staticWebAppName
  location: location
  tags: tags
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    allowConfigFileUpdates: true
    enterpriseGradeCdnStatus: 'Disabled'
    publicNetworkAccess: 'Enabled'
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

output staticWebAppName string = staticWebApp.name

@description('Default hostname (auto-assigned). Format: <name>.<region>.azurestaticapps.net')
output defaultHostname string = 'https://${staticWebApp.properties.defaultHostname}'

@description('Deployment API token. Add to GitHub Actions secrets as AZURE_STATIC_WEB_APPS_API_TOKEN.')
@secure()
output apiToken string = staticWebApp.listSecrets().properties.apiKey