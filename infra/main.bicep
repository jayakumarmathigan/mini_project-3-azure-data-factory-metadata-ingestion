// Creates ADLS Gen2, a Data Factory and the role that lets the factory use the storage.
// Deploying the role assignment needs Owner or User Access Administrator rights
// (or another role that may create role assignments).
param location string = resourceGroup().location

var suffix = uniqueString(resourceGroup().id)
var storageName = 'stadf${suffix}'
var factoryName = 'adf-ingest-${suffix}'
var blobContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [for name in ['source', 'bronze', 'config']: {
  parent: blobService
  name: name
}]

resource factory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: factoryName
  location: location
  identity: { type: 'SystemAssigned' }
}

resource factoryStorageAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, factory.id, blobContributor)
  properties: {
    roleDefinitionId: blobContributor
    principalId: factory.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output storageAccountName string = storage.name
output dataFactoryName string = factory.name
