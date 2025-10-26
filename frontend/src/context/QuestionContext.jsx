import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { uploadPdf } from "../api/pdfApi.js";
import { generateQuestion as generateQuestionApi } from "../api/questionApi.js";
import { submitResponse as submitResponseApi } from "../api/responseApi.js";
import { getUserTraits } from "../api/userApi.js";

const QuestionContext = createContext(null);

const getInitialUserId = () => {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem("user_id") || "";
};

export function QuestionProvider({ children }) {
  const [userId, setUserId] = useState(getInitialUserId);
  const [questions, setQuestions] = useState([]);
  const [traits, setTraits] = useState(null);
  const [uploadMeta, setUploadMeta] = useState({
    subject: "",
    gradeBand: "secondary",
    notes: "",
    filename: "",
    numChunks: 0,
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    if (userId) {
      window.localStorage.setItem("user_id", userId);
    } else {
      window.localStorage.removeItem("user_id");
    }
  }, [userId]);

  const resetSession = useCallback(() => {
    setQuestions([]);
    setTraits(null);
    setUploadMeta({
      subject: "",
      gradeBand: "secondary",
      notes: "",
      filename: "",
      numChunks: 0,
    });
  }, []);

  const uploadMaterial = useCallback(
    async ({ file, subject, gradeBand, notes }) => {
      if (!file) {
        throw new Error("PDF or slide deck file is required");
      }

      // Forward subject as topic and include the userId so backend can tie questions
      const result = await uploadPdf(file, { userId, topic: subject, num_questions: 3 });
      if (Array.isArray(result?.questions)) {
        setQuestions(result.questions);
      }
      setUploadMeta({
        subject,
        gradeBand,
        notes,
        filename: file.name,
        numChunks: result?.num_chunks ?? 0,
      });
      return result;
    },
    [setQuestions, userId]
  );

  const generateQuestion = useCallback(
    async ({ topic, factualContext, misconceptions }) => {
      if (!userId) {
        throw new Error("User ID missing. Refresh or revisit the landing page to initialise session.");
      }

      const payload = {
        user_id: userId,
        topic,
        factual_context: factualContext,
        misconceptions,
        traits: traits || undefined,
      };

      const question = await generateQuestionApi(payload);
      setQuestions((prev) => [...prev, question]);
      return question;
    },
    [traits, userId]
  );

  const submitResponse = useCallback(
    async ({ questionId, selectedOption, confidence, reasoning }) => {
      if (!userId) {
        throw new Error("User ID missing. Refresh or revisit the landing page to initialise session.");
      }

      const response = await submitResponseApi({
        user_id: userId,
        question_id: questionId,
        selected_option: selectedOption,
        confidence,
        reasoning,
      });

      if (response?.traits) {
        setTraits(response.traits);
      }

      return response;
    },
    [userId]
  );

  const refreshTraits = useCallback(
    async (overrideUserId) => {
      const resolvedId = overrideUserId || userId;
      if (!resolvedId) {
        return null;
      }

      const updatedTraits = await getUserTraits(resolvedId);
      setTraits(updatedTraits);
      return updatedTraits;
    },
    [userId]
  );

  const value = useMemo(
    () => ({
      userId,
      setUserId,
      questions,
      setQuestions,
      traits,
      setTraits,
      uploadMeta,
      setUploadMeta,
      resetSession,
      uploadMaterial,
      generateQuestion,
      submitResponse,
      refreshTraits,
    }),
    [
      userId,
      questions,
      traits,
      uploadMeta,
      resetSession,
      uploadMaterial,
      generateQuestion,
      submitResponse,
      refreshTraits,
    ]
  );

  return <QuestionContext.Provider value={value}>{children}</QuestionContext.Provider>;
}

export function useQuestionContext() {
  const context = useContext(QuestionContext);

  if (!context) {
    throw new Error("useQuestionContext must be used within a QuestionProvider");
  }

  return context;
}
