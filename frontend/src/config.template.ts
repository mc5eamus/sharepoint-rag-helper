import { Configuration, PopupRequest } from "@azure/msal-browser";

// Config object to be passed to Msal on creation
export const msalConfig: Configuration = {
    auth: {
        clientId: '[client ID of the frontend app registration]',
        authority: 'https://login.microsoftonline.com/[your tenant id]',
        redirectUri: "/",
        postLogoutRedirectUri: "/"
    },
    system: {
        allowNativeBroker: false // Disables WAM Broker
    }
};

export const apiConfig = { 
    baseUri: "[Base url of the API, e.g. https://localhost:3000/api]", 
};

// Add here scopes for id token to be used at MS Identity Platform endpoints.
export const loginRequest: PopupRequest = {
    scopes: ["api://[api-application-id-uri]/.default"]
};