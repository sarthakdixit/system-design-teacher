// =============================================================================
// Cosmos DB account (Mongo API) + database + collections
// =============================================================================

@description('Cosmos DB account name (3-44 chars, lowercase alphanumeric + hyphens).')
@minLength(3)
@maxLength(44)
param accountName string

@description('Region for the Cosmos account.')
param location string

@description('Whether to claim the free-tier discount (one allowed per subscription).')
param enableFreeTier bool

@description('Tags applied to all resources.')
param tags object

@description('Throughput shared at the database level. Free tier covers 1000 RU/s account-wide.')
param sharedThroughput int = 400

var databaseName = 'sdt'

resource account 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  tags: tags
  kind: 'MongoDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    enableFreeTier: enableFreeTier
    capabilities: [
      {
        name: 'EnableMongo'
      }
      {
        name: 'DisableRateLimitingResponses'
      }
    ]
    apiProperties: {
      serverVersion: '5.0'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capacity: {
      totalThroughputLimit: 1000
    }
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Local'
      }
    }
    networkAclBypass: 'AzureServices'
    publicNetworkAccess: 'Enabled'
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/mongodbDatabases@2024-05-15' = {
  parent: account
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    options: {
      throughput: sharedThroughput
    }
  }
}

// -----------------------------------------------------------------------------
// Collections
// -----------------------------------------------------------------------------
// Indexes are created at runtime by the app's ensure_indexes() startup hook,
// not here. We only declare the collections themselves and their shard keys.
// -----------------------------------------------------------------------------

var collections = [
  { name: 'users', shardKey: 'microsoft_oid' }
  { name: 'questions', shardKey: '_id' }
  { name: 'attempts', shardKey: 'user_id' }
  { name: 'feedback_cache', shardKey: 'key' }
  { name: 'rate_limit_counters', shardKey: 'key' }
]

resource collectionResources 'Microsoft.DocumentDB/databaseAccounts/mongodbDatabases/collections@2024-05-15' = [for c in collections: {
  parent: database
  name: c.name
  properties: {
    resource: {
      id: c.name
      shardKey: {
        '${c.shardKey}': 'Hash'
      }
      indexes: [
        {
          key: {
            keys: [
              '_id'
            ]
          }
        }
      ]
    }
  }
}]

// -----------------------------------------------------------------------------
// Outputs
// -----------------------------------------------------------------------------

output accountName string = account.name

@description('Primary Mongo connection string. Treat as a secret.')
@secure()
output primaryConnectionString string = account.listConnectionStrings().connectionStrings[0].connectionString