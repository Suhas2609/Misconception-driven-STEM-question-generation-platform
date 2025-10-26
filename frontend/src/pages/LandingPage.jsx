import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuestionContext } from "../context/QuestionContext.jsx";

const generateUserId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `user-${Date.now()}-${Math.floor(Math.random() * 10_000)}`;
};

export default function LandingPage() {
  const navigate = useNavigate();
  const { userId, setUserId } = useQuestionContext();

  useEffect(() => {
    if (!userId) {
      setUserId(generateUserId());
    }
  }, [userId, setUserId]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 text-slate-100">
      <section className="mx-auto flex w-full max-w-5xl flex-col gap-12 px-6 py-20">
        <header className="rounded-3xl border border-slate-800/70 bg-slate-900/70 p-10 text-center shadow-xl shadow-slate-950/60 transition-all hover:shadow-2xl">
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Misconception-Driven STEM Platform</h1>
          <p className="mt-4 text-lg text-slate-300">
            Curate learning materials, surface misconceptions, and guide students with evidence-informed diagnostics.
          </p>
          <span className="mt-6 inline-flex items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-4 py-1 text-sm font-medium text-emerald-300">
            Active session: {userId || "initialising..."}
          </span>
        </header>

        <div className="grid gap-6 md:grid-cols-2">
          <button
            type="button"
            className="rounded-2xl border border-emerald-500/40 bg-emerald-500/20 px-8 py-6 text-lg font-semibold text-emerald-100 shadow-lg shadow-emerald-900/40 transition hover:-translate-y-1 hover:bg-emerald-500/30 hover:text-white hover:shadow-emerald-600/40"
            onClick={() => navigate("/upload")}
          >
            Start with PDF Upload
          </button>

          <Link
            className="flex items-center justify-center rounded-2xl border border-slate-700 bg-slate-900/60 px-8 py-6 text-lg font-semibold text-slate-200 shadow-lg shadow-slate-950/50 transition hover:-translate-y-1 hover:border-emerald-400/60 hover:text-emerald-200"
            to="/dashboard"
          >
            View Analytics Dashboard
          </Link>
        </div>

        <footer className="flex flex-wrap items-center justify-center gap-4 text-sm text-slate-400">
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/generate">
            Generate Questions
          </Link>
          <Link className="rounded-full border border-transparent px-3 py-1 transition hover:border-emerald-400 hover:text-emerald-300" to="/quiz">
            Learner Quiz Mode
          </Link>
        </footer>
      </section>
    </main>
  );
}
