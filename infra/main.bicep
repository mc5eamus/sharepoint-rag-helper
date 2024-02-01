param project string = 'sharepointrag'
param prefix string = 'mgr'
param salt string = '01'

param storageAccountName string = '${prefix}${project}${salt}'
param appInsightsName string = '${prefix}-${project}-${salt}'
param logAnalyticsName string = '${prefix}-${project}-${salt}'
param searchServiceName string = '${prefix}-${project}-${salt}'
param webPubSubServiceName string = '${prefix}-${project}-${salt}'
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
