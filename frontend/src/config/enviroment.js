const env = {
  BACKEND_PORT: import.meta.env.VITE_BACKEND_PORT,
  BACKEND_HOST: import.meta.env.VITE_BACKEND_HOST,
  CLIENT_ID: import.meta.env.VITE_CLIENT_ID,
  TENANT_ID: import.meta.env.VITE_TENANT_ID,
  REDIRECT_URI: import.meta.env.VITE_REDIRECT_URI,
  BACKEND_URL_V1: import.meta.env.VITE_BACKEND_URL_V1,
  URL_BLOB: import.meta.env.VITE_URL_BLOB,
  BLOB_TOKEN: import.meta.env.VITE_BLOB_TOKEN,
};

export default env;
