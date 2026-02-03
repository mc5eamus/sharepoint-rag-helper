# Azure Container Apps Deployment Guide

This guide explains how to deploy the SharePoint RAG Helper application to Azure Container Apps using either the Azure CLI or Azure Developer CLI (azd).

## Prerequisites

- Azure subscription
- Azure CLI (`az`) installed and configured
- (Optional) Azure Developer CLI (`azd`) installed for simplified deployment
- Docker installed for building container images
- Appropriate Azure permissions to create resources

## Architecture

The deployment creates the following Azure resources:

1. **User Managed Identity** - For secure access between services
2. **Azure Container Registry (ACR)** - To store container images
3. **Azure Container Apps Environment** - Hosting environment for containers
4. **Backend Container App** - Python FastAPI application
5. **Frontend Container App** - React application
6. **Storage Account** - For PDF page snapshots
7. **Azure AI Search** - For document indexing and search
8. **Azure Web PubSub** - For real-time communication
9. **Application Insights** - For monitoring and logging
10. **Log Analytics Workspace** - For centralized logging

## Deployment Methods

### Method 1: Using Azure Developer CLI (azd) - Recommended

The simplest way to deploy is using Azure Developer CLI, which automates the entire deployment process.

#### Steps:

1. **Initialize azd (first time only)**:
   ```bash
   azd init
   ```
   When prompted, select the current directory.

2. **Login to Azure**:
   ```bash
   azd auth login
   ```

3. **Provision infrastructure**:
   ```bash
   azd provision
   ```
   This will:
   - Create all required Azure resources
   - Set up the container registry
   - Configure the managed identity and permissions

4. **Deploy the applications**:
   ```bash
   azd deploy
   ```
   This will:
   - Build Docker images for backend and frontend
   - Push images to Azure Container Registry
   - Deploy containers to Azure Container Apps

5. **Get service endpoints**:
   ```bash
   azd show
   ```

#### All-in-one command:
```bash
azd up
```
This combines provision and deploy into a single command.

### Method 2: Using Azure CLI

If you prefer more control or don't want to use azd, you can deploy using Azure CLI.

#### Steps:

1. **Create a resource group**:
   ```bash
   RESOURCE_GROUP="rg-sharepoint-rag"
   LOCATION="eastus"
   az group create --name $RESOURCE_GROUP --location $LOCATION
   ```

2. **Deploy the infrastructure**:
   ```bash
   az deployment group create \
     --resource-group $RESOURCE_GROUP \
     --template-file infra/main.bicep \
     --parameters project=sharepointrag prefix=mgr salt=01
   ```

3. **Save the deployment outputs**:
   ```bash
   az deployment group show \
     --resource-group $RESOURCE_GROUP \
     --name main \
     --query properties.outputs
   ```

4. **Login to Azure Container Registry**:
   ```bash
   ACR_NAME=$(az deployment group show -g $RESOURCE_GROUP -n main --query properties.outputs.containerRegistryName.value -o tsv)
   az acr login --name $ACR_NAME
   ```

5. **Build and push backend image**:
   ```bash
   cd backend
   docker build -t $ACR_NAME.azurecr.io/sharepoint-rag-backend:latest .
   docker push $ACR_NAME.azurecr.io/sharepoint-rag-backend:latest
   cd ..
   ```

6. **Build and push frontend image**:
   ```bash
   cd frontend
   docker build -t $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest .
   docker push $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest
   cd ..
   ```

7. **Update Container Apps with new images** (triggers deployment):
   ```bash
   # Backend
   az containerapp update \
     --name mgr-sharepointrag-backend-01 \
     --resource-group $RESOURCE_GROUP \
     --image $ACR_NAME.azurecr.io/sharepoint-rag-backend:latest

   # Frontend
   az containerapp update \
     --name mgr-sharepointrag-frontend-01 \
     --resource-group $RESOURCE_GROUP \
     --image $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest
   ```

