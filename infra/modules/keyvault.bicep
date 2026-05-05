// =============================================================================
// Azure Key Vault — secrets backend for production
// =============================================================================
// Created with RBAC mode (not vault access policies). The deploying user is
// granted Key Vault Secrets Officer role so they can populate secrets via the
// portal or CLI after this Bicep deploy completes.
//
// The Container App's Managed Identity is granted Key Vault Secrets User role
// in main.bicep (after both the Container App and Key Vault exist).

@description('Key Vault name (3-24 chars, alphanumeric + hyphens, must start with a letter, globally unique).')
@minLength(3)
@maxLength(24)
param keyVaultName string

@description('Region for the Key Vault.')
param location string

@description('Object ID of the user/group/SP granted Secrets Officer role.')
param deployingUserObjectId string

@description('Tags applied to all resources.')
param tags object

@description('Soft-delete retention days (7-90). Free tier supports the minimum.')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 7

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: null
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// -----------------------------------------------------------------------------
// Grant deploying user Key Vault Secrets Officer (read/write/delete secrets)
// -----------------------------------------------------------------------------

@description('Built-in role: Key Vault Secrets Officer')
var secretsOfficerRoleId = 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'

resource deployerSecretsOfficerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: keyVault
  name: guid(keyVaultName, deployingUserObjectId, secretsOfficerRoleId)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', secretsOfficerRoleId)
    principalId: deployingUserObjectId
    principalType: 'User'
  }
}

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

output vaultName string = keyVault.name
output vaultUri string = keyVault.properties.vaultUri
output vaultId string = keyVault.id