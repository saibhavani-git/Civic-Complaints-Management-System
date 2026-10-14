# Deployment Guide

## Azure App Service Deployment

### Prerequisites
- Azure subscription
- Azure Container Registry (ACR)
- MongoDB Atlas cluster (production tier)
- Cloudinary production account
- Domain name (optional)

### 1. Azure Resource Setup

```bash
# Create resource group
az group create --name civic-complaints-rg --location centralindia

# Create ACR
az acr create --resource-group civic-complaints-rg \
  --name civiccomplaintsacr --sku Basic

# Create App Service Plan
az appservice plan create --name civic-complaints-plan \
  --resource-group civic-complaints-rg \
  --is-linux --sku B1

# Create Web App for backend
az webapp create --resource-group civic-complaints-rg \
  --plan civic-complaints-plan \
  --name civic-complaints-api \
  --deployment-container-image-name civiccomplaintsacr.azurecr.io/civic-complaints-api:latest
```

### 2. Environment Variables (Azure App Settings)

Set via Azure Portal → App Service → Configuration:

```
MONGODB_URI=mongodb+srv://...
JWT_SECRET_KEY=<generate-strong-secret>
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
GEMINI_API_KEY=...
CORS_ORIGINS=https://your-frontend-domain.com
```

### 3. GitHub Actions CI/CD

Secrets required in GitHub repository:
- `AZURE_CREDENTIALS` — Service principal JSON
- `AZURE_CONTAINER_REGISTRY` — ACR login server
- `ACR_USERNAME` / `ACR_PASSWORD`
- `AZURE_WEBAPP_NAME`

Push to `main` branch triggers automatic build and deploy.

### 4. MongoDB Atlas Production

- Enable IP whitelist for Azure App Service outbound IPs
- Create database user with readWrite role
- Enable backup (M10+ tier recommended)
- Create indexes as defined in DATABASE.md

### 5. Frontend Deployment (Vercel Alternative)

For Next.js frontend, deploy to Vercel or Azure Static Web Apps:

```bash
# Vercel
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard:
NEXT_PUBLIC_API_URL=https://civic-complaints-api.azurewebsites.net/api/v1
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=...
```

### 6. Docker Production Build

```bash
# Backend
docker build -t civic-complaints-api ./backend
docker run -p 8000:8000 --env-file .env civic-complaints-api

# Frontend
docker build -t civic-complaints-web \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com/api/v1 \
  ./frontend
```

### 7. Health Checks

- Backend: `GET /health` → `{ "status": "healthy", "db": "connected" }`
- Configure Azure App Service health check path: `/health`

### 8. Monitoring

- Azure Application Insights for backend telemetry
- MongoDB Atlas monitoring dashboard
- Cloudinary usage analytics
- Set up alerts for error rate > 5%, response time > 2s

### 9. SSL/TLS

- Azure App Service provides free SSL for `*.azurewebsites.net`
- Custom domain: upload certificate or use Azure-managed certificate

### 10. Scaling

```bash
# Scale App Service Plan
az appservice plan update --name civic-complaints-plan \
  --resource-group civic-complaints-rg --sku S1

# Enable autoscale
az monitor autoscale create --resource-group civic-complaints-rg \
  --resource civic-complaints-plan --resource-type Microsoft.Web/serverfarms \
  --name autoscale-plan --min-count 1 --max-count 3 --count 1
```
