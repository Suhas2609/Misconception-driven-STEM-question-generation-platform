import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import { useAuth } from "../context/AuthContext.jsx";
import { getUserSessions, getSessionDetails } from "../api/pdfApi.js";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);

  // Fetch user's sessions on mount
  useEffect(() => {
    if (user) {
      fetchSessions();
    }
  }, [user]);

  const fetchSessions = async () => {
    try {
      setLoadingSessions(true);
      const sessionsData = await getUserSessions();
      setSessions(sessionsData);
    } catch (error) {
      console.error("Error fetching sessions:", error);
      toast.error("Failed to load sessions");
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleViewFeedback = async (sessionId) => {
    try {
      const { session } = await getSessionDetails(sessionId);
      setSelectedSession(session);
      setShowFeedbackModal(true);
    } catch (error) {
      console.error("Error fetching session details:", error);
      toast.error("Failed to load quiz feedback");
    }
  };

  if (!user) {
    return null;
  }

  // Transform cognitive traits for radar chart
  const traits = user.cognitive_traits || {};
  const traitChartData = Object.entries(traits).map(([trait, value]) => ({
    trait: trait.replace(/_/g, " "),
    score: Number(value ?? 0),
  }));

  const handleLogout = () => {
    logout();
    toast.success("Logged out successfully");
    navigate("/login");
  };

  const handleStartNewSession = () => {
    navigate("/upload");
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 px-6 py-16 text-slate-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        {/* Header */}
        <header className="rounded-2xl border border-slate-700 bg-gray-800/90 p-8 shadow-xl">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white">Welcome back, {user.name}!</h1>
              <p className="mt-2 text-gray-400">
                Your cognitive profile has been analyzed. Ready to continue learning?
              </p>
              <p className="mt-1 text-sm text-gray-500">
                Account: {user.email} · Joined {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition text-sm"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Main Content Grid */}
        <section className="grid gap-6 md:grid-cols-2">
          {/* Cognitive Traits Radar Chart */}
          <article className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
            <h3 className="text-2xl font-semibold text-teal-400 mb-2">Your Cognitive Profile</h3>
            <p className="text-sm text-gray-400 mb-4">
              Based on your assessment responses, here are your cognitive strengths
            </p>
            
            {traitChartData.length > 0 ? (
              <>
                <div className="h-80 mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={traitChartData} outerRadius="75%">
                      <PolarGrid stroke="#374151" />
                      <PolarAngleAxis 
                        dataKey="trait" 
                        stroke="#9ca3af" 
                        tick={{ fontSize: 11, fill: "#d1d5db" }}
                        className="capitalize"
                      />
                      <PolarRadiusAxis 
                        angle={30} 
                        domain={[0, 1]} 
                        stroke="#374151"
                        tick={{ fontSize: 10, fill: "#9ca3af" }}
                        tickFormatter={(value) => `${Math.round(value * 100)}%`}
                      />
                      <Radar 
                        dataKey="score" 
                        stroke="#14b8a6" 
                        fill="#14b8a6" 
                        fillOpacity={0.5}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>

                {/* Trait Breakdown */}
                <div className="mt-6 space-y-2">
                  {Object.entries(traits).map(([trait, value]) => (
                    <div key={trait} className="flex items-center justify-between text-sm">
                      <span className="text-gray-300 capitalize">{trait.replace(/_/g, " ")}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-teal-500 rounded-full transition-all duration-500"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                        <span className="text-teal-400 font-semibold w-12 text-right">
                          {Math.round(value * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="mt-4 text-sm text-gray-400">
                Complete the cognitive assessment to see your profile.
              </p>
            )}
          </article>

          {/* Recent Sessions */}
          <article className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
            <h3 className="text-2xl font-semibold text-teal-400 mb-2">Learning Sessions</h3>
            <p className="text-sm text-gray-400 mb-6">
              Your previous study sessions and quiz attempts
            </p>

            {loadingSessions ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto"></div>
                <p className="text-gray-400 mt-4">Loading sessions...</p>
              </div>
            ) : sessions.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                {sessions.map((session) => (
                  <div 
                    key={session.id}
                    className="p-4 bg-gray-700/50 border border-gray-600 rounded-lg hover:bg-gray-700/70 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-white">{session.filename}</h4>
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                          <span>📚 {session.topics_count} topics extracted</span>
                          {session.quiz_completed && (
                            <>
                              <span>•</span>
                              <span>✅ {session.questions_count} questions</span>
                              <span>•</span>
                              <span className={`font-semibold ${
                                session.score_percentage >= 80 ? 'text-green-400' :
                                session.score_percentage >= 60 ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                Score: {session.score_percentage}%
                              </span>
                            </>
                          )}
                        </div>
                        {session.topics && session.topics.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {session.topics.slice(0, 3).map((topic, idx) => (
                              <span 
                                key={idx}
                                className="px-2 py-1 bg-teal-600/20 border border-teal-500/30 rounded text-xs text-teal-300"
                              >
                                {topic}
                              </span>
                            ))}
                            {session.topics.length > 3 && (
                              <span className="px-2 py-1 text-xs text-gray-400">
                                +{session.topics.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className="text-xs text-gray-500">
                          {new Date(session.created_at).toLocaleDateString()}
                        </span>
                        {session.quiz_completed && (
                          <button
                            onClick={() => handleViewFeedback(session.id)}
                            className="px-3 py-1 bg-teal-600/30 hover:bg-teal-600/50 text-teal-300 text-xs rounded transition"
                          >
                            View Feedback
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-400 mb-6">No learning sessions yet</p>
                <button
                  onClick={handleStartNewSession}
                  className="px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg transition"
                >
                  Start Your First Session
                </button>
              </div>
            )}
          </article>
        </section>

        {/* Quick Actions */}
        <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
          <h3 className="text-xl font-semibold text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={handleStartNewSession}
              className="p-6 bg-teal-600/20 border border-teal-500/50 rounded-xl hover:bg-teal-600/30 transition group"
            >
              <div className="text-3xl mb-2">📚</div>
              <h4 className="font-semibold text-white group-hover:text-teal-400 transition">
                New Learning Session
              </h4>
              <p className="text-sm text-gray-400 mt-1">
                Upload a PDF and start practicing
              </p>
            </button>

            <Link
              to="/assessment"
              className="p-6 bg-blue-600/20 border border-blue-500/50 rounded-xl hover:bg-blue-600/30 transition group"
            >
              <div className="text-3xl mb-2">🧠</div>
              <h4 className="font-semibold text-white group-hover:text-blue-400 transition">
                Retake Assessment
              </h4>
              <p className="text-sm text-gray-400 mt-1">
                Update your cognitive profile
              </p>
            </Link>

            <div className="p-6 bg-purple-600/20 border border-purple-500/50 rounded-xl opacity-60">
              <div className="text-3xl mb-2">📊</div>
              <h4 className="font-semibold text-white">
                Analytics
              </h4>
              <p className="text-sm text-gray-400 mt-1">
                Coming soon
              </p>
            </div>
          </div>
        </section>

        {/* Stats Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>
            Onboarding: {user.onboarding_completed ? "✅ Complete" : "⏳ Pending"} · 
            Traits analyzed: {Object.keys(traits).length}
          </p>
        </div>
      </div>

      {/* Feedback Modal */}
      {showFeedbackModal && selectedSession && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-gray-800 rounded-2xl border border-slate-700 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-gray-800 border-b border-slate-700 p-6 flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedSession.filename}</h2>
                <p className="text-sm text-gray-400 mt-1">
                  Submitted: {selectedSession.quiz_results?.submitted_at 
                    ? new Date(selectedSession.quiz_results.submitted_at).toLocaleString()
                    : 'N/A'}
                </p>
              </div>
              <button
                onClick={() => setShowFeedbackModal(false)}
                className="text-gray-400 hover:text-white transition text-2xl"
              >
                ×
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Overall Score */}
              <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-6">
                <h3 className="text-xl font-semibold text-white mb-4">Quiz Summary</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-teal-400">
                      {selectedSession.quiz_results?.score_percentage}%
                    </div>
                    <div className="text-sm text-gray-400 mt-1">Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white">
                      {selectedSession.quiz_results?.correct_count}/{selectedSession.quiz_results?.total_questions}
                    </div>
                    <div className="text-sm text-gray-400 mt-1">Correct</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">
                      {selectedSession.quiz_results?.avg_confidence}%
                    </div>
                    <div className="text-sm text-gray-400 mt-1">Avg Confidence</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-400">
                      {selectedSession.selected_topics?.length || 0}
                    </div>
                    <div className="text-sm text-gray-400 mt-1">Topics</div>
                  </div>
                </div>
              </div>

              {/* Per-Question Feedback */}
              <div>
                <h3 className="text-xl font-semibold text-white mb-4">Question-by-Question Feedback</h3>
                <div className="space-y-4">
                  {selectedSession.quiz_results?.feedback?.map((item, idx) => (
                    <div 
                      key={idx}
                      className={`rounded-xl border p-5 ${
                        item.is_correct 
                          ? 'bg-green-900/20 border-green-700/50' 
                          : 'bg-red-900/20 border-red-700/50'
                      }`}
                    >
                      {/* Question Header */}
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="font-semibold text-white flex items-center gap-2">
                          <span className={`text-lg ${item.is_correct ? 'text-green-400' : 'text-red-400'}`}>
                            {item.is_correct ? '✓' : '✗'}
                          </span>
                          Question {item.question_number}
                        </h4>
                        <span className="text-xs px-2 py-1 bg-gray-700/50 rounded text-gray-300">
                          Confidence: {item.confidence}%
                        </span>
                      </div>

                      {/* Question Text */}
                      <p className="text-gray-200 mb-3">{item.question_text}</p>

                      {/* User's Answer */}
                      <div className="mb-3 p-3 bg-gray-700/30 rounded-lg">
                        <p className="text-sm text-gray-400 mb-1">Your Answer:</p>
                        <p className="text-white">{item.user_answer}</p>
                      </div>

                      {/* Correct Answer (if wrong) */}
                      {!item.is_correct && (
                        <div className="mb-3 p-3 bg-green-900/20 border border-green-700/30 rounded-lg">
                          <p className="text-sm text-gray-400 mb-1">Correct Answer:</p>
                          <p className="text-green-300">{item.correct_answer}</p>
                        </div>
                      )}

                      {/* AI Explanation */}
                      <div className="mb-3">
                        <p className="text-sm font-semibold text-teal-400 mb-1">💡 Explanation:</p>
                        <p className="text-gray-300 text-sm leading-relaxed">{item.explanation}</p>
                      </div>

                      {/* Misconception Analysis */}
                      {item.misconception_addressed && (
                        <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
                          <p className="text-sm font-semibold text-yellow-400 mb-1">⚠️ Misconception Identified:</p>
                          <p className="text-gray-300 text-sm">{item.misconception_addressed}</p>
                        </div>
                      )}

                      {/* Confidence Analysis */}
                      {item.confidence_analysis && (
                        <div className="mb-3">
                          <p className="text-sm font-semibold text-blue-400 mb-1">📊 Confidence Analysis:</p>
                          <p className="text-gray-300 text-sm">{item.confidence_analysis}</p>
                        </div>
                      )}

                      {/* Learning Tips */}
                      {item.learning_tips && item.learning_tips.length > 0 && (
                        <div className="mb-3">
                          <p className="text-sm font-semibold text-purple-400 mb-2">📚 Learning Tips:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {item.learning_tips.map((tip, tipIdx) => (
                              <li key={tipIdx} className="text-gray-300 text-sm">{tip}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Encouragement */}
                      {item.encouragement && (
                        <div className="mt-3 p-3 bg-teal-900/20 border border-teal-700/30 rounded-lg">
                          <p className="text-teal-300 text-sm italic">💪 {item.encouragement}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Close Button */}
              <div className="text-center pt-4">
                <button
                  onClick={() => setShowFeedbackModal(false)}
                  className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