## Post-Deployment Configuration

### 1. Configure Azure OpenAI

The Bicep template does not create Azure OpenAI resources. You need to:

1. Create an Azure OpenAI service (or use an existing one)
2. Deploy the required models:
   - Text embedding model (e.g., text-embedding-ada-002)
   - Text completion model (e.g., gpt-4)
   - Visual completion model (e.g., gpt-4-vision)

### 2. Create App Registrations

Create two app registrations in Azure AD:

#### Frontend App (SPA):
- Type: Single Page Application
- Redirect URI: Your frontend URL (e.g., `https://[frontend-app-name].azurecontainerapps.io`)
- Note the Client ID and Tenant ID

#### Backend App (API):
- Type: Web API
- Permissions: Delegated Graph permission `Sites.Read.All`
- Create a client secret
- Set Application ID URI (e.g., `api://sharepoint-rag-api`)
- Expose API with a scope (e.g., `access_as_user`)
- Add frontend app as authorized client

### 3. Update Backend Environment Variables

Update the backend container app with the required environment variables:

```bash
az containerapp update \
  --name mgr-sharepointrag-backend-01 \
  --resource-group $RESOURCE_GROUP \
  --set-env-vars \
    "OPENAI_ENDPOINT=https://[your-openai-service].openai.azure.com/" \
    "OPENAI_APIKEY=[your-api-key]" \
    "OPENAI_EMBEDDINGS_MODEL=[embedding-model-name]" \
    "OPENAI_COMPLETIONS_MODEL_VISUAL=[vision-model-name]" \
    "OPENAI_COMPLETIONS_MODEL_TEXT=[text-model-name]" \
    "CLIENT_ID=[backend-app-client-id]" \
    "CLIENT_SECRET=[backend-app-secret]" \
    "TENANT_ID=[your-tenant-id]"
```

### 4. Update Frontend Configuration

The frontend needs to be rebuilt with the correct configuration. Update `frontend/src/config.ts` with:

- Frontend app Client ID
- Tenant ID
- Backend API URL
- Backend API scope

Then rebuild and redeploy the frontend container:

```bash
cd frontend
docker build -t $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest .
docker push $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest
az containerapp update \
  --name mgr-sharepointrag-frontend-01 \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/sharepoint-rag-frontend:latest
```

## Monitoring and Troubleshooting

### View Container App Logs

```bash
# Backend logs
az containerapp logs show \
  --name mgr-sharepointrag-backend-01 \
  --resource-group $RESOURCE_GROUP \
  --follow

# Frontend logs
az containerapp logs show \
  --name mgr-sharepointrag-frontend-01 \
  --resource-group $RESOURCE_GROUP \
  --follow
```

### View Application Insights

1. Navigate to the Application Insights resource in Azure Portal
2. Go to "Logs" or "Transaction search" to view application telemetry

### Common Issues

1. **Container fails to start**: Check environment variables are set correctly
2. **Cannot pull image**: Verify managed identity has AcrPull role on the registry
3. **502 Bad Gateway**: Backend may not be ready, check backend logs

## Updating the Application

### Using azd:
```bash
azd deploy
```

### Using Azure CLI:
Rebuild and push images, then update the container apps (see steps 5-7 in Method 2).

## Cleanup

### Using azd:
```bash
azd down
```

### Using Azure CLI:
```bash
az group delete --name $RESOURCE_GROUP --yes
```

## Cost Optimization

- Container Apps scale to zero when idle (set minReplicas to 0)
- Use Free tier for Web PubSub during development
- Use Basic tier for Azure AI Search during development
- Consider using Azure Container Registry Basic tier for lower environments

## Security Considerations

- Managed identity is used for ACR access (no credentials in code)
- Secrets are stored in Container Apps configuration (encrypted at rest)
- HTTPS is enforced for all ingress
- Consider adding authentication middleware to Container Apps
- Regularly rotate client secrets and API keys
