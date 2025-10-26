import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { uploadPDF } from "../api/pdfApi";
import { useAuth } from "../context/AuthContext";

export default function UploadPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        setFile(droppedFile);
      } else {
        toast.error("Please upload a PDF file");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === "application/pdf") {
        setFile(selectedFile);
      } else {
        toast.error("Please select a PDF file");
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a PDF file first");
      return;
    }

    setUploading(true);
    setProcessingStatus("Uploading PDF...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      console.log("📤 Starting PDF upload...", file.name);
      setProcessingStatus("Extracting text from PDF...");
      
      const result = await uploadPDF(formData);
      
      console.log("✅ Upload successful:", result);
      setProcessingStatus("Analyzing content with GPT-4o...");
      
      setTimeout(() => {
        toast.success(`Successfully extracted ${result.topics?.length || 0} topics!`);
        // Navigate to topic selection page
        navigate(`/topics`, { 
          state: { 
            sessionData: {
              session_id: result.session_id,
              topics: result.topics, 
              filename: file.name,
              document_summary: result.document_summary
            }
          } 
        });
      }, 1000);

    } catch (error) {
      console.error("❌ Upload error:", error);
      console.error("Error details:", {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status
      });
      
      const errorMessage = error.response?.data?.detail 
        || error.message 
        || "Failed to upload PDF";
      
      toast.error(errorMessage);
      setProcessingStatus(null);
      setUploading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 px-6 py-16 text-slate-100">
      <div className="mx-auto max-w-4xl">
        {/* Header */}
        <header className="mb-10 text-center">
          <h1 className="text-4xl font-bold text-white mb-3">Upload Study Material</h1>
          <p className="text-gray-400 text-lg">
            Upload a PDF textbook, paper, or notes to generate personalized practice questions
          </p>
          {user && (
            <p className="text-sm text-gray-500 mt-2">
              Logged in as: <span className="text-teal-400">{user.email}</span>
            </p>
          )}
        </header>

        {/* Upload Section */}
        <section className="rounded-2xl border border-slate-700 bg-gray-800/90 p-8 shadow-xl mb-6">
          {/* Drag & Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all ${
              dragActive
                ? "border-teal-500 bg-teal-500/10"
                : "border-gray-600 bg-gray-900/50"
            } ${file ? "border-green-500 bg-green-500/10" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept="application/pdf"
              onChange={handleFileChange}
              disabled={uploading}
            />

            {!file ? (
              <div className="space-y-4">
                <div className="text-6xl">📄</div>
                <div>
                  <p className="text-xl font-semibold text-white mb-2">
                    Drop your PDF here
                  </p>
                  <p className="text-gray-400 mb-4">or</p>
                  <label
                    htmlFor="file-upload"
                    className="inline-block px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg cursor-pointer transition"
                  >
                    Browse Files
                  </label>
                </div>
                <p className="text-sm text-gray-500">
                  Supported: PDF files up to 50MB
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-6xl">✅</div>
                <div>
                  <p className="text-xl font-semibold text-green-400 mb-2">
                    {file.name}
                  </p>
                  <p className="text-gray-400 text-sm">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {!uploading && (
                    <button
                      onClick={() => setFile(null)}
                      className="mt-4 text-sm text-gray-400 hover:text-red-400 transition"
                    >
                      Remove file
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {file && !uploading && (
            <button
              onClick={handleUpload}
              className="mt-6 w-full px-6 py-4 bg-teal-600 hover:bg-teal-700 text-white text-lg font-semibold rounded-xl transition shadow-lg"
            >
              Process & Extract Topics with AI
            </button>
          )}

          {/* Processing Status */}
          {uploading && processingStatus && (
            <div className="mt-6 p-4 bg-blue-900/30 border border-blue-500/50 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent"></div>
                <p className="text-blue-300 font-medium">{processingStatus}</p>
              </div>
            </div>
          )}
        </section>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="rounded-xl border border-slate-700 bg-gray-800/70 p-6">
            <div className="text-3xl mb-3">🧠</div>
            <h3 className="text-lg font-semibold text-white mb-2">AI Topic Extraction</h3>
            <p className="text-sm text-gray-400">
              GPT-4o analyzes your document and identifies key STEM concepts and topics
            </p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-gray-800/70 p-6">
            <div className="text-3xl mb-3">🎯</div>
            <h3 className="text-lg font-semibold text-white mb-2">Personalized Questions</h3>
            <p className="text-sm text-gray-400">
              Questions adapted to your cognitive profile and the document's content
            </p>
          </div>

          <div className="rounded-xl border border-slate-700 bg-gray-800/70 p-6">
            <div className="text-3xl mb-3">💡</div>
            <h3 className="text-lg font-semibold text-white mb-2">Misconception-Aware</h3>
            <p className="text-sm text-gray-400">
              Practice with distractors based on common student misconceptions
            </p>
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-8 text-center">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-gray-400 hover:text-teal-400 transition"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </main>
  );
}
