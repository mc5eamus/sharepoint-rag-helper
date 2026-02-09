import { Configuration, PopupRequest } from "@azure/msal-browser";

// Helper function to get environment variable with fallback
const getEnvVar = (name: string, fallback: string = ''): string => {
    return import.meta.env[name] || fallback;
};

// Config object to be passed to Msal on creation
export const msalConfig: Configuration = {
    auth: {
        clientId: getEnvVar('VITE_MSAL_CLIENT_ID'),
        authority: getEnvVar('VITE_MSAL_AUTHORITY'),
        redirectUri: getEnvVar('VITE_MSAL_REDIRECT_URI', '/'),
        postLogoutRedirectUri: getEnvVar('VITE_MSAL_POST_LOGOUT_REDIRECT_URI', '/')
    },
    system: {
        allowPlatformBroker: false // Disables WAM Broker
    }
};

export const apiConfig = { 
    baseUri: getEnvVar('VITE_API_BASE_URI', 
        import.meta.env.MODE === 'development' ? "http://localhost:8085" : "/api"
    ),
};

// Add here scopes for id token to be used at MS Identity Platform endpoints.
export const loginRequest: PopupRequest = {
    scopes: ["User.Read"]
};

export const apiRequest: PopupRequest = {
    scopes: [getEnvVar('VITE_API_SCOPE')]
};