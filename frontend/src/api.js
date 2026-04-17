import { ENV } from "./config/env";

export const BACKEND_URL_V1 = ENV.VITE_BACKEND_URL_V1;


export async function fetchData({
  url,
  method = "GET",
  body = null,
  headers = {},
  params = null,
}) {
  let finalUrl = BACKEND_URL_V1 + url;

  if (params && typeof params === "object") {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((val) => queryParams.append(key, val));
      } else {
        queryParams.append(key, value);
      }
    });
    finalUrl += `?${queryParams.toString()}`;
  }

  const config = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  if (["POST", "PUT", "PATCH"].includes(method.toUpperCase()) && body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(finalUrl, config);
    if (!response.ok) {
      throw new Error(`Error: ${response.status} - ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}
