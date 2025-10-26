import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "react-hot-toast";
import { extractErrorMessage } from "../api/client.js";
import { useQuestionContext } from "../context/QuestionContext.jsx";

export default function GeneratePage() {
  const { traits, questions, uploadMeta, generateQuestion } = useQuestionContext();
  const [topic, setTopic] = useState(uploadMeta.subject ?? "");
  const [factualContext, setFactualContext] = useState("");
  const [misconceptionsText, setMisconceptionsText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const traitEntries = traits ? Object.entries(traits) : [];

  const handleGenerate = async (event) => {
    event.preventDefault();
    if (!topic.trim()) {
      toast.error("Topic is required to generate a question.");
      return;
    }

    const misconceptions = misconceptionsText
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    try {
      setIsSubmitting(true);
      const question = await generateQuestion({
        topic: topic.trim(),
        factualContext: factualContext.trim() || null,
        misconceptions,
      });

      toast.success(`Generated question on ${question.topic}`);
      setMisconceptionsText("");
    } catch (error) {
      toast.error(extractErrorMessage(error, "Failed to generate question"));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-16 text-slate-100">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-10">
        <header className="rounded-2xl border border-slate-800 bg-slate-900/70 p-8 shadow-xl shadow-slate-950/50">
          <h2 className="text-3xl font-semibold">Generate Diagnostic Questions</h2>
          <p className="mt-2 text-slate-400">
            Provide a topic and optional context to create targeted misconceptions and question prompts. Upload metadata
            pre-fills the topic when available.
          </p>
          {uploadMeta.filename && (
            <p className="mt-4 text-xs text-slate-500">
              Last upload: {uploadMeta.filename} ({uploadMeta.numChunks} processed excerpt{uploadMeta.numChunks === 1 ? "" : "s"})
            </p>
          )}
        </header>

        <section className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-8 shadow-lg shadow-slate-950/50 transition hover:-translate-y-1 hover:shadow-2xl">
          <form className="space-y-6" onSubmit={handleGenerate}>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="flex flex-col gap-2">
                <span className="text-sm font-medium text-slate-200">Topic</span>
                <input
                  className="rounded-xl border border-slate-700/70 bg-slate-950 px-4 py-3 text-slate-100 shadow-inner focus:border-emerald-400 focus:outline-none"
                  placeholder="e.g. Energy conservation"
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                  required
                />
              </label>

              <label className="flex flex-col gap-2">
                <span className="text-sm font-medium text-slate-200">Misconceptions (one per line)</span>
                <textarea
                  className="min-h-[120px] rounded-xl border border-slate-700/70 bg-slate-950 px-4 py-3 text-slate-100 shadow-inner focus:border-emerald-400 focus:outline-none"
                  placeholder="Objects in orbit experience no gravity."
                  value={misconceptionsText}
                  onChange={(event) => setMisconceptionsText(event.target.value)}
                />
              </label>
            </div>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-medium text-slate-200">Factual Context (optional)</span>
              <textarea
                className="min-h-[140px] rounded-xl border border-slate-700/70 bg-slate-950 px-4 py-3 text-slate-100 shadow-inner focus:border-emerald-400 focus:outline-none"
                placeholder="Paste relevant textbook excerpts or lab notes..."
                value={factualContext}
                onChange={(event) => setFactualContext(event.target.value)}
              />
            </label>

            <div className="flex flex-wrap items-center gap-4">
              <button
                type="submit"
                className="rounded-xl border border-emerald-500/50 bg-emerald-500/30 px-5 py-3 text-sm font-semibold text-emerald-100 shadow-lg shadow-emerald-900/40 transition hover:-translate-y-1 hover:bg-emerald-500/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Generating..." : "Generate Question"}
              </button>
              <span className="text-xs text-slate-500">The generator merges context with the curated misconception library.</span>
            </div>
          </form>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <article className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-6 shadow-lg shadow-slate-950/50 transition hover:-translate-y-1 hover:shadow-2xl">
            <h3 className="text-xl font-medium text-emerald-300">Current Trait Signature</h3>
            {traitEntries.length === 0 ? (
              <p className="mt-4 text-sm text-slate-400">No trait updates yet. Submit quiz responses to view analytics.</p>
            ) : (
              <ul className="mt-4 grid gap-3">
                {traitEntries.map(([key, value]) => (
                  <li
                    key={key}
                    className="flex items-center justify-between rounded-xl border border-slate-800/60 bg-slate-950/60 px-4 py-3 text-sm text-slate-100"
                  >
                    <span className="uppercase tracking-wide text-xs text-slate-400">{key}</span>
                    <span className="text-emerald-200">{(value * 100).toFixed(0)}%</span>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <article className="rounded-2xl border border-slate-800/80 bg-slate-900/70 p-6 shadow-lg shadow-slate-950/50 transition hover:-translate-y-1 hover:shadow-2xl">
            <h3 className="text-xl font-medium text-emerald-300">Generated Questions</h3>
            {questions.length === 0 ? (
              <p className="mt-4 text-sm text-slate-400">Generated questions will appear here.</p>
            ) : (
              <ol className="mt-4 space-y-4 text-sm text-slate-200">
                {questions.map((question) => (
                  <li
                    key={question.id || question.stem}
                    className="rounded-xl border border-slate-800/70 bg-slate-950/60 p-4 shadow-inner"
                  >
                    <p className="font-semibold text-slate-100">{question.stem}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
                      Difficulty: {question.difficulty || "n/a"}
                    </p>
                    {question.options?.length > 0 && (
                      <ul className="ml-4 mt-2 list-disc space-y-1 text-slate-300">
                        {question.options.map((option, idx) => (
                          <li key={`${question.id || question.stem}-option-${idx}`}>
                            <span className="font-medium text-emerald-200">{option.type}:</span> {option.text}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </article>
        </section>

        <nav className="flex flex-wrap gap-4 text-sm text-slate-400">
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/quiz">
            Launch Quiz Mode
          </Link>
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/dashboard">
            Review Dashboard
          </Link>
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/">
            Back to Landing
          </Link>
        </nav>
      </div>
    </main>
  );
}
