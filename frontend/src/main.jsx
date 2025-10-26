import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import App from "./App.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import { QuestionProvider } from "./context/QuestionContext.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <QuestionProvider>
          <App />
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#0f172a",
                color: "#e2e8f0",
                border: "1px solid #1e293b",
              },
            }}
          />
        </QuestionProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
