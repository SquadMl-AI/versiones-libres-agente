const runtimeEnv = typeof window !== "undefined" ? window.__ENV__ || {} : {};

function getEnv(key) {
  return runtimeEnv[key] ?? import.meta.env[key];
}

export const ENV = {
  VITE_CLIENT_ID: getEnv("VITE_CLIENT_ID"),
  VITE_TENANT_ID: getEnv("VITE_TENANT_ID"),
  VITE_REDIRECT_URI: getEnv("VITE_REDIRECT_URI"),
  VITE_BACKEND_URL_V1: getEnv("VITE_BACKEND_URL_V1"),
  VITE_URL_BLOB: getEnv("VITE_URL_BLOB"),
  VITE_BLOB_TOKEN: getEnv("VITE_BLOB_TOKEN"),
};
