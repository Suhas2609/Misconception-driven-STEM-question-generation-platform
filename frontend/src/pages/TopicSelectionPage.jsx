import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useAuth } from "../context/AuthContext.jsx";
import { selectTopicsForPractice, generateQuestionsFromTopics } from "../api/pdfApi.js";

export default function TopicSelectionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  // Get session data from navigation state
  const sessionData = location.state?.sessionData;
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!sessionData) {
      toast.error("No session data found. Please upload a PDF first.");
      navigate("/upload");
    }
  }, [sessionData, navigate]);

  if (!sessionData) {
    return null;
  }

  const { session_id, topics, filename, document_summary } = sessionData;

  const toggleTopic = (topicTitle) => {
    setSelectedTopics((prev) =>
      prev.includes(topicTitle)
        ? prev.filter((t) => t !== topicTitle)
        : [...prev, topicTitle]
    );
  };

  const handleStartPractice = async () => {
    if (selectedTopics.length === 0) {
      toast.error("Please select at least one topic to practice.");
      return;
    }

    setIsSubmitting(true);
    try {
      // Step 1: Save selected topics
      await selectTopicsForPractice(session_id, selectedTopics);
      
      toast.success("Generating personalized questions with GPT-4o...");
      
      // Step 2: Generate questions using GPT-4o (CORE PROMPT ENGINEERING!)
      const questionData = await generateQuestionsFromTopics(
        session_id,
        selectedTopics,
        2  // 2 questions per topic
      );
      
      toast.success(`Generated ${questionData.num_questions} personalized questions!`);
      
      // Navigate to quiz page with generated questions
      navigate("/quiz", {
        state: {
          sessionId: session_id,
          questions: questionData.questions,
          topics: selectedTopics,
          filename,
        },
      });
    } catch (error) {
      console.error("Failed to generate questions:", error);
      toast.error(error.response?.data?.detail || "Failed to generate questions. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case "beginner":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
      case "intermediate":
        return "text-yellow-400 bg-yellow-500/10 border-yellow-500/30";
      case "advanced":
        return "text-rose-400 bg-rose-500/10 border-rose-500/30";
      default:
        return "text-slate-400 bg-slate-500/10 border-slate-500/30";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-sm">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                📚 Select Topics to Practice
              </h1>
              <p className="mt-1 text-sm text-slate-400">
                Logged in as: <span className="text-emerald-400">{user?.email}</span>
              </p>
            </div>
            <button
              onClick={() => navigate("/dashboard")}
              className="rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-2 text-sm text-slate-300 transition hover:border-slate-600 hover:bg-slate-800"
            >
              ← Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-6xl px-6 py-8">
        {/* Document Summary */}
        <div className="mb-8 rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-500/5 to-transparent p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-2xl">
              📄
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-white">{filename}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">
                {document_summary}
              </p>
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-emerald-400">
                  ✨ {topics.length} topics extracted by GPT-4o
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Topics Grid */}
        <div className="mb-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Choose topics you want to practice ({selectedTopics.length} selected):
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {topics.map((topic) => {
              const isSelected = selectedTopics.includes(topic.title);
              return (
                <button
                  key={topic.title}
                  onClick={() => toggleTopic(topic.title)}
                  className={`group relative rounded-2xl border p-5 text-left transition ${
                    isSelected
                      ? "border-emerald-500/50 bg-emerald-500/10 shadow-lg shadow-emerald-900/20"
                      : "border-slate-700/50 bg-slate-800/30 hover:border-slate-600 hover:bg-slate-800/50"
                  }`}
                >
                  {/* Selection Indicator */}
                  <div className="absolute right-4 top-4">
                    <div
                      className={`flex h-6 w-6 items-center justify-center rounded-full border-2 transition ${
                        isSelected
                          ? "border-emerald-500 bg-emerald-500 text-white"
                          : "border-slate-600 bg-transparent"
                      }`}
                    >
                      {isSelected && "✓"}
                    </div>
                  </div>

                  {/* Topic Content */}
                  <div className="pr-10">
                    <h4 className="mb-2 font-semibold text-white">{topic.title}</h4>
                    <p className="mb-3 text-sm leading-relaxed text-slate-300">
                      {topic.description}
                    </p>

                    {/* Difficulty Badge */}
                    <div className="mb-3">
                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-medium ${getDifficultyColor(
                          topic.difficulty
                        )}`}
                      >
                        {topic.difficulty || "intermediate"}
                      </span>
                    </div>

                    {/* Keywords */}
                    {topic.keywords && topic.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {topic.keywords.slice(0, 5).map((keyword) => (
                          <span
                            key={keyword}
                            className="rounded-md bg-slate-700/30 px-2 py-0.5 text-xs text-slate-400"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Prerequisites */}
                    {topic.prerequisites && topic.prerequisites.length > 0 && (
                      <p className="mt-2 text-xs text-slate-500">
                        Prerequisites: {topic.prerequisites.join(", ")}
                      </p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between rounded-2xl border border-slate-700/50 bg-slate-800/30 p-6">
          <div className="text-sm text-slate-300">
            {selectedTopics.length > 0 ? (
              <p>
                <span className="font-semibold text-white">{selectedTopics.length}</span> topic
                {selectedTopics.length > 1 ? "s" : ""} selected for practice
              </p>
            ) : (
              <p className="text-slate-500">Select topics to generate personalized questions</p>
            )}
          </div>
          <button
            onClick={handleStartPractice}
            disabled={selectedTopics.length === 0 || isSubmitting}
            className="rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-8 py-3 font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:from-emerald-600 hover:to-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Generating Questions..." : "Start Practice →"}
          </button>
        </div>
      </main>
    </div>
  );
}
