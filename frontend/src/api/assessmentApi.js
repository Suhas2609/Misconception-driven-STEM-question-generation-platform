import { apiClient } from "./client";

/**
 * Get assessment questions for onboarding
 * @returns {Promise<Array<object>>}
 */
export async function getAssessmentQuestions() {
  const response = await apiClient.get("/assessment/questions");
  return response.data;
}

/**
 * Submit assessment responses
 * @param {string} token - JWT access token
 * @param {{ responses: Array<{ question_id: string, answer_text: string, confidence?: number }> }} submission
 * @returns {Promise<object>} Updated user object
 */
export async function submitAssessment(token, submission) {
  const response = await apiClient.post("/assessment/submit", submission, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}
