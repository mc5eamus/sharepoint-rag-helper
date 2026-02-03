param project string = 'sharepointrag'
param prefix string = 'mgr'
param salt string = '01'

param storageAccountName string = '${prefix}${project}${salt}'
param appInsightsName string = '${prefix}-${project}-${salt}'
param logAnalyticsName string = '${prefix}-${project}-${salt}'
param searchServiceName string = '${prefix}-${project}-${salt}'
param webPubSubServiceName string = '${prefix}-${project}-${salt}'
param containerRegistryName string = '${prefix}${project}${salt}'
param managedIdentityName string = '${prefix}-${project}-${salt}-identity'
param containerAppsEnvironmentName string = '${prefix}-${project}-${salt}-env'
param backendContainerAppName string = '${prefix}-${project}-backend-${salt}'
param frontendContainerAppName string = '${prefix}-${project}-frontend-${salt}'

@description('SKU name')
@allowed([
  'Standard_S1'
  'Free_F1'
])
param webPubSubSku string = 'Free_F1'

param location string = resourceGroup().location
var imagesContainerName = 'sharepoint-images'
var fileContentIndexName = 'sharepoint-files'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
  }
  
  resource blobServices 'blobServices' = {
    name: 'default'
    resource inventory 'containers' = {
      name: imagesContainerName
    }
  }
}

resource appInsights 'microsoft.insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Flow_Type: 'Redfield'
    Request_Source: 'IbizaAIExtension'
    RetentionInDays: 30
    WorkspaceResourceId: logAnalytics.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2021-12-01-preview' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'pergb2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: { 
      dailyQuotaGb: -1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}


resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    semanticSearch: 'disabled'
  }
}

resource webPubSubService 'Microsoft.SignalRService/webPubSub@2023-02-01' = {
  name: webPubSubServiceName
  location: location
  sku: {
    capacity: 1
    name: webPubSubSku
  }
  identity: {
    type: 'None'
  }
  properties: {
    disableAadAuth: false
    disableLocalAuth: false
    liveTraceConfiguration: {
      categories: [
        {
          enabled: 'false'
          name: 'ConnectivityLogs'
        }
        {
          enabled: 'false'
          name: 'MessagingLogs'
        }
      ]
      enabled: 'false'
    }
    networkACLs: {
      defaultAction: 'Deny'     
      publicNetwork: {
        allow: [
          'ServerConnection'
          'ClientConnection'
          'RESTAPI'
          'Trace'
        ]
      }
    }
    publicNetworkAccess: 'Enabled'
    resourceLogConfiguration: {
      categories: [
        {
          enabled: 'true'
          name: 'ConnectivityLogs'
        }
        {
          enabled: 'true'
          name: 'MessagingLogs'
        }
      ]
    }
    tls: {
      clientCertEnabled: false
    }
  }
}

var storagePrimaryKey = storageAccount.listKeys().keys[0].value
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};AccountKey=${storagePrimaryKey};EndpointSuffix=${environment().suffixes.storage}'

var searchAdminKey = searchService.listAdminKeys().primaryKey

var pubSubConnectionString = webPubSubService.listKeys().primaryConnectionString

//var searchQueryKey = searchService.listQueryKeys().value[0].key

// User Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

// Grant ACR Pull permission to managed identity
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, managedIdentity.id, 'acrpull')
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull role
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Container Apps Environment
resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerAppsEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Backend Container App
resource backendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: backendContainerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8085
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'indexer-apikey'
          value: searchAdminKey
        }
        {
          name: 'indexer-manage-key'
          value: searchAdminKey
        }
        {
          name: 'webpubsub-connection-string'
          value: pubSubConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${containerRegistry.properties.loginServer}/sharepoint-rag-backend:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'OPENAI_ENDPOINT'
              value: '[REQUIRED: Endpoint URL for Azure OpenAI service]'
            }
            {
              name: 'OPENAI_APIKEY'
              value: '[REQUIRED: API key for Azure OpenAI service]'
            }
            {
              name: 'OPENAI_EMBEDDINGS_MODEL'
              value: '[REQUIRED: Model name for text embedding in Azure OpenAI]'
            }
            {
              name: 'OPENAI_COMPLETIONS_MODEL_VISUAL'
              value: '[REQUIRED: Model name for multimodal completions in OpenAI]'
            }
            {
              name: 'OPENAI_COMPLETIONS_MODEL_TEXT'
              value: '[REQUIRED: Model name for text completions in OpenAI]'
            }
            {
              name: 'CLIENT_ID'
              value: '[REQUIRED: ID of the backend API app registration]'
            }
            {
              name: 'CLIENT_SECRET'
              value: '[REQUIRED: Client secret for backend API app registration]'
            }
            {
              name: 'TENANT_ID'
              value: '[REQUIRED: Azure AD Tenant ID]'
            }
            {
              name: 'BLOB_CONNECTION_STRING'
              value: storageConnectionString
            }
            {
              name: 'BLOB_CONTAINER_NAME'
              value: imagesContainerName
            }
            {
              name: 'INDEXER_ENDPOINT'
              value: 'https://${searchServiceName}.search.windows.net'
            }
            {
              name: 'INDEXER_APIKEY'
              secretRef: 'indexer-apikey'
            }
            {
              name: 'INDEXER_INDEX'
              value: fileContentIndexName
            }
            {
              name: 'INDEXER_MANAGE_KEY'
              secretRef: 'indexer-manage-key'
            }
            {
              name: 'WEBPUBSUB_CONNECTION_STRING'
              secretRef: 'webpubsub-connection-string'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appInsights.properties.ConnectionString
            }
            {
              name: 'DEBUG'
              value: 'False'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

// Frontend Container App
resource frontendContainerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: frontendContainerAppName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: '${containerRegistry.properties.loginServer}/sharepoint-rag-frontend:latest'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output deployEnvironment string = join([
    'OPENAI_ENDPOINT=[Endpoint URL for  Azure OpenAI service]'
    'OPENAI_APIKEY=[API key for Azure OpenAI service]'
    'OPENAI_EMBEDDINGS_MODEL=[Model name for text embedding in Azure OpenAI - must be ada or compatible]'
    'OPENAI_COMPLETIONS_MODEL_VISUAL=[Model name for multimodal completions in OpenAI]'
    'OPENAI_COMPLETIONS_MODEL_TEXT=[Model name for text completions in OpenAI]'
    'CLIENT_ID=[ID of the client app]'
    'CLIENT_SECRET=[Client secret]'
    'TENANT_ID=[Tenant ID]'  
    'BLOB_CONNECTION_STRING=${storageConnectionString}'
    'BLOB_CONTAINER_NAME=${imagesContainerName}'
    'INDEXER_ENDPOINT=https://${searchServiceName}.search.windows.net'
    'INDEXER_APIKEY=${searchAdminKey}'
    'INDEXER_INDEX=${fileContentIndexName}'
    'INDEXER_MANAGE_KEY=${searchAdminKey}'
    'WEBPUBSUB_CONNECTION_STRING=${pubSubConnectionString}'
    'APPLICATIONINSIGHTS_CONNECTION_STRING=${appInsights.properties.ConnectionString}'
    'DEBUG=False'
  ], '\n')

output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerRegistryName string = containerRegistry.name
output managedIdentityClientId string = managedIdentity.properties.clientId
output backendUrl string = 'https://${backendContainerApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendContainerApp.properties.configuration.ingress.fqdn}'
