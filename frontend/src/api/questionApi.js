import { apiClient } from "./client.js";

export async function generateQuestion(payload) {
  const { data } = await apiClient.post("/question/generate", payload);
  return data;
}
