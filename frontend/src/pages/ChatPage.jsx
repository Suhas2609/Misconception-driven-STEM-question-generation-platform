import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "react-hot-toast";
import { useQuestionContext } from "../context/QuestionContext.jsx";
import { extractErrorMessage } from "../api/client.js";

const createId = (prefix) => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10_000)}`;
};

const initialAssistantMessage = {
  id: createId("assistant"),
  role: "assistant",
  type: "text",
  content:
    "Hi! Share a PDF so I can ground the quiz generator, or just ask me to build a misconception-aware question.",
};

function TraitBadge({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-700/60 bg-slate-900/70 px-3 py-2 text-xs text-slate-200 shadow-sm shadow-slate-950/40">
      <span className="font-semibold text-slate-100">{label}: </span>
      <span className="font-mono text-emerald-300">{value?.toFixed(2) ?? "--"}</span>
    </div>
  );
}

function MessageBubble({ message, onSelectOption }) {
  const alignment = message.role === "user" ? "items-end" : "items-start";
  const bubbleBase =
    message.role === "user"
      ? "bg-emerald-500/80 text-slate-900"
      : "bg-slate-800/80 text-slate-100 border border-slate-700/70";

  if (message.type === "question") {
    const { question, isSubmitting, answered, selectedOption, answerFeedback } = message;
    return (
      <li className={`flex flex-col gap-3 ${alignment}`}>
        <div className={`max-w-2xl rounded-3xl ${bubbleBase} px-5 py-4 shadow-lg shadow-slate-950/50`}>
          <p className="text-base font-semibold leading-relaxed">{question.stem}</p>
          <div className="mt-4 space-y-2">
            {question.options.map((option) => {
              const isSelected = selectedOption === option.text;
              const isCorrect = option.type === "correct";
              let optionClass = "border border-slate-700/60 bg-slate-900/60 hover:border-emerald-400/60";

              if (answered) {
                if (isSelected && isCorrect) {
                  optionClass = "border-emerald-500/80 bg-emerald-500/20";
                } else if (isSelected && !isCorrect) {
                  optionClass = "border-rose-500/80 bg-rose-500/20";
                } else if (isCorrect) {
                  optionClass = "border-emerald-400/70 bg-emerald-500/10";
                }
              }

              return (
                <button
                  key={option.text}
                  type="button"
                  disabled={isSubmitting || answered}
                  onClick={() => onSelectOption(message.id, option)}
                  className={`w-full rounded-2xl px-4 py-3 text-left text-sm transition focus:outline-none focus:ring-2 focus:ring-emerald-400/60 disabled:cursor-not-allowed disabled:opacity-70 ${optionClass}`}
                >
                  <span className="block font-medium text-slate-100">{option.text}</span>
                  <span className="mt-1 block text-xs uppercase tracking-wide text-slate-400">{option.type}</span>
                </button>
              );
            })}
          </div>
          {isSubmitting && <p className="mt-3 text-sm text-slate-300">Scoring your response…</p>}
          {answerFeedback && <p className="mt-3 text-sm text-emerald-300">{answerFeedback}</p>}
        </div>
      </li>
    );
  }

  return (
    <li className={`flex ${alignment}`}>
      <div className={`max-w-2xl whitespace-pre-line rounded-3xl ${bubbleBase} px-5 py-4 text-sm leading-relaxed shadow-md shadow-slate-950/40`}>
        {message.content}
      </div>
    </li>
  );
}

export default function ChatPage() {
  const {
    userId,
    uploadMaterial,
    generateQuestion,
    submitResponse,
    refreshTraits,
    traits,
    uploadMeta,
    setQuestions,
  } = useQuestionContext();

  const [messages, setMessages] = useState([initialAssistantMessage]);
  const [promptInput, setPromptInput] = useState("");
  const [pendingUpload, setPendingUpload] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    if (!userId) {
      return;
    }

    refreshTraits(userId).catch(() => {
      /* let chat flow continue even if trait refresh fails */
    });
  }, [userId, refreshTraits]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const traitBadges = useMemo(() => {
    if (!traits) {
      return null;
    }

    return Object.entries(traits).map(([key, value]) => (
      <TraitBadge key={key} label={key} value={Number(value)} />
    ));
  }, [traits]);

  const appendMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const replaceMessage = (messageId, nextMessage) => {
    setMessages((prev) => prev.map((msg) => (msg.id === messageId ? { ...msg, ...nextMessage } : msg)));
  };

  const handlePromptSubmit = async (event) => {
    event.preventDefault();
    const topic = promptInput.trim();
    if (!topic) {
      toast.error("Ask a question or describe the concept you want to probe.");
      return;
    }

    const userMessage = {
      id: createId("user"),
      role: "user",
      type: "text",
      content: topic,
    };
    appendMessage(userMessage);
    setPromptInput("");

    const statusId = createId("assistant");
    appendMessage({
      id: statusId,
      role: "assistant",
      type: "text",
      content: "Shaping a misconception-aware question…",
    });
    setIsGenerating(true);

    try {
      const question = await generateQuestion({
        topic,
        factualContext: undefined,
        misconceptions: undefined,
      });

      setQuestions((prev) => [...prev, question]);

      replaceMessage(statusId, {
        type: "question",
        question,
        isSubmitting: false,
        answered: false,
        selectedOption: null,
        answerFeedback: null,
      });
    } catch (error) {
      const message = extractErrorMessage(error, "Unable to generate a question");
      replaceMessage(statusId, {
        type: "text",
        content: message,
      });
      toast.error(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    setPendingUpload({
      file,
      subject: "",
      gradeBand: "secondary",
      notes: "",
    });
  };

  const cancelPendingUpload = () => {
    setPendingUpload(null);
  };

  const confirmUpload = async () => {
    if (!pendingUpload?.file) {
      return;
    }

    const { file, subject, gradeBand, notes } = pendingUpload;
    if (!subject.trim()) {
      toast.error("Please provide a topic or subject focus before uploading.");
      return;
    }

    const userMessage = {
      id: createId("user"),
      role: "user",
      type: "text",
      content: `Uploaded “${file.name}” to focus on ${subject}.`,
    };
    appendMessage(userMessage);

    const statusId = createId("assistant");
    appendMessage({
      id: statusId,
      role: "assistant",
      type: "text",
      content: "Digesting the document and extracting misconceptions…",
    });

    setIsUploading(true);
    try {
      const result = await uploadMaterial({ file, subject, gradeBand, notes });
      const chunkInfo = result?.num_chunks ?? 0;
      const generated = Array.isArray(result?.questions) ? result.questions : [];

      setQuestions(generated);

      const summaryLines = [
        `Ingested “${result?.filename || file.name}” with ${chunkInfo} high-value chunks.`,
      ];

      if (generated.length > 0) {
        summaryLines.push(`Generated ${generated.length} draft question${generated.length > 1 ? "s" : ""}.`);
      }

      replaceMessage(statusId, {
        type: "text",
        content: summaryLines.join("\n"),
      });

      generated.forEach((question) => {
        appendMessage({
          id: createId("assistant"),
          role: "assistant",
          type: "question",
          question,
          isSubmitting: false,
          answered: false,
          selectedOption: null,
          answerFeedback: null,
        });
      });

      toast.success("Upload processed successfully.");
      setPendingUpload(null);
    } catch (error) {
      const message = extractErrorMessage(error, "Failed to process the upload");
      replaceMessage(statusId, {
        type: "text",
        content: message,
      });
      toast.error(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleOptionSelect = async (messageId, option) => {
    const targetMessage = messages.find((item) => item.id === messageId);
    if (!targetMessage?.question) {
      toast.error("Question payload missing identifier.");
      return;
    }

    setMessages((prev) =>
      prev.map((message) =>
        message.id === messageId
          ? { ...message, isSubmitting: true, selectedOption: option.text }
          : message
      )
    );

    try {
      if (!targetMessage.question.id) {
        throw new Error("Question payload missing identifier.");
      }

      const response = await submitResponse({
        questionId: targetMessage.question.id,
        selectedOption: option.text,
        confidence: 0.75,
        reasoning: "chat-selection",
      });

      setMessages((prev) =>
        prev.map((item) =>
          item.id === messageId
            ? {
                ...item,
                isSubmitting: false,
                answered: true,
                answerFeedback: option.type === "correct"
                  ? "Great pick — that aligns perfectly with the evidence."
                  : "Thanks for the attempt. I’ll adapt the next probe to address this misconception.",
              }
            : item
        )
      );

      if (response?.traits) {
        const traitSummary = Object.entries(response.traits)
          .map(([trait, value]) => `${trait}: ${(Number(value) || 0).toFixed(2)}`)
          .join("\n");

        appendMessage({
          id: createId("assistant"),
          role: "assistant",
          type: "text",
          content: `Updated learner traits based on that response:\n${traitSummary}`,
        });
      }
    } catch (error) {
      const message = extractErrorMessage(error, "Unable to score the response");
      setMessages((prev) =>
        prev.map((item) =>
          item.id === messageId
            ? { ...item, isSubmitting: false, answered: false, answerFeedback: message }
            : item
        )
      );
      toast.error(message);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-6">
          <div>
            <h1 className="text-2xl font-semibold">Adaptive Misconception Tutor</h1>
            <p className="mt-1 text-sm text-slate-400">Session: {userId || "initialising…"}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">{traitBadges}</div>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-6 md:px-8">
        <ul className="flex flex-1 flex-col gap-4 overflow-y-auto pb-4">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onSelectOption={handleOptionSelect} />
          ))}
          <li ref={endOfMessagesRef} />
        </ul>
      </main>

      <footer className="border-t border-slate-800 bg-slate-950/80">
        <div className="mx-auto w-full max-w-4xl px-4 py-6 md:px-8">
          {pendingUpload ? (
            <div className="mb-4 rounded-3xl border border-emerald-500/40 bg-emerald-500/10 p-5 shadow-lg shadow-emerald-900/30">
              <h2 className="text-sm font-semibold text-emerald-200">Prepare upload</h2>
              <p className="mt-1 text-xs text-emerald-100/80">{pendingUpload.file.name}</p>
              <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
                <input
                  type="text"
                  className="flex-1 rounded-2xl border border-emerald-500/40 bg-slate-950/80 px-4 py-2 text-sm text-slate-100 focus:border-emerald-400/60 focus:outline-none"
                  placeholder="What concept or subject should we emphasise?"
                  value={pendingUpload.subject}
                  onChange={(event) =>
                    setPendingUpload((prev) => ({ ...prev, subject: event.target.value }))
                  }
                />
                <select
                  className="rounded-2xl border border-emerald-500/40 bg-slate-950/80 px-4 py-2 text-sm text-slate-100 focus:border-emerald-400/60 focus:outline-none"
                  value={pendingUpload.gradeBand}
                  onChange={(event) =>
                    setPendingUpload((prev) => ({ ...prev, gradeBand: event.target.value }))
                  }
                >
                  <option value="primary">Primary</option>
                  <option value="secondary">Secondary</option>
                  <option value="higher">Higher Ed</option>
                </select>
              </div>
              <textarea
                className="mt-3 w-full rounded-2xl border border-emerald-500/40 bg-slate-950/80 px-4 py-2 text-sm text-slate-100 focus:border-emerald-400/60 focus:outline-none"
                rows={3}
                placeholder="Any guidance or specific misconceptions to watch for?"
                value={pendingUpload.notes}
                onChange={(event) =>
                  setPendingUpload((prev) => ({ ...prev, notes: event.target.value }))
                }
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-2xl border border-emerald-400/60 bg-emerald-500/20 px-4 py-2 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30"
                  onClick={confirmUpload}
                  disabled={isUploading}
                >
                  {isUploading ? "Uploading…" : "Confirm upload"}
                </button>
                <button
                  type="button"
                  className="rounded-2xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-sm text-slate-300 transition hover:border-rose-400/50 hover:text-rose-200"
                  onClick={cancelPendingUpload}
                  disabled={isUploading}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : null}

          <div className="flex flex-col gap-3 rounded-3xl border border-slate-800/80 bg-slate-900/70 p-4 shadow-xl shadow-slate-950/40">
            <div className="flex items-center gap-3">
              <label className="relative inline-flex h-11 w-11 cursor-pointer items-center justify-center rounded-2xl border border-slate-700/70 bg-slate-900/80 text-slate-300 transition hover:border-emerald-400/60 hover:text-emerald-200">
                <input
                  type="file"
                  accept="application/pdf"
                  className="absolute inset-0 cursor-pointer opacity-0"
                  onChange={handleFileChange}
                />
                <span className="text-lg">📎</span>
              </label>
              <form onSubmit={handlePromptSubmit} className="flex-1">
                <div className="flex flex-col gap-3 md:flex-row md:items-center">
                  <input
                    type="text"
                    value={promptInput}
                    onChange={(event) => setPromptInput(event.target.value)}
                    placeholder={
                      uploadMeta?.subject
                        ? `Ask about ${uploadMeta.subject} or request a new probe…`
                        : "Ask for misconception-targeted practice…"
                    }
                    className="flex-1 rounded-2xl border border-slate-700/70 bg-slate-950/80 px-4 py-3 text-sm text-slate-100 focus:border-emerald-400/60 focus:outline-none"
                    disabled={isGenerating || isUploading}
                  />
                  <button
                    type="submit"
                    className="rounded-2xl bg-emerald-500/80 px-6 py-3 text-sm font-semibold text-slate-900 shadow-lg shadow-emerald-900/40 transition hover:bg-emerald-400"
                    disabled={isGenerating || isUploading}
                  >
                    {isGenerating ? "Generating…" : "Send"}
                  </button>
                </div>
              </form>
            </div>
            <p className="text-xs text-slate-400">
              I’ll keep the conversation grounded in the uploaded material and continuously refine the learner profile in the background.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
