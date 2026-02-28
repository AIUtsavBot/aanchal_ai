import React, { useState, useEffect, useRef } from "react";
import {
  FileText,
  Upload,
  Loader,
  ExternalLink,
  AlertCircle,
  CheckCircle,
  Trash2,
  Eye,
  RefreshCw,
  User,
  Clock,
  Zap,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function DocumentManager({
  motherId,
  motherName,
  uploaderId,
  uploaderRole,
  uploaderName,
}) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(null); // Track which document is being deleted
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fileInputRef = useRef(null);

  // Check if current user is a doctor (can delete)
  const isDoctor = uploaderRole?.toUpperCase() === "DOCTOR";

  useEffect(() => {
    let isMounted = true;

    const fetchDocuments = async () => {
      if (!motherId) return;

      setLoading(true);
      setError("");
      try {
        const response = await fetch(`${API_URL}/reports/${motherId}`);
        if (!response.ok) throw new Error("Failed to load documents");
        const data = await response.json();
        if (isMounted) {
          setDocuments(data.data || []);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Error loading documents:", err);
          setError("Failed to load documents");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDocuments();

    return () => {
      isMounted = false;
    };
  }, [motherId]);

  const loadDocuments = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/reports/${motherId}`);
      if (!response.ok) throw new Error("Failed to load documents");
      const data = await response.json();
      setDocuments(data.data || []);
    } catch (err) {
      console.error("Error loading documents:", err);
      setError("Failed to load documents");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "image/jpeg",
      "image/png",
      "image/webp",
    ];
    if (!allowedTypes.includes(file.type)) {
      setError("Please upload a PDF or image file (PDF, JPG, PNG, WebP)");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append("file", file);
      formData.append("mother_id", motherId);

      // Add uploader info if provided
      if (uploaderId) formData.append("uploader_id", uploaderId);
      if (uploaderRole) formData.append("uploader_role", uploaderRole);
      if (uploaderName) formData.append("uploader_name", uploaderName);

      // Upload to backend
      const response = await fetch(`${API_URL}/reports/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to upload document");
      }

      const result = await response.json();

      if (result.success) {
        setSuccess(`✅ Document "${file.name}" uploaded successfully`);
        // Reload documents to show the new one
        await loadDocuments();
      } else {
        throw new Error(result.message || "Upload failed");
      }
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDeleteDocument = async (reportId, fileName) => {
    if (!isDoctor) {
      setError("Only doctors can delete documents");
      return;
    }

    if (!window.confirm(`Are you sure you want to delete "${fileName}"? This action cannot be undone.`)) {
      return;
    }

    setDeleting(reportId);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(`${API_URL}/reports/${reportId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete document");
      }

      const result = await response.json();

      if (result.success) {
        setSuccess(`✅ Document "${fileName}" deleted successfully`);
        // Reload documents to reflect the deletion
        await loadDocuments();
      } else {
        throw new Error(result.message || "Delete failed");
      }
    } catch (err) {
      console.error("Delete error:", err);
      setError(err.message || "Failed to delete document");
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      return new Date(dateStr).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200";
      case "processing":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "error":
        return "bg-red-100 text-red-800 border-red-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-3 h-3" />;
      case "processing":
        return <Loader className="w-3 h-3 animate-spin" />;
      case "error":
        return <AlertCircle className="w-3 h-3" />;
      case "pending":
        return <Clock className="w-3 h-3" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "completed":
        return "Analyzed";
      case "processing":
        return "Analyzing...";
      case "error":
        return "Error";
      case "pending":
        return "Awaiting Analysis";
      default:
        return "Pending";
    }
  };

  const getRiskColor = (risk) => {
    if (!risk) return "bg-gray-100 text-gray-600";
    const riskLower = risk.toLowerCase();
    if (riskLower === "high") return "bg-red-100 text-red-800";
    if (riskLower === "moderate") return "bg-yellow-100 text-yellow-800";
    return "bg-green-100 text-green-800";
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 to-teal-600 text-white px-6 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Documents for {motherName || "Mother"}
          </h3>
          <button
            onClick={loadDocuments}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Upload Section */}
      <div className="p-4 bg-gray-50 border-b">
        <div className="flex items-center gap-4">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            className="hidden"
            disabled={uploading}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                Upload Document
              </>
            )}
          </button>
          <span className="text-sm text-gray-500">
            Supported: PDF, JPG, PNG, WebP (max 10MB)
          </span>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
            <button
              onClick={() => setError("")}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        )}
        {success && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-800 text-sm">
            <CheckCircle className="w-4 h-4" />
            {success}
            <button
              onClick={() => setSuccess("")}
              className="ml-auto text-green-600 hover:text-green-800"
            >
              ×
            </button>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <div className="text-center py-8">
            <Loader className="w-8 h-8 animate-spin mx-auto text-teal-600" />
            <p className="text-gray-600 mt-2">Loading documents...</p>
          </div>
        ) : documents.length > 0 ? (
          <div className="space-y-3">
            {documents.map((doc, idx) => (
              <div
                key={doc.id || idx}
                className="bg-white p-4 rounded-lg border border-gray-200 hover:border-indigo-300 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-5 h-5 text-teal-600" />
                      <span className="font-semibold text-gray-900">
                        {doc.filename || doc.file_name || "Document"}
                      </span>
                      {/* Enhanced Status Badge */}
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1 border ${getStatusColor(
                          doc.analysis_status
                        )}`}
                      >
                        {getStatusIcon(doc.analysis_status)}
                        {getStatusLabel(doc.analysis_status)}
                      </span>
                    </div>

                    <div className="text-sm text-gray-600 space-y-1">
                      <p>
                        📅 Uploaded:{" "}
                        {formatDate(doc.uploaded_at || doc.created_at)}
                      </p>
                      <p>
                        📄 Type:{" "}
                        {doc.file_type?.split("/").pop()?.toUpperCase() ||
                          "Unknown"}
                      </p>

                      {/* Uploader info */}
                      {doc.uploader_name && (
                        <p className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          Uploaded by: {doc.uploader_name}
                          {doc.uploader_role && (
                            <span className="px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded text-xs ml-1">
                              {doc.uploader_role}
                            </span>
                          )}
                        </p>
                      )}

                      {/* Pending Status Explanation */}
                      {doc.analysis_status === "pending" && (
                        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                          <div className="flex items-center gap-1 font-medium">
                            <Clock className="w-3 h-3" />
                            Awaiting AI Analysis
                          </div>
                          <p className="mt-1">
                            This document will be analyzed by our AI system to extract health metrics and detect any concerns.
                          </p>
                        </div>
                      )}

                      {doc.analysis_result?.risk_level && (
                        <p className="flex items-center gap-1">
                          ⚠️ Risk:
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getRiskColor(
                              doc.analysis_result.risk_level
                            )}`}
                          >
                            {doc.analysis_result.risk_level}
                          </span>
                        </p>
                      )}

                      {doc.analysis_result?.concerns?.length > 0 && (
                        <div className="mt-2 p-2 bg-yellow-50 rounded">
                          <p className="text-xs font-semibold text-yellow-800 mb-1">
                            Concerns:
                          </p>
                          <ul className="text-xs text-yellow-700 list-disc pl-4">
                            {doc.analysis_result.concerns
                              .slice(0, 3)
                              .map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* View Document Button */}
                    {doc.file_url && (
                      <a
                        href={doc.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                        title="View Document"
                      >
                        <ExternalLink className="w-5 h-5" />
                      </a>
                    )}

                    {/* Delete Button - Only for Doctors */}
                    {isDoctor && (
                      <button
                        onClick={() => handleDeleteDocument(doc.id, doc.filename || doc.file_name || "Document")}
                        disabled={deleting === doc.id}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Delete Document"
                      >
                        {deleting === doc.id ? (
                          <Loader className="w-5 h-5 animate-spin" />
                        ) : (
                          <Trash2 className="w-5 h-5" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-600 font-semibold">
              No documents uploaded yet
            </p>
            <p className="text-gray-500 text-sm mt-1">
              Click "Upload Document" to add medical reports
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
