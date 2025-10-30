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
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
} from "recharts";
import { useAuth } from "../context/AuthContext.jsx";
import { getUserSessions, getSessionDetails, deleteSession } from "../api/pdfApi.js";

// Helper to get trait change from localStorage
const getTraitChanges = () => {
  const changes = localStorage.getItem('trait_changes');
  return changes ? JSON.parse(changes) : null;
};

// Helper to clear trait changes
const clearTraitChanges = () => {
  localStorage.removeItem('trait_changes');
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [traitChanges, setTraitChanges] = useState(null);
  const [showChanges, setShowChanges] = useState(false);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'analytics', 'sessions'

  // Check for trait changes on mount
  useEffect(() => {
    const changes = getTraitChanges();
    if (changes) {
      setTraitChanges(changes);
      setShowChanges(true);
      
      // Auto-hide changes after 10 seconds
      setTimeout(() => {
        setShowChanges(false);
      }, 10000);
    }
  }, []);

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
      
      // Check if it's an authentication error
      if (error.response?.status === 401) {
        toast.error("Your session has expired. Please log in again.");
        logout();
        navigate("/login");
      } else {
        toast.error("Failed to load sessions");
      }
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

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      toast.success("Session deleted successfully");
      setDeleteConfirmId(null);
      await fetchSessions();
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
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

  // Generate historical trait evolution data
  const getTraitEvolutionData = () => {
    if (!sessions || sessions.length === 0) return [];
    
    // Sort sessions by date
    const sortedSessions = [...sessions]
      .filter(s => s.quiz_completed)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    // This is simulated - in production, you'd store trait snapshots after each quiz
    // For now, we'll create synthetic progression data
    const currentTraits = user.cognitive_traits || {};
    const evolutionData = sortedSessions.map((session, idx) => {
      const sessionDate = new Date(session.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      const data = { session: sessionDate, sessionNumber: idx + 1 };
      
      // Simulate trait progression (in production, retrieve from stored snapshots)
      Object.keys(currentTraits).forEach(trait => {
        // Simulate gradual improvement
        const currentValue = currentTraits[trait];
        const progressRatio = (idx + 1) / sortedSessions.length;
        const startValue = Math.max(0.3, currentValue - (0.2 * (1 - progressRatio)));
        data[trait] = Math.round(startValue * 100);
      });
      
      return data;
    });
    
    return evolutionData;
  };

  // Generate performance trends data
  const getPerformanceTrends = () => {
    if (!sessions || sessions.length === 0) return [];
    
    return [...sessions]
      .filter(s => s.quiz_completed)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      .map((session, idx) => ({
        session: new Date(session.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        sessionNumber: idx + 1,
        score: session.score_percentage || 0,
        questions: session.questions_count || 0,
      }));
  };

  // Generate misconception statistics
  const getMisconceptionStats = () => {
    const completedSessions = sessions.filter(s => s.quiz_completed);
    const totalMisconceptions = completedSessions.reduce((acc, session) => {
      const misconceptionCount = session.quiz_results?.feedback?.filter(
        f => f.misconception_addressed
      ).length || 0;
      return acc + misconceptionCount;
    }, 0);
    
    const resolvedCount = 0; // Would need backend support to track resolution
    const activeCount = totalMisconceptions - resolvedCount;
    
    return {
      total: totalMisconceptions,
      active: activeCount,
      resolved: resolvedCount,
    };
  };

  // Generate weekly activity data
  const getWeeklyActivity = () => {
    if (!sessions || sessions.length === 0) return [];
    
    const last7Days = [];
    const today = new Date();
    
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
      
      const sessionsOnDay = sessions.filter(s => {
        const sessionDate = new Date(s.created_at);
        return sessionDate.toDateString() === date.toDateString();
      }).length;
      
      last7Days.push({
        day: dayName,
        sessions: sessionsOnDay,
      });
    }
    
    return last7Days;
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 px-6 py-16 text-slate-100">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10">
        {/* Trait Update Notification */}
        {showChanges && traitChanges && (
          <div className="rounded-2xl border-2 border-emerald-500/50 bg-emerald-900/20 p-6 shadow-xl">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-xl font-bold text-emerald-400 flex items-center gap-2">
                  🎉 Cognitive Profile Updated!
                </h3>
                <p className="text-sm text-gray-300 mt-1">
                  Your recent quiz has been analyzed. Here's how your traits changed:
                </p>
              </div>
              <button
                onClick={() => {
                  setShowChanges(false);
                  clearTraitChanges();
                }}
                className="text-gray-400 hover:text-white text-2xl transition"
              >
                ×
              </button>
            </div>
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(traitChanges).map(([trait, change]) => {
                const changeValue = change.new_value - change.old_value;
                const changePercentage = Math.round(changeValue * 100);
                
                return (
                  <div key={trait} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700">
                    <p className="text-xs text-gray-400 capitalize mb-1">
                      {trait.replace(/_/g, ' ')}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white">
                        {Math.round(change.old_value * 100)}% → {Math.round(change.new_value * 100)}%
                      </span>
                      <span className={`text-xs font-bold ${
                        changeValue > 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {changeValue > 0 ? '+' : ''}{changePercentage}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

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

        {/* Navigation Tabs */}
        <nav className="rounded-2xl border border-slate-700 bg-gray-800/90 p-2 shadow-lg">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('overview')}
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition ${
                activeTab === 'overview'
                  ? 'bg-teal-600 text-white shadow-lg'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              📊 Overview
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition ${
                activeTab === 'analytics'
                  ? 'bg-teal-600 text-white shadow-lg'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              📈 Historical Analytics
            </button>
            <button
              onClick={() => setActiveTab('sessions')}
              className={`flex-1 px-6 py-3 rounded-xl font-semibold transition ${
                activeTab === 'sessions'
                  ? 'bg-teal-600 text-white shadow-lg'
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              📚 Learning Sessions
            </button>
          </div>
        </nav>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>

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
                  {Object.entries(traits).map(([trait, value]) => {
                    const change = traitChanges?.[trait];
                    const changeValue = change ? change.new_value - change.old_value : 0;
                    const changePercentage = Math.round(changeValue * 100);
                    
                    return (
                      <div key={trait}>
                        <div className="flex items-center justify-between text-sm">
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
                            {showChanges && change && changeValue !== 0 && (
                              <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                                changeValue > 0 
                                  ? 'bg-emerald-900/50 text-emerald-400' 
                                  : 'bg-red-900/50 text-red-400'
                              }`}>
                                {changeValue > 0 ? '+' : ''}{changePercentage}
                              </span>
                            )}
                          </div>
                        </div>
                        {showChanges && change && (
                          <div className="mt-1 text-xs text-gray-500 text-right">
                            Previous: {Math.round(change.old_value * 100)}%
                          </div>
                        )}
                      </div>
                    );
                  })}
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
            <h3 className="text-2xl font-semibold text-teal-400 mb-2">Recent Sessions</h3>
            <p className="text-sm text-gray-400 mb-6">
              Your latest study sessions
            </p>

            {loadingSessions ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto"></div>
                <p className="text-gray-400 mt-4">Loading sessions...</p>
              </div>
            ) : sessions.length > 0 ? (
              <div className="space-y-3">
                {sessions.slice(0, 3).map((session) => (
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
                        <div className="flex gap-2">
                          {session.quiz_completed && (
                            <button
                              onClick={() => handleViewFeedback(session.id)}
                              className="px-3 py-1 bg-teal-600/30 hover:bg-teal-600/50 text-teal-300 text-xs rounded transition"
                            >
                              View Feedback
                            </button>
                          )}
                          {deleteConfirmId === session.id ? (
                            <>
                              <button
                                onClick={() => handleDeleteSession(session.id)}
                                className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition"
                              >
                                Confirm
                              </button>
                              <button
                                onClick={() => setDeleteConfirmId(null)}
                                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-xs rounded transition"
                              >
                                Cancel
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => setDeleteConfirmId(session.id)}
                              className="px-3 py-1 bg-red-600/30 hover:bg-red-600/50 text-red-300 text-xs rounded transition"
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                {sessions.length > 3 && (
                  <button
                    onClick={() => setActiveTab('sessions')}
                    className="w-full mt-3 px-4 py-3 bg-teal-600/20 border border-teal-500/50 rounded-lg hover:bg-teal-600/30 transition text-teal-300 font-semibold"
                  >
                    View All {sessions.length} Sessions →
                  </button>
                )}
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

            <button
              onClick={() => setActiveTab('analytics')}
              className="p-6 bg-purple-600/20 border border-purple-500/50 rounded-xl hover:bg-purple-600/30 transition group"
            >
              <div className="text-3xl mb-2">📊</div>
              <h4 className="font-semibold text-white group-hover:text-purple-400 transition">
                Analytics
              </h4>
              <p className="text-sm text-gray-400 mt-1">
                View detailed trends
              </p>
            </button>
          </div>
        </section>
          </>
        )}

        {/* Historical Analytics Tab */}
        {activeTab === 'analytics' && (
          <>
            {/* Analytics Header */}
            <section className="rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-transparent p-8 shadow-xl">
              <h2 className="text-3xl font-bold text-white mb-2">📈 Historical Analytics</h2>
              <p className="text-gray-400">
                Track your cognitive growth, performance trends, and misconception resolution over time
              </p>
            </section>

            {/* Quick Stats Cards */}
            <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="rounded-xl border border-teal-500/30 bg-teal-500/10 p-6">
                <div className="text-3xl mb-2">📚</div>
                <div className="text-3xl font-bold text-teal-400">{sessions.filter(s => s.quiz_completed).length}</div>
                <p className="text-sm text-gray-400 mt-1">Quizzes Completed</p>
              </div>
              
              <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-6">
                <div className="text-3xl mb-2">🎯</div>
                <div className="text-3xl font-bold text-blue-400">
                  {sessions.filter(s => s.quiz_completed).length > 0
                    ? Math.round(
                        sessions
                          .filter(s => s.quiz_completed)
                          .reduce((acc, s) => acc + (s.score_percentage || 0), 0) /
                          sessions.filter(s => s.quiz_completed).length
                      )
                    : 0}%
                </div>
                <p className="text-sm text-gray-400 mt-1">Average Score</p>
              </div>
              
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-6">
                <div className="text-3xl mb-2">🧠</div>
                <div className="text-3xl font-bold text-rose-400">{getMisconceptionStats().total}</div>
                <p className="text-sm text-gray-400 mt-1">Misconceptions Identified</p>
              </div>
              
              <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-6">
                <div className="text-3xl mb-2">✅</div>
                <div className="text-3xl font-bold text-emerald-400">
                  {Object.values(traits).filter(v => v >= 0.7).length}
                </div>
                <p className="text-sm text-gray-400 mt-1">Strong Traits (≥70%)</p>
              </div>
            </section>

            {/* Trait Evolution Chart */}
            {getTraitEvolutionData().length > 0 && (
              <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
                <h3 className="text-2xl font-semibold text-purple-400 mb-2">📊 Cognitive Trait Evolution</h3>
                <p className="text-sm text-gray-400 mb-6">
                  Track how your cognitive abilities have improved across sessions
                </p>
                
                <div className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={getTraitEvolutionData()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="session" 
                        stroke="#9ca3af"
                        tick={{ fontSize: 12, fill: "#d1d5db" }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        tick={{ fontSize: 12, fill: "#d1d5db" }}
                        domain={[0, 100]}
                        label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                        labelStyle={{ color: '#d1d5db' }}
                      />
                      <Legend 
                        wrapperStyle={{ paddingTop: '20px' }}
                        formatter={(value) => value.replace(/_/g, ' ')}
                      />
                      {Object.keys(traits).map((trait, idx) => {
                        const colors = ['#14b8a6', '#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];
                        return (
                          <Line 
                            key={trait}
                            type="monotone" 
                            dataKey={trait} 
                            stroke={colors[idx % colors.length]}
                            strokeWidth={2}
                            dot={{ r: 4 }}
                            activeDot={{ r: 6 }}
                            name={trait}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>
            )}

            {/* Performance Trends */}
            {getPerformanceTrends().length > 0 && (
              <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
                <h3 className="text-2xl font-semibold text-blue-400 mb-2">🎯 Quiz Performance Trends</h3>
                <p className="text-sm text-gray-400 mb-6">
                  Your quiz scores over time - spot improvement patterns
                </p>
                
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={getPerformanceTrends()}>
                      <defs>
                        <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis 
                        dataKey="session" 
                        stroke="#9ca3af"
                        tick={{ fontSize: 12, fill: "#d1d5db" }}
                      />
                      <YAxis 
                        stroke="#9ca3af"
                        tick={{ fontSize: 12, fill: "#d1d5db" }}
                        domain={[0, 100]}
                        label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                      />
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                        labelStyle={{ color: '#d1d5db' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="score" 
                        stroke="#3b82f6" 
                        strokeWidth={3}
                        fillOpacity={1} 
                        fill="url(#scoreGradient)" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Performance Insights */}
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Best Performance</p>
                    <p className="text-2xl font-bold text-emerald-400">
                      {Math.max(...getPerformanceTrends().map(d => d.score))}%
                    </p>
                  </div>
                  <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Latest Score</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {getPerformanceTrends()[getPerformanceTrends().length - 1]?.score || 0}%
                    </p>
                  </div>
                  <div className="bg-gray-700/50 border border-gray-600 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-1">Improvement</p>
                    <p className="text-2xl font-bold text-purple-400">
                      {getPerformanceTrends().length > 1
                        ? `${Math.round(
                            getPerformanceTrends()[getPerformanceTrends().length - 1].score -
                            getPerformanceTrends()[0].score
                          )}%`
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </section>
            )}

            {/* Weekly Activity */}
            <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
              <h3 className="text-2xl font-semibold text-teal-400 mb-2">📅 Weekly Activity</h3>
              <p className="text-sm text-gray-400 mb-6">
                Your learning activity over the past 7 days
              </p>
              
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={getWeeklyActivity()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="day" 
                      stroke="#9ca3af"
                      tick={{ fontSize: 12, fill: "#d1d5db" }}
                    />
                    <YAxis 
                      stroke="#9ca3af"
                      tick={{ fontSize: 12, fill: "#d1d5db" }}
                      allowDecimals={false}
                      label={{ value: 'Sessions', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                      labelStyle={{ color: '#d1d5db' }}
                    />
                    <Bar 
                      dataKey="sessions" 
                      fill="#14b8a6" 
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Misconception Resolution Progress */}
            <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
              <h3 className="text-2xl font-semibold text-rose-400 mb-2">🧠 Misconception Resolution</h3>
              <p className="text-sm text-gray-400 mb-6">
                Track identified misconceptions and resolution progress
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-6 bg-rose-900/20 border border-rose-700/50 rounded-xl">
                  <div className="text-5xl font-bold text-rose-400 mb-2">
                    {getMisconceptionStats().total}
                  </div>
                  <p className="text-sm text-gray-400">Total Identified</p>
                </div>
                
                <div className="text-center p-6 bg-amber-900/20 border border-amber-700/50 rounded-xl">
                  <div className="text-5xl font-bold text-amber-400 mb-2">
                    {getMisconceptionStats().active}
                  </div>
                  <p className="text-sm text-gray-400">Active (Need Work)</p>
                </div>
                
                <div className="text-center p-6 bg-emerald-900/20 border border-emerald-700/50 rounded-xl">
                  <div className="text-5xl font-bold text-emerald-400 mb-2">
                    {getMisconceptionStats().resolved}
                  </div>
                  <p className="text-sm text-gray-400">Resolved (3/3 correct)</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-400">Resolution Rate</span>
                  <span className="text-sm font-bold text-emerald-400">
                    {getMisconceptionStats().total > 0
                      ? Math.round((getMisconceptionStats().resolved / getMisconceptionStats().total) * 100)
                      : 0}%
                  </span>
                </div>
                <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full transition-all duration-500"
                    style={{ 
                      width: `${getMisconceptionStats().total > 0
                        ? (getMisconceptionStats().resolved / getMisconceptionStats().total) * 100
                        : 0}%` 
                    }}
                  />
                </div>
              </div>
            </section>
          </>
        )}

        {/* Sessions Tab */}
        {activeTab === 'sessions' && (
          <>
            <section className="rounded-2xl border border-teal-500/30 bg-gradient-to-br from-teal-500/10 to-transparent p-8 shadow-xl">
              <h2 className="text-3xl font-bold text-white mb-2">📚 Learning Sessions History</h2>
              <p className="text-gray-400">
                All your past study sessions and quiz attempts with detailed feedback
              </p>
            </section>

            {/* Full Sessions List */}
            <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-6 shadow-lg">
              {loadingSessions ? (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto"></div>
                  <p className="text-gray-400 mt-4">Loading sessions...</p>
                </div>
              ) : sessions.length > 0 ? (
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div 
                      key={session.id}
                      className="p-5 bg-gray-700/50 border border-gray-600 rounded-xl hover:bg-gray-700/70 transition"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-white mb-2">{session.filename}</h4>
                          <div className="flex items-center gap-3 mb-3 text-sm text-gray-400">
                            <span>📚 {session.topics_count} topics extracted</span>
                            {session.quiz_completed && (
                              <>
                                <span>•</span>
                                <span>✅ {session.questions_count} questions</span>
                                <span>•</span>
                                <span className={`font-semibold px-2 py-1 rounded ${
                                  session.score_percentage >= 80 ? 'bg-green-900/30 text-green-400' :
                                  session.score_percentage >= 60 ? 'bg-yellow-900/30 text-yellow-400' :
                                  'bg-red-900/30 text-red-400'
                                }`}>
                                  Score: {session.score_percentage}%
                                </span>
                              </>
                            )}
                          </div>
                          {session.topics && session.topics.length > 0 && (
                            <div className="flex flex-wrap gap-2">
                              {session.topics.map((topic, idx) => (
                                <span 
                                  key={idx}
                                  className="px-3 py-1 bg-teal-600/20 border border-teal-500/30 rounded-full text-xs text-teal-300"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2 ml-4">
                          <span className="text-sm text-gray-500">
                            {new Date(session.created_at).toLocaleDateString()}
                          </span>
                          <div className="flex gap-2">
                            {session.quiz_completed && (
                              <button
                                onClick={() => handleViewFeedback(session.id)}
                                className="px-4 py-2 bg-teal-600/30 hover:bg-teal-600/50 text-teal-300 text-sm rounded-lg transition font-semibold"
                              >
                                View Feedback
                              </button>
                            )}
                            {deleteConfirmId === session.id ? (
                              <>
                                <button
                                  onClick={() => handleDeleteSession(session.id)}
                                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg transition font-semibold"
                                >
                                  Confirm
                                </button>
                                <button
                                  onClick={() => setDeleteConfirmId(null)}
                                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded-lg transition font-semibold"
                                >
                                  Cancel
                                </button>
                              </>
                            ) : (
                              <button
                                onClick={() => setDeleteConfirmId(session.id)}
                                className="px-4 py-2 bg-red-600/30 hover:bg-red-600/50 text-red-300 text-sm rounded-lg transition font-semibold"
                              >
                                Delete
                              </button>
                            )}
                          </div>
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
            </section>
          </>
        )}

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
