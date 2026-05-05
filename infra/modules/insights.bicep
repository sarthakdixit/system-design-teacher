// =============================================================================
// Application Insights (workspace-based) + Log Analytics workspace
// =============================================================================
// Workspace-based App Insights is the modern path. Classic mode (without a
// backing Log Analytics workspace) is deprecated and won't work for new
// deployments after 2026.

@description('Application Insights resource name.')
param insightsName string

@description('Log Analytics workspace name (the workspace that backs App Insights).')
param logAnalyticsName string

@description('Region for both resources.')
param location string

@description('Tags applied to all resources.')
param tags object

@description('Daily ingestion cap in GB. Free tier covers 5 GB/month per workspace.')
param dailyQuotaGb int = 1

@description('Data retention in days (free tier: 30 days).')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    workspaceCapping: {
      dailyQuotaGb: dailyQuotaGb
    }
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: insightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    IngestionMode: 'LogAnalytics'
    DisableLocalAuth: false
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

output insightsName string = appInsights.name
output insightsId string = appInsights.id

@description('App Insights connection string. Used by APPINSIGHTS_CONNECTION_STRING env var.')
output connectionString string = appInsights.properties.ConnectionString

@description('Log Analytics workspace ID. Container Apps Environment ties to this for log ingestion.')
output workspaceId string = workspace.id

@description('Log Analytics workspace customer ID (for connecting other resources).')
output workspaceCustomerId string = workspace.properties.customerId