import { useEffect, useState, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import authService, { supabase } from "../services/auth";
import { Upload, CheckCircle, XCircle, Loader2 } from "lucide-react";

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { loading, user, isAuthenticated, signOut } = useAuth();
  const [stage, setStage] = useState("loading"); // 'loading', 'role_selection', 'doctor_upload', 'submitting', 'pending', 'error'
  const [pendingEmail, setPendingEmail] = useState("");
  const [oauthError, setOauthError] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingCountdown, setPendingCountdown] = useState(5);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Check for OAuth errors in URL
    const error = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    if (error) {
      console.error("OAuth error:", error, errorDescription);
      setOauthError({
        code: error,
        message: decodeURIComponent(
          errorDescription || "Authentication failed"
        ),
      });
      setStage("error");
      return;
    }

    const handleAuth = async () => {
      if (loading) return;

      let currentUser = user;
      if (!isAuthenticated) {
        currentUser = await authService.getCurrentUser();
      }

      if (!currentUser) {
        navigate("/auth/login", { replace: true });
        return;
      }

      const role = currentUser?.role?.toUpperCase();

      // If user has no role, show role selection
      if (!role) {
        setPendingEmail(currentUser?.email || "");
        setStage("role_selection");
        return;
      }

      // Redirect based on role
      if (role === "ADMIN") {
        navigate("/admin/dashboard", { replace: true });
      } else if (role === "DOCTOR") {
        navigate("/doctor/dashboard", { replace: true });
      } else if (role === "ASHA_WORKER") {
        navigate("/asha/dashboard", { replace: true });
      } else {
        // Unknown role - show pending
        setPendingEmail(currentUser?.email || "");
        setStage("pending");
      }
    };

    handleAuth();
  }, [loading, isAuthenticated, user, navigate, searchParams]);

  // Auto-redirect to login after successful registration submission
  useEffect(() => {
    if (stage === "pending") {
      const timer = setInterval(() => {
        setPendingCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            signOut().then(() => {
              navigate("/auth/login", { replace: true });
            });
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [stage, navigate, signOut]);

  const handleRoleSelect = (role) => {
    setSelectedRole(role);
    if (role === "DOCTOR") {
      setStage("doctor_upload");
    } else {
      // For ASHA Worker, submit immediately
      handleSubmitRole(role, null);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setUploadError("");

    if (file) {
      // Validate file type
      const validTypes = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg",
      ];
      if (!validTypes.includes(file.type)) {
        setUploadError("Please upload a PDF or image file (JPG, PNG)");
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setUploadError("File size must be less than 5MB");
        return;
      }

      setUploadedFile(file);
    }
  };

  const handleSubmitRole = async (role, file) => {
    setIsSubmitting(true);
    setStage("submitting");

    try {
      const currentUser = await authService.getCurrentUser();
      if (!currentUser) {
        throw new Error("User not found");
      }

      // Upload file to Supabase Storage if it's a doctor
      let uploadedFileUrl = null;
      if (file && role === "DOCTOR") {
        const fileName = `doctor_registrations/${
          currentUser.id
        }/${Date.now()}_${file.name}`;
        const { data: uploadData, error: uploadError } = await supabase.storage
          .from("certifications")
          .upload(fileName, file);

        if (uploadError) {
          console.error("Upload error:", uploadError);
          // Continue without file - admin can request later
        } else {
          const { data: urlData } = supabase.storage
            .from("certifications")
            .getPublicUrl(fileName);
          uploadedFileUrl = urlData?.publicUrl;
        }
      }

      // Create registration request for admin approval
      // First try insert, if duplicate email exists, update
      const requestData = {
        email: currentUser.email,
        full_name: currentUser.full_name || currentUser.email?.split("@")[0],
        role_requested: role,
        degree_cert_url: uploadedFileUrl,
        status: "PENDING",
      };

      // Check if request already exists (don't use .single() as it throws 406 when not found)
      const { data: existingRows } = await supabase
        .from("registration_requests")
        .select("id")
        .eq("email", currentUser.email)
        .limit(1);

      const existing = existingRows && existingRows.length > 0;

      let insertError;
      if (existing) {
        // Update existing request
        const { error } = await supabase
          .from("registration_requests")
          .update(requestData)
          .eq("email", currentUser.email);
        insertError = error;
      } else {
        // Insert new request
        const { error } = await supabase
          .from("registration_requests")
          .insert(requestData);
        insertError = error;
      }

      if (insertError) {
        console.error("Insert/Update error:", insertError);
      }

      // Show pending approval message
      setPendingEmail(currentUser.email || "");
      setStage("pending");
    } catch (error) {
      console.error("Submit error:", error);
      setOauthError({ code: "submit_error", message: error.message });
      setStage("error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
    navigate("/auth/login", { replace: true });
  };

  const handleBackToLogin = () => {
    navigate("/auth/login", { replace: true });
  };

  // Show OAuth error message
  if (stage === "error" && oauthError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-100">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Authentication Failed
            </h2>
            <p className="text-gray-600 mb-4">{oauthError.message}</p>
            <p className="text-sm text-gray-500 mb-6">
              This usually happens when there's an issue with your account or
              the authentication service. Please try again or contact support.
            </p>
            <div className="space-y-3">
              <button
                onClick={handleBackToLogin}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Back to Login
              </button>
              <p className="text-xs text-gray-400">
                Error code: {oauthError.code}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Role Selection Screen
  if (stage === "role_selection") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
        <div className="max-w-lg w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-purple-600 mb-2">
                🤰 MatruRaksha AI
              </h1>
              <h2 className="text-xl font-semibold text-gray-900">Welcome!</h2>
              <p className="text-gray-600 mt-2">
                Please select your role to continue
              </p>
              {pendingEmail && (
                <p className="text-sm text-gray-500 mt-1">
                  Signed in as:{" "}
                  <span className="font-medium">{pendingEmail}</span>
                </p>
              )}
            </div>

            <div className="space-y-4">
              {/* Doctor Option */}
              <button
                onClick={() => handleRoleSelect("DOCTOR")}
                className="w-full p-6 rounded-xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-all group text-left"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                    <span className="text-3xl">👨‍⚕️</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      I am a Doctor
                    </h3>
                    <p className="text-sm text-gray-500">
                      Medical practitioner overseeing maternal care
                    </p>
                  </div>
                </div>
              </button>

              {/* ASHA Worker Option */}
              <button
                onClick={() => handleRoleSelect("ASHA_WORKER")}
                className="w-full p-6 rounded-xl border-2 border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition-all group text-left"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                    <span className="text-3xl">👩‍⚕️</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      I am an ASHA Worker
                    </h3>
                    <p className="text-sm text-gray-500">
                      Community health worker supporting mothers
                    </p>
                  </div>
                </div>
              </button>
            </div>

            <div className="mt-8 text-center">
              <button
                onClick={handleSignOut}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Sign out and use different account
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Doctor Document Upload Screen
  if (stage === "doctor_upload") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
        <div className="max-w-lg w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">👨‍⚕️</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">
                Doctor Registration
              </h2>
              <p className="text-gray-600 mt-2">
                Please upload your medical registration document for
                verification
              </p>
            </div>

            {/* File Upload Area */}
            <div className="mb-6">
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
                  ${
                    uploadedFile
                      ? "border-green-400 bg-green-50"
                      : "border-gray-300 hover:border-purple-400 hover:bg-purple-50"
                  }
                  ${uploadError ? "border-red-400 bg-red-50" : ""}
                `}
              >
                {uploadedFile ? (
                  <div className="flex flex-col items-center">
                    <CheckCircle className="w-12 h-12 text-green-500 mb-2" />
                    <p className="font-semibold text-green-700">
                      {uploadedFile.name}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                    <p className="text-xs text-gray-400 mt-2">
                      Click to change file
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <Upload className="w-12 h-12 text-gray-400 mb-2" />
                    <p className="font-semibold text-gray-700">
                      Click to upload document
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      PDF, JPG, or PNG (max 5MB)
                    </p>
                  </div>
                )}
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={handleFileChange}
                className="hidden"
              />

              {uploadError && (
                <p className="text-red-500 text-sm mt-2">{uploadError}</p>
              )}
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h4 className="font-semibold text-blue-800 mb-2">
                📋 Accepted Documents:
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Medical Council Registration Certificate</li>
                <li>• MBBS/MD Degree Certificate</li>
                <li>• State Medical Council License</li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => handleSubmitRole("DOCTOR", uploadedFile)}
                disabled={!uploadedFile || isSubmitting}
                className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? "Submitting..." : "Submit for Verification"}
              </button>

              <button
                onClick={() => setStage("role_selection")}
                className="w-full py-2 px-4 text-gray-600 hover:text-gray-800 transition-colors"
              >
                ← Back to role selection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Submitting state
  if (stage === "submitting") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-500 animate-spin mx-auto" />
          <p className="mt-4 text-gray-600">Submitting your registration...</p>
        </div>
      </div>
    );
  }

  // Show pending approval message
  if (stage === "pending") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-yellow-100">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-yellow-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Registration Submitted!
            </h2>
            <p className="text-gray-600 mb-4">
              Your registration for{" "}
              <span className="font-semibold text-gray-800">
                {pendingEmail}
              </span>{" "}
              is pending admin approval.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              {selectedRole === "DOCTOR"
                ? "Your medical registration document will be verified by our team. This usually takes 24-48 hours."
                : "An administrator will review and approve your account shortly."}
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <p className="text-sm text-green-700">
                ✅ You will receive an email notification once your account is
                approved.
              </p>
            </div>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                Redirecting to login in {pendingCountdown} seconds...
              </p>
              <p className="text-xs text-gray-400">
                Contact your system administrator if you need immediate access.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Loading state
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
        <p className="mt-4 text-gray-600">Signing you in...</p>
      </div>
    </div>
  );
}
