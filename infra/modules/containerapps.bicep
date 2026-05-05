// =============================================================================
// Azure Container Apps — runtime for the FastAPI backend
// =============================================================================
// Provisions:
//   - Container Apps Environment (the underlying Kubernetes-ish runtime)
//   - Container App with system-assigned Managed Identity
//   - Scale-to-zero (min replicas = 0) for $0 idle cost
//   - All non-secret env vars baked in
//
// What this module does NOT do:
//   - Deploy a real container image (uses a Microsoft placeholder; CI/CD
//     pushes the real image and updates the app via `az containerapp update`)
//   - Grant Key Vault access (done in main.bicep after both resources exist)
//   - Set CORS_ALLOWED_ORIGINS to the Static Web App URL (chicken-and-egg;
//     done as a post-deploy CLI step)

@description('Container Apps Environment name.')
param environmentName string

@description('Container App name.')
param appName string

@description('Region.')
param location string

@description('Key Vault name (for AZURE_KEYVAULT_URL env var construction).')
param keyVaultName string

@description('App Insights connection string (set as APPINSIGHTS_CONNECTION_STRING env var).')
@secure()
param appInsightsConnectionString string

@description('Tags applied to all resources.')
param tags object

@description('Initial container image. Replaced by CI/CD after first deploy.')
param initialImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Container CPU allocation. 0.25 = smallest; fits free tier.')
param cpuCores string = '0.25'

@description('Container memory allocation. Must scale with CPU per Azure rules.')
param memorySize string = '0.5Gi'

@description('Minimum replica count. 0 = scale-to-zero (free tier friendly).')
@minValue(0)
@maxValue(25)
param minReplicas int = 0

@description('Maximum replica count.')
@minValue(1)
@maxValue(25)
param maxReplicas int = 2

@description('Daily situation question rate limit per user.')
param rateLimitSituationDaily int = 5

@description('Daily design submission rate limit per user.')
param rateLimitDesignDaily int = 2

@description('Daily situation question generation cap (global).')
param globalCapSituationDaily int = 50

@description('Daily design submission cap (global).')
param globalCapDesignDaily int = 100

@description('Feedback cache TTL in days.')
@minValue(1)
@maxValue(365)
param feedbackCacheTtlDays int = 30

// -----------------------------------------------------------------------------
// Computed values
// -----------------------------------------------------------------------------

var keyVaultUrl = 'https://${keyVaultName}.vault.azure.net/'

// Initial CORS placeholder. Real Static Web App URL is patched in post-deploy.
var corsPlaceholder = '["http://localhost:5173"]'

// -----------------------------------------------------------------------------
// Container Apps Environment
// -----------------------------------------------------------------------------

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    zoneRedundant: false
  }
}

// -----------------------------------------------------------------------------
// Container App
// -----------------------------------------------------------------------------

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        corsPolicy: {
          allowedOrigins: [
            'http://localhost:5173'
          ]
          allowedHeaders: [
            'Authorization'
            'Content-Type'
          ]
          allowedMethods: [
            'GET'
            'POST'
            'PUT'
            'DELETE'
            'OPTIONS'
          ]
          allowCredentials: true
        }
      }
    }
    template: {
      containers: [
        {
          name: 'sdt-backend'
          image: initialImage
          resources: {
            cpu: json(cpuCores)
            memory: memorySize
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 30
              periodSeconds: 30
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 10
              failureThreshold: 3
            }
          ]
          env: [
            { name: 'ENVIRONMENT', value: 'azure' }
            { name: 'AZURE_KEYVAULT_URL', value: keyVaultUrl }
            { name: 'APPINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'MONGO_DB_NAME', value: 'sdt' }
            { name: 'LLM_PROVIDER', value: 'openai' }
            { name: 'JWT_ALGORITHM', value: 'HS256' }
            { name: 'JWT_EXPIRY_HOURS', value: '24' }
            { name: 'RATE_LIMIT_SITUATION_DAILY', value: string(rateLimitSituationDaily) }
            { name: 'RATE_LIMIT_DESIGN_DAILY', value: string(rateLimitDesignDaily) }
            { name: 'GLOBAL_CAP_SITUATION_DAILY', value: string(globalCapSituationDaily) }
            { name: 'GLOBAL_CAP_DESIGN_DAILY', value: string(globalCapDesignDaily) }
            { name: 'FEEDBACK_CACHE_TTL_DAYS', value: string(feedbackCacheTtlDays) }
            { name: 'CORS_ALLOWED_ORIGINS', value: corsPlaceholder }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scaler'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

output appName string = containerApp.name
output environmentName string = environment.name

@description('Public HTTPS URL for the Container App.')
output appUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'

@description('Managed Identity principal ID. Used in main.bicep to grant Key Vault access.')
output managedIdentityPrincipalId string = containerApp.identity.principalId