import { PublicClientApplication } from "@azure/msal-browser";
import { ENV } from "./env";

export const msalConfig = {
  auth: {
    clientId: ENV.VITE_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${ENV.VITE_TENANT_ID}`,
    redirectUri: ENV.VITE_REDIRECT_URI,
    postLogoutRedirectUri: "/",
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: "sessionStorage", // This configures where your cache will be stored
    storeAuthStateInCookie: false, // Set this to true if you are having issues on IE11 or Edge
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: ["user.read"],
};
