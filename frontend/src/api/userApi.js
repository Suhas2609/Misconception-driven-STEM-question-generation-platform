import { apiClient } from "./client.js";

export async function registerUser(payload) {
  const { data } = await apiClient.post("/user/register", payload);
  return data;
}

export async function getUserTraits(userId) {
  const { data } = await apiClient.get(`/user/${encodeURIComponent(userId)}/traits`);
  return data;
}
