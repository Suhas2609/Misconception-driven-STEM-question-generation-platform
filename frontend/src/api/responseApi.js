import { apiClient } from "./client.js";

export async function submitResponse(payload) {
  const { data } = await apiClient.post("/response/submit", payload);
  return data;
}
