import { apiClient } from "./client.js";

// Legacy PDF upload (old API)
export async function uploadPdf(file, { userId, topic, num_questions } = {}) {
  const formData = new FormData();
  formData.append("file", file);

  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  if (topic) params.set("topic", topic);
  if (num_questions) params.set("num_questions", String(num_questions));

  // Let axios set multipart boundary header automatically
  const url = `/pdf/upload${params.toString() ? `?${params.toString()}` : ""}`;
  const { data } = await apiClient.post(url, formData);

  return data;
}

// ===== NEW API with GPT-4o Topic Extraction =====

/**
 * Upload a PDF file and extract topics using GPT-4o
 * @param {FormData} formData - FormData containing the PDF file
 * @returns {Promise} Response with session_id, topics, and document summary
 */
export async function uploadPDF(formData) {
  const token = localStorage.getItem("access_token"); // Fixed: use correct key
  
  if (!token) {
    throw new Error("No authentication token found. Please log in again.");
  }
  
  console.log("📤 Uploading PDF with token:", token.substring(0, 20) + "...");
  
  // Don't set Content-Type - let axios set it automatically with boundary
  const { data } = await apiClient.post("/pdf-v2/upload", formData, {
    headers: {
      "Authorization": `Bearer ${token}`,
    },
  });
  return data;
}

/**
 * Get all learning sessions for the current user
 * @returns {Promise} List of sessions
 */
export async function getUserSessions() {
  const { data } = await apiClient.get("/pdf-v2/sessions");
  return data.sessions;
}

/**
 * Get details of a specific learning session
 * @param {string} sessionId - The session ID
 * @returns {Promise} Session details
 */
export async function getSessionDetails(sessionId) {
  const { data } = await apiClient.get(`/pdf-v2/sessions/${sessionId}`);
  return data;
}

/**
 * Update session with selected topics for quiz generation
 * @param {string} sessionId - The session ID
 * @param {string[]} selectedTopics - Array of topic titles to practice
 * @returns {Promise} Updated session
 */
export async function selectTopicsForPractice(sessionId, selectedTopics) {
  const { data } = await apiClient.patch(
    `/pdf-v2/sessions/${sessionId}/select-topics`,
    selectedTopics
  );
  return data;
}

/**
 * Generate personalized questions from selected topics using GPT-4o
 * @param {string} sessionId - The session ID
 * @param {string[]} selectedTopics - Array of topic titles
 * @param {number} numQuestionsPerTopic - Questions to generate per topic (default 2)
 * @returns {Promise} Generated questions
 */
export async function generateQuestionsFromTopics(sessionId, selectedTopics, numQuestionsPerTopic = 2) {
  const { data } = await apiClient.post(
    `/pdf-v2/sessions/${sessionId}/generate-questions`,
    {
      session_id: sessionId,
      selected_topics: selectedTopics,
      num_questions_per_topic: numQuestionsPerTopic
    }
  );
  return data;
}

/**
 * Submit quiz responses and get AI-generated feedback
 * @param {string} sessionId - The session ID
 * @param {Array} responses - Array of response objects
 * @returns {Promise} Feedback and updated traits
 */
export async function submitQuizWithFeedback(sessionId, responses) {
  const { data } = await apiClient.post(
    `/pdf-v2/sessions/${sessionId}/submit-quiz`,
    {
      session_id: sessionId,
      responses
    }
  );
  return data;
}

/**
 * Delete a learning session
 * @param {string} sessionId - The session ID to delete
 * @returns {Promise} Deletion confirmation
 */
export async function deleteSession(sessionId) {
  const { data } = await apiClient.delete(`/pdf-v2/sessions/${sessionId}`);
  return data;
}
