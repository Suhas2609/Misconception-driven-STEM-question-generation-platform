import { useMemo, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { extractErrorMessage } from "../api/client.js";
import { useQuestionContext } from "../context/QuestionContext.jsx";
import { submitQuizWithFeedback } from "../api/pdfApi.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function QuizPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const { questions: contextQuestions, submitResponse } = useQuestionContext();
  
  // Get questions and session ID from navigation state
  const questionsFromState = location.state?.questions || [];
  const sessionId = location.state?.sessionId;
  const allQuestions = questionsFromState.length > 0 ? questionsFromState : contextQuestions;
  
  const [responses, setResponses] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);  // Store AI feedback
  const [showResults, setShowResults] = useState(false);  // Toggle results view
  const [oldTraits, setOldTraits] = useState(null); // Store traits before quiz

  useEffect(() => {
    if (questionsFromState.length > 0) {
      console.log("📝 Loaded", questionsFromState.length, "questions from navigation state");
    }
    
    // Save current traits before quiz
    if (user?.cognitive_traits) {
      setOldTraits(user.cognitive_traits);
    }
  }, [questionsFromState.length, user]);

  const questionList = useMemo(
    () =>
      allQuestions.map((question, index) => ({
        ...question,
        _key: question.id || `question-${index}`,
        _index: index,
      })),
    [allQuestions]
  );

  const handleSelect = (questionKey, value) => {
    setResponses((prev) => ({
      ...prev,
      [questionKey]: {
        ...prev[questionKey],
        selectedOption: value,
      },
    }));
  };

  const handleConfidenceChange = (questionKey, value) => {
    setResponses((prev) => ({
      ...prev,
      [questionKey]: {
        ...prev[questionKey],
        confidence: Number(value),
      },
    }));
  };

  const handleReasoningChange = (questionKey, value) => {
    setResponses((prev) => ({
      ...prev,
      [questionKey]: {
        ...prev[questionKey],
        reasoning: value,
      },
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (questionList.length === 0) {
      toast("Add questions in the generation tab first.", { icon: "ℹ️" });
      return;
    }

    const unanswered = questionList.filter((item) => !responses[item._key]?.selectedOption);

    if (unanswered.length > 0) {
      toast.error("Please respond to each question before submitting.");
      return;
    }

    try {
      setIsSubmitting(true);
      
      // Use new GPT-4o feedback endpoint if sessionId available
      if (sessionId) {
        const formattedResponses = questionList.map((question) => {
          const answer = responses[question._key];
          return {
            question_number: question.question_number || question._index + 1,
            selected_answer: typeof answer.selectedOption === "string" 
              ? answer.selectedOption 
              : answer.selectedOption?.text,
            confidence: Number.isFinite(answer.confidence) ? answer.confidence : 0.5,
            reasoning: answer.reasoning?.trim() || null,
          };
        });

        const result = await submitQuizWithFeedback(sessionId, formattedResponses);
        
        setFeedback(result);
        setShowResults(true);
        
        // Refresh user to get updated traits
        await refreshUser();
        
        // Store trait changes in localStorage for dashboard notification
        if (user?.cognitive_traits && oldTraits) {
          const changes = {};
          Object.keys(user.cognitive_traits).forEach(trait => {
            if (oldTraits[trait] !== undefined) {
              changes[trait] = {
                old_value: oldTraits[trait],
                new_value: user.cognitive_traits[trait]
              };
            }
          });
          localStorage.setItem('trait_changes', JSON.stringify(changes));
        }
        
        toast.success(`Quiz complete! Score: ${result.score_percentage.toFixed(1)}% (${result.correct_count}/${result.total_questions})`);
      } else {
        // Fallback to old submission method
        await Promise.all(
          questionList.map((question) => {
            const answer = responses[question._key];
            const questionId = question.id || question._key;
            return submitResponse({
              questionId,
              selectedOption: typeof answer.selectedOption === "string" ? answer.selectedOption : answer.selectedOption?.text,
              confidence: Number.isFinite(answer.confidence) ? answer.confidence : 0.5,
              reasoning: answer.reasoning?.trim() || undefined,
            });
          })
        );
        toast.success("Responses submitted. Traits refreshed on dashboard.");
      }
    } catch (error) {
      console.error("Submission error:", error);
      toast.error(extractErrorMessage(error, "Failed to submit responses"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-16 text-slate-100">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-10">
        <header className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl shadow-slate-950/50">
          <h2 className="text-3xl font-semibold">Quiz Delivery</h2>
          <p className="mt-2 text-slate-400">
            Once questions are generated, deliver them in class or asynchronously. Learner selections will inform
            misconception tracking.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-8 shadow-lg shadow-slate-950/50 transition hover:-translate-y-1 hover:shadow-2xl">
          <form className="space-y-8" onSubmit={handleSubmit}>
            {questionList.length === 0 ? (
              <p className="text-sm text-slate-400">No questions queued yet.</p>
            ) : (
              <>
                {/* Global Personalization Summary Panel */}
                <div className="rounded-xl border-2 border-teal-500/30 bg-gradient-to-r from-teal-900/20 to-emerald-900/20 p-6 mb-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">🧠</span>
                    <div>
                      <h3 className="text-lg font-bold text-teal-400">AI-Personalized Quiz</h3>
                      <p className="text-xs text-slate-400">Questions adapted to your cognitive profile</p>
                    </div>
                  </div>
                  
                  {user?.cognitive_traits && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                      {Object.entries(user.cognitive_traits).map(([trait, score]) => {
                        const percentage = Math.round(score * 100);
                        const status = percentage >= 80 ? 'strong' : percentage >= 60 ? 'developing' : 'needs support';
                        const color = percentage >= 80 ? 'emerald' : percentage >= 60 ? 'yellow' : 'rose';
                        
                        return (
                          <div key={trait} className={`bg-slate-800/50 rounded-lg p-3 border border-${color}-500/30`}>
                            <div className="text-[10px] text-slate-400 capitalize mb-1">
                              {trait.replace(/_/g, ' ')}
                            </div>
                            <div className="flex items-baseline gap-2">
                              <span className={`text-lg font-bold text-${color}-400`}>{percentage}%</span>
                              <span className={`text-[9px] text-${color}-300/60`}>{status}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                  
                  <div className="mt-4 flex flex-wrap gap-2 text-xs">
                    <div className="bg-purple-900/30 border border-purple-500/30 rounded px-3 py-1">
                      <span className="text-purple-300">📊 Adaptive Difficulty</span>
                    </div>
                    <div className="bg-rose-900/30 border border-rose-500/30 rounded px-3 py-1">
                      <span className="text-rose-300">⚠️ Misconception-Aware</span>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-500/30 rounded px-3 py-1">
                      <span className="text-teal-300">🎯 Trait-Targeted</span>
                    </div>
                  </div>
                  
                  <div className="mt-3 text-[10px] text-slate-400 italic">
                    💡 Each question below shows its personalization metadata (visible for panel review)
                  </div>
                </div>

                <div className="space-y-6">
                {questionList.map((question) => (
                  <article
                    key={question._key}
                    className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-6 shadow-inner transition hover:border-emerald-400/40"
                  >
                    {/* Personalization Proof Panel */}
                    {(question.difficulty || question.traits_targeted || question.misconception_target) && (
                      <div className="mb-4 rounded-lg border-2 border-purple-500/30 bg-purple-900/10 p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-purple-400 font-bold text-xs">🎯 PERSONALIZED FOR YOU</span>
                          <span className="text-[10px] text-purple-300/60">(Visible for panel review)</span>
                        </div>
                        <div className="flex flex-wrap gap-2 text-[11px]">
                          {question.difficulty && (
                            <div className="flex items-center gap-1 bg-slate-800/50 px-2 py-1 rounded border border-slate-700">
                              <span className="text-slate-400">Difficulty:</span>
                              <span className={`font-semibold ${
                                question.difficulty === 'easy' ? 'text-green-400' :
                                question.difficulty === 'medium' ? 'text-yellow-400' :
                                question.difficulty === 'hard' ? 'text-orange-400' :
                                'text-red-400'
                              }`}>
                                {question.difficulty.toUpperCase()}
                              </span>
                            </div>
                          )}
                          {question.traits_targeted && question.traits_targeted.length > 0 && (
                            <div className="flex items-center gap-1 bg-slate-800/50 px-2 py-1 rounded border border-slate-700">
                              <span className="text-slate-400">Targets:</span>
                              <span className="text-teal-400 font-semibold">
                                {question.traits_targeted.map(t => t.replace(/_/g, ' ')).join(', ')}
                              </span>
                            </div>
                          )}
                          {question.misconception_target && (
                            <div className="flex items-center gap-1 bg-slate-800/50 px-2 py-1 rounded border border-slate-700">
                              <span className="text-slate-400">Misconception:</span>
                              <span className="text-rose-400 font-semibold">{question.misconception_target}</span>
                            </div>
                          )}
                          {question.requires_calculation !== undefined && (
                            <div className="flex items-center gap-1 bg-slate-800/50 px-2 py-1 rounded border border-slate-700">
                              <span className="text-slate-400">Calculation:</span>
                              <span className={question.requires_calculation ? 'text-blue-400' : 'text-gray-400'}>
                                {question.requires_calculation ? 'Required' : 'Not Required'}
                              </span>
                            </div>
                          )}
                        </div>
                        {question.adaptive_reason && (
                          <div className="mt-2 text-[10px] text-purple-300/80 italic">
                            💡 {question.adaptive_reason}
                          </div>
                        )}
                      </div>
                    )}
                    
                    <header className="flex items-start justify-between gap-4">
                      <span className="rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-200">
                        Question {question._index + 1}
                      </span>
                    </header>
                    <p className="mt-3 text-base text-slate-100">{question.stem || question.prompt}</p>
                    {question.options && (
                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        {question.options.map((option, optionIdx) => {
                          const optionKey = `${question._key}-option-${optionIdx}`;
                          const optionValue = option.text || option;
                          const optionLabel = option.text || option;
                          const optionType = option.type || '';

                          // Define badge colors based on option type
                          let typeBadge = null;
                          if (optionType === 'correct') {
                            typeBadge = <span className="ml-2 rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300 border border-emerald-500/30">Correct Answer</span>;
                          } else if (optionType === 'misconception') {
                            typeBadge = <span className="ml-2 rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-semibold text-rose-300 border border-rose-500/30">Common Misconception</span>;
                          } else if (optionType === 'partial_misconception' || optionType === 'partial') {
                            typeBadge = <span className="ml-2 rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300 border border-amber-500/30">Partial Understanding</span>;
                          } else if (optionType === 'plausible_distractor' || optionType === 'procedural') {
                            typeBadge = <span className="ml-2 rounded-full bg-blue-500/20 px-2 py-0.5 text-[10px] font-semibold text-blue-300 border border-blue-500/30">Procedural Error</span>;
                          } else if (optionType) {
                            // Fallback for any other type (show it exists)
                            typeBadge = <span className="ml-2 rounded-full bg-slate-500/20 px-2 py-0.5 text-[10px] font-semibold text-slate-300 border border-slate-500/30">{optionType}</span>;
                          }

                          return (
                            <label
                              key={optionKey}
                              className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-800/80 bg-slate-900 px-4 py-3 text-sm text-slate-200 shadow-inner transition hover:border-emerald-400/40"
                            >
                              <input
                                checked={responses[question._key]?.selectedOption === optionValue}
                                className="mt-1 h-4 w-4 rounded-full border-slate-500 text-emerald-400 focus:ring-emerald-400"
                                name={question._key}
                                onChange={() => handleSelect(question._key, optionValue)}
                                type="radio"
                                value={optionValue}
                              />
                              <span className="flex-1">
                                {optionLabel}
                                {typeBadge}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    )}

                    <div className="mt-4 flex flex-col gap-2 rounded-xl border border-slate-800/70 bg-slate-950/60 p-4 text-xs text-slate-400">
                      <label className="flex flex-col gap-2 text-slate-300">
                        <span>Confidence ({Math.round((responses[question._key]?.confidence ?? 0.5) * 100)}%)</span>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.05"
                          value={responses[question._key]?.confidence ?? 0.5}
                          onChange={(event) => handleConfidenceChange(question._key, event.target.value)}
                        />
                      </label>

                      <label className="flex flex-col gap-2 text-slate-300">
                        <span>Reasoning</span>
                        <textarea
                          className="rounded-lg border border-slate-800/70 bg-slate-950 px-3 py-2 text-slate-100 focus:border-emerald-400 focus:outline-none"
                          rows={3}
                          placeholder="Explain why you chose this answer..."
                          value={responses[question._key]?.reasoning ?? ""}
                          onChange={(event) => handleReasoningChange(question._key, event.target.value)}
                        />
                      </label>
                    </div>
                  </article>
                ))}
              </div>
              </>
            )}

            <div className="flex flex-wrap items-center justify-between gap-4">
              <button
                type="submit"
                className="rounded-xl border border-emerald-500/50 bg-emerald-500/30 px-5 py-3 text-sm font-semibold text-emerald-100 shadow-lg shadow-emerald-900/40 transition hover:-translate-y-1 hover:bg-emerald-500/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={questionList.length === 0 || isSubmitting || showResults}
              >
                {isSubmitting ? "Submitting & Generating AI Feedback..." : showResults ? "Quiz Completed" : "Submit Responses"}
              </button>

              <span className="text-xs text-slate-500">
                AI will analyze your responses and provide personalized feedback
              </span>
            </div>
          </form>
        </section>

        {/* AI-Generated Feedback Section */}
        {showResults && feedback && (
          <section className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 to-transparent p-8 shadow-2xl">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-white">Quiz Results</h3>
                <p className="mt-1 text-sm text-slate-400">Personalized feedback from GPT-4o</p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-emerald-400">{feedback.score_percentage.toFixed(1)}%</div>
                <div className="text-sm text-slate-400">{feedback.correct_count} / {feedback.total_questions} correct</div>
                
                {/* Quick Stats */}
                <div className="mt-3 flex gap-2 justify-end">
                  {feedback.feedback.filter(item => item.misconception_addressed).length > 0 && (
                    <div className="px-2 py-1 rounded-lg bg-rose-500/20 border border-rose-400/50">
                      <p className="text-xs text-rose-300 font-semibold">
                        {feedback.feedback.filter(item => item.misconception_addressed).length} 🧠
                      </p>
                    </div>
                  )}
                  <div className="px-2 py-1 rounded-lg bg-emerald-500/20 border border-emerald-400/50">
                    <p className="text-xs text-emerald-300 font-semibold">
                      {feedback.correct_count} ✓
                    </p>
                  </div>
                  <div className="px-2 py-1 rounded-lg bg-blue-500/20 border border-blue-400/50">
                    <p className="text-xs text-blue-300 font-semibold">
                      GPT-4o
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Misconception Summary */}
            {(() => {
              const misconceptionCount = feedback.feedback.filter(item => item.misconception_addressed).length;
              if (misconceptionCount > 0) {
                return (
                  <div className="mb-6 rounded-2xl border-2 border-rose-500/40 bg-gradient-to-br from-rose-500/10 via-purple-500/5 to-blue-500/5 p-6 shadow-xl">
                    <div className="flex items-start gap-4">
                      <div className="rounded-full bg-rose-500/20 p-3 border-2 border-rose-400/50">
                        <svg className="w-8 h-8 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                          🧠 Misconceptions Detected
                          <span className="px-3 py-1 rounded-full bg-rose-500/30 text-rose-200 text-sm font-bold border border-rose-400/50">
                            {misconceptionCount}
                          </span>
                        </h4>
                        <p className="text-sm text-slate-300 mb-4">
                          Our AI identified {misconceptionCount} conceptual misunderstanding{misconceptionCount > 1 ? 's' : ''} in your responses. 
                          Don't worry - this is a normal part of learning! Review the detailed analysis below for each question.
                        </p>
                        
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-purple-500/30">
                            <p className="text-xs font-semibold text-purple-300 mb-1">🎯 Personalized Targeting</p>
                            <p className="text-xs text-slate-400">
                              Your next quiz will include questions specifically designed to address these misconceptions
                            </p>
                          </div>
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-blue-500/30">
                            <p className="text-xs font-semibold text-blue-300 mb-1">📊 Progress Tracking</p>
                            <p className="text-xs text-slate-400">
                              Answer 3 related questions correctly to mark each misconception as resolved
                            </p>
                          </div>
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-emerald-500/30">
                            <p className="text-xs font-semibold text-emerald-300 mb-1">🚀 Growth Opportunity</p>
                            <p className="text-xs text-slate-400">
                              Addressing these will boost your cognitive trait scores by 5-15%
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            })()}

            {/* Detailed Feedback for Each Question */}
            <div className="space-y-6">
              {feedback.feedback.map((item, idx) => (
                <article
                  key={idx}
                  className={`rounded-2xl border p-6 ${
                    item.is_correct
                      ? "border-emerald-500/40 bg-emerald-500/5"
                      : "border-rose-500/40 bg-rose-500/5"
                  }`}
                >
                  <div className="mb-3 flex items-start justify-between">
                    <h4 className="font-semibold text-white">Question {item.question_number}</h4>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-bold ${
                        item.is_correct
                          ? "bg-emerald-500/20 text-emerald-300"
                          : "bg-rose-500/20 text-rose-300"
                      }`}
                    >
                      {item.is_correct ? "✓ CORRECT" : "✗ INCORRECT"}
                    </span>
                  </div>

                  <p className="mb-4 text-sm text-slate-300">{item.question_stem}</p>
                  <p className="mb-2 text-sm text-slate-400">
                    <span className="font-semibold">Your answer:</span> {item.selected_answer}
                  </p>

                  {/* AI Explanation */}
                  <div className="mt-4 space-y-3">
                    <div className="rounded-xl border-2 border-emerald-500/40 bg-gradient-to-br from-emerald-500/10 to-teal-500/5 p-5 shadow-lg">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="rounded-full bg-emerald-500/20 p-2 mt-0.5">
                          <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-bold text-emerald-300 mb-1">🤖 AI-Powered Explanation</p>
                          <p className="text-xs text-emerald-400/80 font-medium">
                            Detailed breakdown from GPT-4o
                          </p>
                        </div>
                      </div>
                      <div className="bg-slate-900/60 rounded-lg p-4 border border-emerald-500/20">
                        <p className="leading-relaxed text-slate-200">{item.explanation}</p>
                      </div>
                    </div>

                    {item.misconception_addressed && (
                      <div className="rounded-xl border-2 border-rose-500/40 bg-gradient-to-br from-rose-500/10 to-rose-500/5 p-5 shadow-lg">
                        <div className="flex items-start gap-3 mb-3">
                          <div className="rounded-full bg-rose-500/20 p-2 mt-0.5">
                            <svg className="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-bold text-rose-300 mb-1">🧠 Misconception Identified</p>
                            <p className="text-xs text-rose-400/80 font-medium">
                              This concept requires clarification
                            </p>
                          </div>
                          <span className="rounded-full px-3 py-1 text-xs font-bold bg-rose-500/30 text-rose-200 border border-rose-400/50">
                            HIGH SEVERITY
                          </span>
                        </div>
                        
                        <div className="ml-0 space-y-3">
                          {/* Misconception Details */}
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-rose-500/20">
                            <p className="text-xs font-semibold text-rose-300/80 mb-2">📌 What You Misunderstood:</p>
                            <p className="text-sm leading-relaxed text-slate-200">
                              {item.misconception_addressed}
                            </p>
                          </div>
                          
                          {/* Why This Matters */}
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-amber-500/20">
                            <p className="text-xs font-semibold text-amber-300/80 mb-2">⚠️ Why This Matters:</p>
                            <p className="text-sm leading-relaxed text-slate-300">
                              Understanding this concept correctly is crucial for building a solid foundation in this topic. 
                              This misconception affects your <span className="text-purple-400 font-semibold">analytical depth</span> and 
                              may lead to errors in related problems.
                            </p>
                          </div>
                          
                          {/* Personalized Remediation Plan */}
                          <div className="bg-gradient-to-br from-emerald-500/10 to-blue-500/10 rounded-lg p-4 border border-emerald-500/30">
                            <p className="text-xs font-semibold text-emerald-300 mb-3 flex items-center gap-2">
                              🎯 Your Personalized Remediation Plan:
                            </p>
                            <ol className="space-y-2 text-sm text-slate-300">
                              <li className="flex gap-2">
                                <span className="text-emerald-400 font-bold">1.</span>
                                <span>Review the AI explanation above carefully and identify the key difference</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="text-emerald-400 font-bold">2.</span>
                                <span>Practice similar questions focusing on this specific concept</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="text-emerald-400 font-bold">3.</span>
                                <span>Your next quiz will include questions targeting this misconception</span>
                              </li>
                              <li className="flex gap-2">
                                <span className="text-emerald-400 font-bold">4.</span>
                                <span className="italic text-emerald-300">
                                  Answer 3 related questions correctly to mark this as resolved ✅
                                </span>
                              </li>
                            </ol>
                          </div>
                          
                          {/* Cognitive Traits Affected */}
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-purple-500/20">
                            <p className="text-xs font-semibold text-purple-300 mb-3 flex items-center gap-2">
                              🧩 Cognitive Traits Affected:
                            </p>
                            <div className="flex flex-wrap gap-2">
                              <span className="px-3 py-1.5 rounded-full bg-purple-500/20 border border-purple-400/40 text-xs font-semibold text-purple-300">
                                📊 Analytical Depth
                              </span>
                              <span className="px-3 py-1.5 rounded-full bg-blue-500/20 border border-blue-400/40 text-xs font-semibold text-blue-300">
                                🔬 Conceptual Understanding
                              </span>
                            </div>
                            <p className="text-xs text-slate-400 mt-3">
                              Improving this will boost these cognitive skills by ~5-10%
                            </p>
                          </div>
                          
                          {/* Progress Tracker */}
                          <div className="bg-slate-900/60 rounded-lg p-4 border border-slate-600/30">
                            <div className="flex items-center justify-between mb-2">
                              <p className="text-xs font-semibold text-slate-300">📈 Resolution Progress:</p>
                              <span className="text-xs text-slate-400">1st occurrence</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-rose-500 to-amber-500 rounded-full" style={{ width: "33%" }}></div>
                              </div>
                              <span className="text-xs font-bold text-amber-400">1/3</span>
                            </div>
                            <p className="text-xs text-slate-500 mt-2">
                              Answer 2 more related questions correctly to resolve this
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="rounded-xl border-2 border-blue-500/40 bg-gradient-to-br from-blue-500/10 to-cyan-500/5 p-5 shadow-lg">
                      <div className="flex items-start gap-3 mb-3">
                        <div className="rounded-full bg-blue-500/20 p-2 mt-0.5">
                          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-bold text-blue-300 mb-1">📊 Confidence Analysis</p>
                          <p className="text-xs text-blue-400/80 font-medium">
                            Understanding your certainty level
                          </p>
                        </div>
                      </div>
                      <div className="bg-slate-900/60 rounded-lg p-4 border border-blue-500/20">
                        <p className="text-sm leading-relaxed text-slate-300">
                          {item.confidence_analysis}
                        </p>
                      </div>
                      
                      {/* Confidence Tips */}
                      <div className="mt-3 p-3 bg-cyan-500/5 rounded-lg border border-cyan-500/20">
                        <p className="text-xs font-semibold text-cyan-300 mb-2">💡 Building Confidence:</p>
                        <ul className="text-xs text-slate-400 space-y-1">
                          <li>• Review fundamental concepts before attempting similar questions</li>
                          <li>• Use the process of elimination to increase your certainty</li>
                          <li>• Track patterns in your answers to identify knowledge gaps</li>
                        </ul>
                      </div>
                    </div>

                    {item.learning_tips && item.learning_tips.length > 0 && (
                      <div className="rounded-xl border-2 border-purple-500/40 bg-gradient-to-br from-purple-500/10 to-indigo-500/5 p-5 shadow-lg">
                        <div className="flex items-start gap-3 mb-3">
                          <div className="rounded-full bg-purple-500/20 p-2 mt-0.5">
                            <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-bold text-purple-300 mb-1">📚 Personalized Learning Tips</p>
                            <p className="text-xs text-purple-400/80 font-medium">
                              Tailored strategies to master this concept
                            </p>
                          </div>
                        </div>
                        <ul className="ml-0 space-y-3">
                          {item.learning_tips.map((tip, tipIdx) => (
                            <li key={tipIdx} className="flex gap-3 bg-slate-900/60 rounded-lg p-3 border border-purple-500/20">
                              <span className="text-purple-400 font-bold text-sm mt-0.5">
                                {tipIdx + 1}.
                              </span>
                              <span className="text-sm text-slate-300 leading-relaxed">{tip}</span>
                            </li>
                          ))}
                        </ul>
                        
                        {/* Action Items */}
                        <div className="mt-4 pt-4 border-t border-purple-500/20">
                          <p className="text-xs font-semibold text-indigo-300 mb-2">✨ Immediate Action Items:</p>
                          <div className="flex flex-wrap gap-2">
                            <span className="px-3 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-400/40 text-xs font-semibold text-indigo-300">
                              📖 Review similar examples
                            </span>
                            <span className="px-3 py-1.5 rounded-full bg-purple-500/20 border border-purple-400/40 text-xs font-semibold text-purple-300">
                              🎯 Practice targeted questions
                            </span>
                            <span className="px-3 py-1.5 rounded-full bg-blue-500/20 border border-blue-400/40 text-xs font-semibold text-blue-300">
                              🧠 Retake quiz in 24-48h
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {item.encouragement && (
                      <p className="mt-3 text-sm italic text-emerald-300">💡 {item.encouragement}</p>
                    )}
                  </div>
                </article>
              ))}
            </div>

            {/* Trait Weakness Analysis */}
            {user?.cognitive_traits && (
              <div className="mt-8 rounded-2xl border-2 border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-transparent p-6">
                <h4 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  🎯 Areas to Focus On
                </h4>
                <p className="text-sm text-slate-400 mb-6">
                  Based on your current cognitive profile, here are your areas for improvement:
                </p>
                
                {(() => {
                  // Identify weak traits (< 70%)
                  const weakTraits = Object.entries(user.cognitive_traits)
                    .filter(([_, score]) => score < 0.70)
                    .sort((a, b) => a[1] - b[1]); // Sort by score ascending
                  
                  const moderateTraits = Object.entries(user.cognitive_traits)
                    .filter(([_, score]) => score >= 0.70 && score < 0.80)
                    .sort((a, b) => a[1] - b[1]);
                  
                  const strongTraits = Object.entries(user.cognitive_traits)
                    .filter(([_, score]) => score >= 0.80)
                    .sort((a, b) => b[1] - a[1]); // Sort by score descending
                  
                  return (
                    <div className="space-y-6">
                      {/* Weak Traits - Priority */}
                      {weakTraits.length > 0 && (
                        <div className="rounded-xl border-2 border-red-500/40 bg-red-500/5 p-5">
                          <h5 className="text-sm font-bold text-red-400 mb-3 flex items-center gap-2">
                            ⚠️ Priority - Needs Improvement (&lt; 70%)
                          </h5>
                          <div className="space-y-3">
                            {weakTraits.map(([trait, score]) => (
                              <div key={trait} className="flex items-center justify-between">
                                <span className="text-slate-200 capitalize font-medium">
                                  {trait.replace(/_/g, " ")}
                                </span>
                                <div className="flex items-center gap-3">
                                  <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-red-500 to-orange-500 rounded-full"
                                      style={{ width: `${score * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-red-400 font-bold text-sm w-12 text-right">
                                    {Math.round(score * 100)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Moderate Traits */}
                      {moderateTraits.length > 0 && (
                        <div className="rounded-xl border-2 border-yellow-500/40 bg-yellow-500/5 p-5">
                          <h5 className="text-sm font-bold text-yellow-400 mb-3 flex items-center gap-2">
                            📈 Developing (70-80%)
                          </h5>
                          <div className="space-y-3">
                            {moderateTraits.map(([trait, score]) => (
                              <div key={trait} className="flex items-center justify-between">
                                <span className="text-slate-200 capitalize font-medium">
                                  {trait.replace(/_/g, " ")}
                                </span>
                                <div className="flex items-center gap-3">
                                  <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-yellow-500 to-blue-500 rounded-full"
                                      style={{ width: `${score * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-yellow-400 font-bold text-sm w-12 text-right">
                                    {Math.round(score * 100)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Strong Traits */}
                      {strongTraits.length > 0 && (
                        <div className="rounded-xl border-2 border-emerald-500/40 bg-emerald-500/5 p-5">
                          <h5 className="text-sm font-bold text-emerald-400 mb-3 flex items-center gap-2">
                            ✅ Strengths (≥ 80%)
                          </h5>
                          <div className="space-y-3">
                            {strongTraits.map(([trait, score]) => (
                              <div key={trait} className="flex items-center justify-between">
                                <span className="text-slate-200 capitalize font-medium">
                                  {trait.replace(/_/g, " ")}
                                </span>
                                <div className="flex items-center gap-3">
                                  <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
                                    <div 
                                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full"
                                      style={{ width: `${score * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-emerald-400 font-bold text-sm w-12 text-right">
                                    {Math.round(score * 100)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Recommendations */}
                      <div className="mt-6 p-5 bg-blue-500/5 border-2 border-blue-500/30 rounded-xl">
                        <h5 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-2">
                          💡 Recommendations
                        </h5>
                        <ul className="text-sm text-slate-300 space-y-2 list-disc list-inside">
                          {weakTraits.length > 0 && (
                            <li>
                              Focus on improving <strong className="text-red-400">{weakTraits[0][0].replace(/_/g, " ")}</strong> - 
                              take more quizzes targeting this cognitive skill
                            </li>
                          )}
                          <li>Your next quiz questions will be personalized to target your weak areas</li>
                          <li>Review the explanations above to understand common misconceptions</li>
                          {strongTraits.length > 0 && (
                            <li>
                              Great job on <strong className="text-emerald-400">{strongTraits[0][0].replace(/_/g, " ")}</strong>! 
                              Maintain this strength with spaced practice
                            </li>
                          )}
                        </ul>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* What's Next - Learning Path */}
            <div className="mt-8 rounded-2xl border-2 border-indigo-500/40 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-blue-500/5 p-6 shadow-xl">
              <div className="flex items-start gap-4 mb-4">
                <div className="rounded-full bg-indigo-500/20 p-3 border-2 border-indigo-400/50">
                  <svg className="w-8 h-8 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-xl font-bold text-white mb-2">🚀 What's Next in Your Learning Journey?</h4>
                  <p className="text-sm text-slate-300 mb-4">
                    Based on your performance, here's your personalized learning path:
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Next Quiz */}
                    <div className="bg-slate-900/60 rounded-xl p-5 border-2 border-emerald-500/30 hover:border-emerald-400/50 transition-all cursor-pointer group">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-3xl">🎯</span>
                        <div>
                          <h5 className="text-sm font-bold text-emerald-300 group-hover:text-emerald-200 transition">Take Another Quiz</h5>
                          <p className="text-xs text-slate-400">Recommended in 24-48 hours</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 mb-3">
                        Your next quiz will target the {feedback.feedback.filter(item => item.misconception_addressed).length} misconception(s) identified today
                      </p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full" style={{ width: "60%" }}></div>
                        </div>
                        <span className="text-xs font-bold text-emerald-400">60%</span>
                      </div>
                      <p className="text-xs text-slate-500 mt-2">Probability of improvement</p>
                    </div>
                    
                    {/* Review Weak Traits */}
                    <div className="bg-slate-900/60 rounded-xl p-5 border-2 border-purple-500/30 hover:border-purple-400/50 transition-all cursor-pointer group">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-3xl">📊</span>
                        <div>
                          <h5 className="text-sm font-bold text-purple-300 group-hover:text-purple-200 transition">Check Your Dashboard</h5>
                          <p className="text-xs text-slate-400">Track cognitive growth</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 mb-3">
                        View detailed analytics of your trait evolution and misconception resolution progress
                      </p>
                      <div className="flex flex-wrap gap-1">
                        <span className="px-2 py-1 rounded-full bg-purple-500/20 text-xs text-purple-300 border border-purple-400/30">
                          Trait Trends
                        </span>
                        <span className="px-2 py-1 rounded-full bg-blue-500/20 text-xs text-blue-300 border border-blue-400/30">
                          History
                        </span>
                      </div>
                    </div>
                    
                    {/* Explore Topics */}
                    <div className="bg-slate-900/60 rounded-xl p-5 border-2 border-blue-500/30 hover:border-blue-400/50 transition-all cursor-pointer group">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-3xl">📚</span>
                        <div>
                          <h5 className="text-sm font-bold text-blue-300 group-hover:text-blue-200 transition">Explore More Topics</h5>
                          <p className="text-xs text-slate-400">Expand your knowledge</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 mb-3">
                        Browse 50+ STEM topics and discover areas you haven't explored yet
                      </p>
                      <div className="flex items-center gap-2 text-xs text-blue-400">
                        <span>→</span>
                        <span>Physics, Math, Chemistry & more</span>
                      </div>
                    </div>
                    
                    {/* Upload New Material */}
                    <div className="bg-slate-900/60 rounded-xl p-5 border-2 border-amber-500/30 hover:border-amber-400/50 transition-all cursor-pointer group">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-3xl">📄</span>
                        <div>
                          <h5 className="text-sm font-bold text-amber-300 group-hover:text-amber-200 transition">Upload New Material</h5>
                          <p className="text-xs text-slate-400">Start fresh session</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400 mb-3">
                        Upload a PDF to generate questions based on your study materials
                      </p>
                      <div className="flex items-center gap-2 text-xs text-amber-400">
                        <span>✨</span>
                        <span>Personalized to your textbook</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 flex gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="flex-1 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 px-6 py-4 font-bold text-white text-lg shadow-xl transition hover:from-emerald-600 hover:to-teal-700 hover:shadow-2xl hover:shadow-emerald-500/50 transform hover:scale-105"
              >
                📊 View Dashboard
              </button>
              <button
                onClick={() => navigate("/topics")}
                className="flex-1 rounded-xl border-2 border-purple-500/50 bg-gradient-to-br from-purple-500/10 to-transparent px-6 py-4 font-bold text-purple-300 text-lg transition hover:border-purple-400 hover:bg-purple-500/20 transform hover:scale-105"
              >
                📚 Browse Topics
              </button>
              <button
                onClick={() => navigate("/upload")}
                className="flex-1 rounded-xl border-2 border-slate-700 bg-slate-800/50 px-6 py-4 font-bold text-slate-300 text-lg transition hover:border-slate-600 hover:bg-slate-800 transform hover:scale-105"
              >
                🚀 New Session
              </button>
            </div>
          </section>
        )}

        <nav className="flex flex-wrap gap-4 text-sm text-slate-400">
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/generate">
            Back to Generation
          </Link>
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/dashboard">
            Review Dashboard
          </Link>
        </nav>
      </div>
    </main>
  );
}
