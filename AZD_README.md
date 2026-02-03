# Azure Developer CLI (azd) Support

This project supports deployment using the Azure Developer CLI (azd), which simplifies the process of deploying to Azure.

## Quick Start

### Prerequisites

1. Install [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
2. Install [Docker](https://docs.docker.com/get-docker/)
3. Have an Azure subscription

### Deploy in 3 Commands

```bash
# 1. Login to Azure
azd auth login

# 2. Provision infrastructure and deploy apps
azd up

# 3. Open the frontend in your browser
azd show
```

That's it! The `azd up` command will:
- Create all Azure resources (Container Apps, Container Registry, Storage, AI Search, etc.)
- Build Docker images for frontend and backend
- Push images to Azure Container Registry
- Deploy containers to Azure Container Apps

## Post-Deployment Configuration

After the initial deployment, you need to configure a few additional settings:

### 1. Azure OpenAI Setup

The deployment doesn't include Azure OpenAI. You need to:

1. Create an Azure OpenAI service (or use existing)
2. Deploy required models
3. Update backend environment variables:

```bash
azd env set OPENAI_ENDPOINT "https://your-openai.openai.azure.com/"
azd env set OPENAI_APIKEY "your-api-key"
azd env set OPENAI_EMBEDDINGS_MODEL "text-embedding-ada-002"
azd env set OPENAI_COMPLETIONS_MODEL_TEXT "gpt-4"
azd env set OPENAI_COMPLETIONS_MODEL_VISUAL "gpt-4-vision"
```

### 2. Azure AD App Registrations

Create two app registrations:

**Frontend (SPA):**
- Redirect URI: Your frontend URL from `azd show`

**Backend (API):**
- Graph permission: Sites.Read.All
- Create client secret
- Expose API with scope

Update environment variables:

```bash
azd env set CLIENT_ID "backend-app-client-id"
azd env set CLIENT_SECRET "backend-app-secret"
azd env set TENANT_ID "your-tenant-id"
```

### 3. Redeploy with Configuration

```bash
azd deploy
```

## Useful Commands

```bash
# Show service endpoints
azd show

# View environment variables
azd env get-values

# View logs (requires Azure CLI)
azd monitor --logs

# Update infrastructure only
azd provision

# Deploy code changes only
azd deploy

# Clean up all resources
azd down
```

## Environment Variables

azd automatically sets these environment variables:

- `AZURE_RESOURCE_GROUP` - Resource group name
- `AZURE_CONTAINER_REGISTRY_NAME` - Container registry name
- `AZURE_CONTAINER_REGISTRY_ENDPOINT` - Container registry endpoint

## Customization

### Change Resource Names

Edit parameters in `infra/main.bicep`:
- `project` - Project name (default: sharepointrag)
- `prefix` - Prefix for resources (default: mgr)
- `salt` - Unique suffix (default: 01)

### Change Region

```bash
azd env set AZURE_LOCATION "eastus"
azd provision
```

## Troubleshooting

### Container App Won't Start

Check if required environment variables are set:
```bash
azd env get-values
```

### Can't Access Frontend

Ensure app registrations are configured with correct redirect URIs.

### Build Fails

Make sure Docker is running and you're logged into Azure:
```bash
docker ps
azd auth login
```

## Cost Estimation

The deployed resources include:
- Azure Container Apps (Consumption plan)
- Azure Container Registry (Basic tier)
- Azure Storage (Standard LRS)
- Azure AI Search (Basic tier)
- Azure Web PubSub (Free or Standard tier)
- Application Insights
- Log Analytics Workspace

Estimated cost: ~$50-100/month depending on usage.

## More Information

- [Azure Developer CLI Documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Detailed Deployment Guide](DEPLOYMENT.md)
