// Aanchal AI - Signup Page
import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { authAPI, certificateAPI } from "../services/api";

const Signup = () => {
  const navigate = useNavigate();
  const { signInWithGoogle, user, isAuthenticated } = useAuth();

  // Check if we are in "Complete Profile" mode (authenticated but no role)
  // Or explicitly trying to sign up while authenticated
  const isProfileCompletion = isAuthenticated && !user?.role;

  const [formData, setFormData] = useState({
    email: user?.email || "",
    password: "",
    confirmPassword: "",
    fullName: user?.full_name || user?.user_metadata?.full_name || "",
    role: "ASHA_WORKER",
    phone: user?.phone || "",
    assignedArea: user?.assigned_area || "",
  });

  useEffect(() => {
    // If authenticated and has role, redirect to dashboard
    if (isAuthenticated && user?.role) {
      if (user.role === 'ADMIN') navigate('/admin/dashboard');
      else if (user.role === 'DOCTOR') navigate('/doctor/dashboard');
      else if (user.role === 'ASHA_WORKER') navigate('/asha/dashboard');
    }

    // If getting data from user object for profile completion
    if (user?.email && !formData.email) {
      setFormData(prev => ({
        ...prev,
        email: user.email,
        fullName: user.full_name || user.user_metadata?.full_name || prev.fullName
      }));
    }
  }, [isAuthenticated, user, navigate]);
  const [degreeFile, setDegreeFile] = useState(null);
  const [idFile, setIdFile] = useState(null);      // ASHA ID document
  const [idDocUrl, setIdDocUrl] = useState(null);  // URL of uploaded ID document
  const [idValidation, setIdValidation] = useState(null);  // ID validation result
  const [certValidation, setCertValidation] = useState(null); // Doctor cert validation result
  const [nameMatch, setNameMatch] = useState(null); // Name matching result
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [validatingId, setValidatingId] = useState(false);
  const [validatingCert, setValidatingCert] = useState(false);
  const [success, setSuccess] = useState(false);
  const [countdown, setCountdown] = useState(5);

  // Auto-redirect to login after successful registration
  useEffect(() => {
    if (success) {
      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            navigate("/auth/login");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [success, navigate]);

  // Function to check if names match (case-insensitive, handling common variations)
  const checkNameMatch = (formName, docName) => {
    if (!formName || !docName) {
      setNameMatch(null);
      return;
    }
    const normalizedFormName = formName.toLowerCase().replace(/[^a-z\s]/g, '').trim();
    const normalizedDocName = docName.toLowerCase().replace(/[^a-z\s]/g, '').trim();

    // Check direct match or if one contains the other (handles middle names, initials)
    const isMatch = normalizedFormName === normalizedDocName ||
      normalizedDocName.includes(normalizedFormName) ||
      normalizedFormName.includes(normalizedDocName);

    setNameMatch({
      match: isMatch,
      formName: formName,
      docName: docName,
      message: isMatch
        ? `✅ Name matches ID document`
        : `⚠️ Name mismatch: Form says "${formName}" but ID shows "${docName}". Please use the name exactly as on your ID.`
    });
  };

  const handleChange = (e) => {
    const newFormData = {
      ...formData,
      [e.target.name]: e.target.value,
    };
    setFormData(newFormData);
    setError("");

    // Re-check name match when fullName changes
    if (e.target.name === 'fullName') {
      if (formData.role === 'ASHA_WORKER' && idValidation?.info?.full_name) {
        checkNameMatch(e.target.value, idValidation.info.full_name);
      } else if (formData.role === 'DOCTOR' && certValidation?.info?.doctor_name) {
        checkNameMatch(e.target.value, certValidation.info.doctor_name);
      }
    }
  };

  // Handle ASHA ID document upload and validation
  const handleIdFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIdFile(file);
    setIdValidation(null);
    setValidatingId(true);
    setError("");

    try {
      // Validate ID document (includes hidden age check on backend)
      const res = await certificateAPI.validateAshaID(file);
      if (res?.data?.success && res?.data?.eligible) {
        const docName = res.data.id_info?.full_name || '';
        setIdValidation({
          valid: true,
          info: res.data.id_info,
          message: `✅ ID verified: ${docName}`
        });
        // Store the document URL if provided
        if (res.data.id_doc_url) {
          setIdDocUrl(res.data.id_doc_url);
        }
        // Check name matching
        checkNameMatch(formData.fullName, docName);
      } else {
        setIdValidation({
          valid: false,
          message: res?.data?.error || "ID validation failed"
        });
        setNameMatch(null);
      }
    } catch (err) {
      // Handle Rate Limit / Quota Exceeded Gracefully
      const errorMsg = err.response?.data?.detail || err.message || "Failed to validate ID";

      if (errorMsg.includes('429') || errorMsg.includes('RESOURCE_EXHAUSTED') || errorMsg.includes('Quota')) {
        setIdValidation({
          valid: true, // Allow submission!
          info: null,
          message: "⚠️ Automatic verification unavailable (Server Busy). Admin will verify manually."
        });
        setError(""); // Clear error to allow submit
      } else {
        setIdValidation({
          valid: false,
          message: errorMsg
        });
        setError(errorMsg);
      }
      setNameMatch(null);
    } finally {
      setValidatingId(false);
    }
  };

  // Handle Doctor Certificate upload and validation
  const handleDegreeFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setDegreeFile(file);
    setCertValidation(null);
    setValidatingCert(true);
    setError("");

    try {
      // Parse certificate to extract name
      const res = await certificateAPI.parseCertificate(file);
      if (res?.data?.parsed_data) {
        const docName = res.data.parsed_data.doctor_name || '';

        // Basic validation - must have a name
        if (docName && docName !== 'Unknown') {
          setCertValidation({
            valid: true,
            info: res.data.parsed_data,
            message: `✅ Certificate parsed: ${docName}`
          });
          // Check name matching
          checkNameMatch(formData.fullName, docName);
        } else {
          setCertValidation({
            valid: false,
            message: "Could not extract name from certificate. Please ensure it's clear."
          });
          setNameMatch(null);
        }
      }
    } catch (err) {
      console.error("Certificate parsing error:", err);
      // Don't block upload on parsing error, but warn
      setCertValidation({
        valid: true, // Allow upload even if parsing fails
        info: null,
        message: "⚠️ Could not auto-read certificate details (Manual review required)"
      });
    } finally {
      setValidatingCert(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    // Validation
    if (!isProfileCompletion && formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (!isProfileCompletion && formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      setLoading(false);
      return;
    }

    // ASHA worker requires valid ID document
    if (formData.role === "ASHA_WORKER") {
      if (!idFile) {
        setError("Please upload your ID document (PAN/Aadhaar/Driving License)");
        setLoading(false);
        return;
      }
      if (!idValidation?.valid) {
        setError("ID document validation failed. Please upload a valid document.");
        setLoading(false);
        return;
      }
      // Check name match
      if (nameMatch && !nameMatch.match) {
        setError(`Name mismatch: Your name "${formData.fullName}" doesn't match the ID document name "${nameMatch.docName}". Please use the name exactly as shown on your ID.`);
        setLoading(false);
        return;
      }
    }

    try {
      let degreeUrl = null;
      let uploadedIdDocUrl = null;

      // Upload ID document for ASHA worker
      if (formData.role === "ASHA_WORKER" && idFile) {
        try {
          const idUpload = await authAPI.uploadCertification(formData.email, idFile);
          uploadedIdDocUrl = idUpload?.data?.public_url || null;
        } catch (uploadErr) {
          console.warn("ID document upload failed, continuing with validation info:", uploadErr);
        }
      }

      if (formData.role === "DOCTOR") {
        if (!degreeFile) {
          setError("Please upload your degree certification");
          setLoading(false);
          return;
        }

        // Name matching check for doctors (using parsed certificate)
        if (certValidation?.valid && nameMatch && !nameMatch.match) {
          setError(`Name mismatch: Your name "${formData.fullName}" doesn't match the name on the certificate "${nameMatch.docName}". Please use the name exactly as shown on your certificate.`);
          setLoading(false);
          return;
        }

        const up = await authAPI.uploadCertification(
          formData.email,
          degreeFile
        );
        degreeUrl = up?.data?.public_url || null;
      }

      const payload = {
        email: formData.email,
        password: isProfileCompletion ? null : formData.password,
        full_name: formData.fullName,
        role: formData.role,
        phone: formData.phone,
        assigned_area: formData.assignedArea,
        degree_cert_url: degreeUrl,
        // Include parsed ID info for admin review (ASHA workers)
        id_info: formData.role === "ASHA_WORKER" && idValidation?.info ? {
          ...idValidation.info,
          name_verified: nameMatch?.match || false,
          form_name: formData.fullName,
          document_name: idValidation?.info?.full_name
        } : null,
        // Include parsed Certificate info for admin review (Doctors)
        document_metadata: formData.role === "DOCTOR" && certValidation?.info ? {
          ...certValidation.info,
          name_verified: nameMatch?.match || false,
          form_name: formData.fullName,
          document_name: certValidation?.info?.doctor_name
        } : null,
        // Include ID document URL for admin to view
        id_doc_url: uploadedIdDocUrl,
      };

      const res = await authAPI.createRegisterRequest(payload);
      if (res?.data?.success) {
        setSuccess(true);
        return;
      }
      throw new Error("Failed to submit registration request");
    } catch (err) {
      setError(err.message || "Failed to sign up");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setLoading(true);
      await signInWithGoogle();
      // Google OAuth will redirect automatically
    } catch (err) {
      setError(err.message || "Failed to sign in with Google");
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-purple-50 py-12 px-4">
        <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg text-center">
          <div className="text-green-500 text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Registration Successful!
          </h2>
          <p className="text-gray-600 mb-4">
            Please check your email to verify your account.
          </p>
          <p className="text-sm text-gray-500">
            Redirecting to login in {countdown} seconds...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-pink-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-purple-600 mb-2">
            🤰 Aanchal AI
          </h1>
          <h2 className="text-2xl font-bold text-gray-900">
            {isProfileCompletion ? "Complete Your Profile" : "Create Account"}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {isProfileCompletion ? "Please provide additional details to verify your role" : "Join the Aanchal AI healthcare system"}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Signup Form */}
        <form
          className="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-lg"
          onSubmit={handleSubmit}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Full Name */}
            <div className="md:col-span-2">
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Full Name *
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                required
                value={formData.fullName}
                onChange={handleChange}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Dr. John Doe"
              />
            </div>

            {/* Email */}
            <div className="md:col-span-2">
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Email Address *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="your@email.com"
              />
            </div>

            {/* Role (Admin hidden) */}
            <div className="md:col-span-2">
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Role *
              </label>
              <select
                id="role"
                name="role"
                required
                value={formData.role}
                onChange={handleChange}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="ASHA_WORKER">ASHA Worker</option>
                <option value="DOCTOR">Doctor</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                Select your role in the healthcare system
              </p>
            </div>

            {/* ASHA Worker ID Document Upload */}
            {formData.role === "ASHA_WORKER" && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID Document * (PAN Card / Aadhaar / Driving License)
                </label>
                <input
                  type="file"
                  accept="application/pdf,image/*"
                  onChange={handleIdFileChange}
                  className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                {validatingId && (
                  <p className="mt-2 text-sm text-blue-600 flex items-center gap-2">
                    <span className="animate-spin">⏳</span> Validating ID document...
                  </p>
                )}
                {idValidation && (
                  <p className={`mt-2 text-sm ${idValidation.valid ? 'text-green-600' : 'text-red-600'}`}>
                    {idValidation.message}
                  </p>
                )}
                {/* Name Match Status */}
                {nameMatch && idValidation?.valid && (
                  <div className={`mt-2 p-2 rounded-lg text-sm ${nameMatch.match
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                    }`}>
                    {nameMatch.message}
                  </div>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Upload your government ID for verification (any language)
                </p>
              </div>
            )}

            {/* Doctor Degree Certificate */}
            {formData.role === "DOCTOR" && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Degree Certification *
                </label>
                <input
                  type="file"
                  accept="application/pdf,image/*"
                  onChange={handleDegreeFileChange}
                  className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                {validatingCert && (
                  <p className="mt-2 text-sm text-blue-600 flex items-center gap-2">
                    <span className="animate-spin">⏳</span> Analyzing certificate...
                  </p>
                )}
                {certValidation && (
                  <p className={`mt-2 text-sm ${certValidation.valid ? 'text-green-600' : 'text-gray-600'}`}>
                    {certValidation.message}
                  </p>
                )}
                {/* Name Match Status for Doctor */}
                {nameMatch && certValidation?.valid && (
                  <div className={`mt-2 p-2 rounded-lg text-sm ${nameMatch.match
                    ? 'bg-green-50 text-green-700 border border-green-200'
                    : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                    }`}>
                    {nameMatch.message}
                  </div>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Upload PDF or image of your medical degree
                </p>
              </div>
            )}

            {/* Phone */}
            <div>
              <label
                htmlFor="phone"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Phone Number
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={formData.phone}
                onChange={handleChange}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="+91 9876543210"
              />
            </div>

            {/* Assigned Area */}
            <div>
              <label
                htmlFor="assignedArea"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Assigned Area
              </label>
              <input
                id="assignedArea"
                name="assignedArea"
                type="text"
                value={formData.assignedArea}
                onChange={handleChange}
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., Pune, Mumbai"
              />
            </div>

            {/* Password Fields - Hidden for OAuth Profile Completion */}
            {!isProfileCompletion && (
              <>
                {/* Password */}
                <div>
                  <label
                    htmlFor="password"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Password *
                  </label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="••••••••"
                  />
                  <p className="mt-1 text-xs text-gray-500">Minimum 8 characters</p>
                </div>

                {/* Confirm Password */}
                <div>
                  <label
                    htmlFor="confirmPassword"
                    className="block text-sm font-medium text-gray-700 mb-1"
                  >
                    Confirm Password *
                  </label>
                  <input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    required
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    placeholder="••••••••"
                  />
                </div>
              </>
            )}
          </div>

          {/* Sign Up Button */}
          <button
            type="submit"
            disabled={loading}
            className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Submitting request..." : "Submit Registration Request"}
          </button>

          {/* OAuth Divider - Hide if completing profile */}
          {!isProfileCompletion && (
            <>
              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">
                    Or continue with
                  </span>
                </div>
              </div>

              {/* Google Sign In */}
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 py-3 px-4 border border-gray-300 rounded-lg shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign up with Google
              </button>

              {/* Login Link */}
              <div className="text-center mt-4">
                <p className="text-sm text-gray-600">
                  Already have an account?{" "}
                  <Link
                    to="/auth/login"
                    className="font-medium text-purple-600 hover:text-purple-500"
                  >
                    Log in
                  </Link>
                </p>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
};

export default Signup;
