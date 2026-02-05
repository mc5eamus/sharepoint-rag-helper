# Frontend Environment Configuration

## Environment Variables

The frontend application uses environment variables for configuration. All variables must be prefixed with `VITE_` to be accessible in the browser.

### Setup

1. Copy the template file:
   ```bash
   cp .env.template .env.local
   ```

2. Update the values in `.env.local` with your specific configuration.

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_MSAL_CLIENT_ID` | Azure AD Application Client ID | Required |
| `VITE_MSAL_AUTHORITY` | Azure AD Authority URL | Required |
| `VITE_MSAL_REDIRECT_URI` | Redirect URI after login | `/` |
| `VITE_MSAL_POST_LOGOUT_REDIRECT_URI` | Redirect URI after logout | `/` |
| `VITE_API_BASE_URI` | Backend API base URL | `http://localhost:8085` (dev), `/api` (prod) |
| `VITE_API_SCOPE` | API scope for authentication | `api://python-graph-api/.default` |

### Environment Files

- `.env.template` - Template with placeholder values
- `.env.local` - Local development (not committed)
- `.env.production` - Production defaults

### Notes

- `.env.local` is ignored by git and should contain your actual values
- Environment variables are embedded at build time
- Changes to environment variables require a restart of the development server