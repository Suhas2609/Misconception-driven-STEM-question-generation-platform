import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { getAssessmentQuestions, submitAssessment } from "../api/assessmentApi";
import { extractErrorMessage } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function AssessmentPage() {
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);

  const { token, updateUser } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    getAssessmentQuestions()
      .then((data) => {
        setQuestions(data);
        // Initialize response state
        const initial = {};
        data.forEach((q) => {
          initial[q.id] = { question_id: q.id, answer_text: "", confidence: null };
        });
        setResponses(initial);
      })
      .catch((err) => {
        toast.error(extractErrorMessage(err, "Failed to load assessment"));
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleAnswerChange = (questionId, text) => {
    setResponses((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], answer_text: text },
    }));
  };

  const handleSubmit = async () => {
    // Validate all questions answered
    const unanswered = questions.filter((q) => !responses[q.id]?.answer_text.trim());
    if (unanswered.length > 0) {
      toast.error(`Please answer all questions (${unanswered.length} remaining)`);
      return;
    }

    setSubmitting(true);
    try {
      const submission = {
        responses: Object.values(responses).map((r) => ({
          question_id: r.question_id,
          answer_text: r.answer_text,
          confidence: r.confidence,
        })),
      };

      const updatedUser = await submitAssessment(token, submission);
      updateUser(updatedUser);
      toast.success("Assessment complete! Your cognitive profile has been created.");
      navigate("/dashboard");
    } catch (err) {
      toast.error(extractErrorMessage(err, "Failed to submit assessment"));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading assessment...</div>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gray-800 rounded-lg shadow-xl p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">
              Cognitive Assessment
            </h1>
            <p className="text-gray-400">
              Answer each question with your reasoning. This helps us understand your learning style.
            </p>
            <div className="mt-4 flex items-center justify-between">
              <span className="text-sm text-gray-400">
                Question {currentIndex + 1} of {questions.length}
              </span>
              <div className="flex gap-1">
                {questions.map((_, idx) => (
                  <div
                    key={idx}
                    className={`h-2 w-2 rounded-full ${
                      idx === currentIndex
                        ? "bg-teal-500"
                        : responses[questions[idx].id]?.answer_text.trim()
                        ? "bg-teal-700"
                        : "bg-gray-600"
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>

          {currentQuestion && (
            <div className="space-y-6">
              <div>
                <div className="flex items-start gap-3 mb-4">
                  <span className="inline-block px-3 py-1 bg-teal-600/20 text-teal-400 text-xs font-medium rounded-full">
                    {currentQuestion.category}
                  </span>
                  <span className="inline-block px-3 py-1 bg-blue-600/20 text-blue-400 text-xs font-medium rounded-full">
                    {currentQuestion.difficulty}
                  </span>
                </div>
                <h2 className="text-xl font-semibold text-white mb-3">
                  {currentQuestion.text}
                </h2>
                {currentQuestion.context && (
                  <p className="text-sm text-gray-400 italic mb-4">
                    {currentQuestion.context}
                  </p>
                )}
              </div>

              <div>
                <label
                  htmlFor="answer"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Your reasoning and answer:
                </label>
                <textarea
                  id="answer"
                  value={responses[currentQuestion.id]?.answer_text || ""}
                  onChange={(e) =>
                    handleAnswerChange(currentQuestion.id, e.target.value)
                  }
                  rows={8}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none"
                  placeholder="Explain your thought process, show calculations, and provide your final answer..."
                />
                <p className="mt-2 text-xs text-gray-500">
                  Be as detailed as possible—your reasoning helps us understand your cognitive strengths.
                </p>
              </div>

              <div className="flex justify-between items-center pt-4">
                <button
                  onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                  disabled={currentIndex === 0}
                  className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Previous
                </button>

                {currentIndex < questions.length - 1 ? (
                  <button
                    onClick={() =>
                      setCurrentIndex((prev) => Math.min(questions.length - 1, prev + 1))
                    }
                    className="px-6 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="px-8 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? "Analyzing..." : "Submit Assessment"}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
