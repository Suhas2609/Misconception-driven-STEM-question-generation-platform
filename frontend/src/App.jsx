import { Navigate, Route, Routes } from "react-router-dom";
import AssessmentPage from "./pages/AssessmentPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import GeneratePage from "./pages/GeneratePage.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import QuizPage from "./pages/QuizPage.jsx";
import UploadPage from "./pages/UploadPage.jsx";
import TopicSelectionPage from "./pages/TopicSelectionPage.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<LoginPage />} path="/login" />
      <Route element={<RegisterPage />} path="/register" />
      
      <Route
        element={
          <ProtectedRoute>
            <AssessmentPage />
          </ProtectedRoute>
        }
        path="/assessment"
      />
      <Route
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
        path="/chat"
      />
      <Route
        element={
          <ProtectedRoute>
            <TopicSelectionPage />
          </ProtectedRoute>
        }
        path="/topics"
      />
      <Route element={<LandingPage />} path="/classic" />
      <Route
        element={
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        }
        path="/upload"
      />
      <Route
        element={
          <ProtectedRoute>
            <GeneratePage />
          </ProtectedRoute>
        }
        path="/generate"
      />
      <Route
        element={
          <ProtectedRoute>
            <QuizPage />
          </ProtectedRoute>
        }
        path="/quiz"
      />
      <Route
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
        path="/dashboard"
      />
      <Route
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
        path="/"
      />
      <Route element={<Navigate replace to="/login" />} path="*" />
    </Routes>
  );
}
