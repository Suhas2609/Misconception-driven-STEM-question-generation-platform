import { apiClient } from "./client";

/**
 * Register a new user
 * @param {{ name: string, email: string, password: string }} data
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 */
export async function registerUser(data) {
  const response = await apiClient.post("/auth/register", data);
  return response.data;
}

/**
 * Login existing user
 * @param {{ username: string, password: string }} credentials - username is email
 * @returns {Promise<{ access_token: string, token_type: string, user: object }>}
 */
export async function loginUser(credentials) {
  // OAuth2PasswordRequestForm expects form data
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const response = await apiClient.post("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
}

/**
 * Get current authenticated user
 * @param {string} token - JWT access token
 * @returns {Promise<object>}
 */
export async function getCurrentUser(token) {
  const response = await apiClient.get("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}
