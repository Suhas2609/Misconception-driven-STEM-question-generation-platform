import { useMemo, useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { extractErrorMessage } from "../api/client.js";
import { useQuestionContext } from "../context/QuestionContext.jsx";
import { submitQuizWithFeedback } from "../api/pdfApi.js";

export default function QuizPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { questions: contextQuestions, submitResponse } = useQuestionContext();
  
  // Get questions and session ID from navigation state
  const questionsFromState = location.state?.questions || [];
  const sessionId = location.state?.sessionId;
  const allQuestions = questionsFromState.length > 0 ? questionsFromState : contextQuestions;
  
  const [responses, setResponses] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);  // Store AI feedback
  const [showResults, setShowResults] = useState(false);  // Toggle results view

  useEffect(() => {
    if (questionsFromState.length > 0) {
      console.log("📝 Loaded", questionsFromState.length, "questions from navigation state");
    }
  }, [questionsFromState.length]);

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
              <div className="space-y-6">
                {questionList.map((question) => (
                  <article
                    key={question._key}
                    className="rounded-2xl border border-slate-800/80 bg-slate-950/60 p-6 shadow-inner transition hover:border-emerald-400/40"
                  >
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
              </div>
            </div>

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
                    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
                      <p className="text-sm font-semibold text-emerald-300">AI Explanation</p>
                      <p className="mt-2 leading-relaxed text-slate-200">{item.explanation}</p>
                    </div>

                    {item.misconception_addressed && (
                      <div className="rounded-xl border border-rose-500/30 bg-rose-500/5 p-4">
                        <p className="text-sm font-semibold text-rose-300">Misconception Identified</p>
                        <p className="mt-2 text-sm leading-relaxed text-slate-300">
                          {item.misconception_addressed}
                        </p>
                      </div>
                    )}

                    <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
                      <p className="text-sm font-semibold text-blue-300">Confidence Analysis</p>
                      <p className="mt-2 text-sm leading-relaxed text-slate-300">
                        {item.confidence_analysis}
                      </p>
                    </div>

                    {item.learning_tips && item.learning_tips.length > 0 && (
                      <div className="rounded-xl border border-slate-700/50 bg-slate-900/50 p-4">
                        <p className="text-sm font-semibold text-purple-300">Learning Tips</p>
                        <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-300">
                          {item.learning_tips.map((tip, tipIdx) => (
                            <li key={tipIdx}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {item.encouragement && (
                      <p className="mt-3 text-sm italic text-emerald-300">💡 {item.encouragement}</p>
                    )}
                  </div>
                </article>
              ))}
            </div>

            <div className="mt-8 flex gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="flex-1 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-6 py-3 font-semibold text-white shadow-lg transition hover:from-emerald-600 hover:to-emerald-700"
              >
                View Updated Dashboard →
              </button>
              <button
                onClick={() => navigate("/upload")}
                className="flex-1 rounded-xl border border-slate-700 bg-slate-800/50 px-6 py-3 font-semibold text-slate-300 transition hover:border-slate-600 hover:bg-slate-800"
              >
                Start New Session
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
