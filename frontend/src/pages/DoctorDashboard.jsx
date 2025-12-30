import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import PatientChatHistory from "../components/PatientChatHistory.jsx";
import ConsultationForm from "../components/ConsultationForm.jsx";
import MotherRegistrationForm from "../components/MotherRegistrationForm.jsx";
import DocumentManager from "../components/DocumentManager.jsx";
import { supabase } from "../services/auth.js";
import { useAuth } from "../contexts/AuthContext";
import {
  Stethoscope,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  MapPin,
  Cake,
  Activity,
  Heart,
  TrendingUp,
  Search,
  RefreshCw,
  Loader,
  FileText,
  Calendar,
  Thermometer,
  BarChart2,
  MessageCircle,
  ClipboardList,
  UserPlus,
  Upload,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const apiCall = async (method, endpoint, data = null) => {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (data) options.body = JSON.stringify(data);
  const response = await fetch(`${API_URL}${endpoint}`, options);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return await response.json();
};

export default function DoctorDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();

  const [doctorId, setDoctorId] = useState(null);
  const [doctorInfo, setDoctorInfo] = useState(null);
  const [mothers, setMothers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [riskMap, setRiskMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState("");

  // Assessment history for selected mother
  const [assessments, setAssessments] = useState([]);
  const [loadingAssessments, setLoadingAssessments] = useState(false);

  // View tab: 'chat' | 'history' | 'consultation' | 'documents'
  const [activeTab, setActiveTab] = useState("history");

  // Main view for sidebar: 'patients' | 'register'
  const [mainView, setMainView] = useState("patients");
  const [successMsg, setSuccessMsg] = useState("");

  // Auto-detect doctor by user_profile_id from doctors table
  useEffect(() => {
    const autoDetectDoctor = async () => {
      if (!user?.id && !user?.email) {
        setLoadingProfile(false);
        return;
      }

      try {
        // First try: Look up doctor by user_profile_id (auth user ID)
        if (user?.id) {
          const { data, error } = await supabase
            .from("doctors")
            .select("id, name, phone, assigned_area, email")
            .eq("user_profile_id", user.id)
            .single();

          if (!error && data) {
            setDoctorId(data.id);
            setDoctorInfo(data);
            console.log("✅ Found doctor by user_profile_id:", data.name);
            setLoadingProfile(false);
            return;
          }
        }

        // Second try: Look up by email
        if (user?.email) {
          const { data, error } = await supabase
            .from("doctors")
            .select("id, name, phone, assigned_area, email")
            .eq("email", user.email)
            .single();

          if (!error && data) {
            setDoctorId(data.id);
            setDoctorInfo(data);
            console.log("✅ Found doctor by email:", data.name);
            setLoadingProfile(false);
            return;
          }
        }

        // Third try: Match by name
        if (user?.full_name) {
          const { data: byName } = await supabase
            .from("doctors")
            .select("id, name, phone, assigned_area, email")
            .ilike("name", `%${user.full_name}%`)
            .limit(1);

          if (byName && byName[0]) {
            setDoctorId(byName[0].id);
            setDoctorInfo(byName[0]);
            console.log("✅ Found doctor by name:", byName[0].name);
            setLoadingProfile(false);
            return;
          }
        }

        setError(
          "Your account is not linked to a doctor profile. Contact admin."
        );
      } catch (err) {
        console.error("Auto-detect error:", err);
        setError("Could not find your doctor profile");
      } finally {
        setLoadingProfile(false);
      }
    };

    if (user) {
      autoDetectDoctor();
    }
  }, [user]);

  // Load mothers assigned to this doctor
  const loadMothers = async () => {
    if (!doctorId) return;
    setLoading(true);
    try {
      // Get mothers assigned to this doctor
      const { data } = await supabase
        .from("mothers")
        .select("*")
        .eq("doctor_id", doctorId);

      const moms = data || [];
      setMothers(moms);

      // Load risk levels in a single batch query
      if (moms.length > 0) {
        const motherIds = moms.map(m => m.id);
        const { data: allAssessments } = await supabase
          .from("risk_assessments")
          .select("mother_id, risk_level, created_at")
          .in("mother_id", motherIds)
          .order("created_at", { ascending: false });

        // Group by mother_id and get the latest for each
        const risks = {};
        (allAssessments || []).forEach(ra => {
          if (!risks[ra.mother_id]) {
            risks[ra.mother_id] = ra.risk_level;
          }
        });

        // Set default LOW for mothers without assessments
        moms.forEach(m => {
          if (!risks[m.id]) {
            risks[m.id] = "LOW";
          }
        });

        setRiskMap(risks);
      }
    } finally {
      setLoading(false);
    }
  };

  // Load assessments for selected mother
  const loadAssessments = async (motherId) => {
    setLoadingAssessments(true);
    try {
      const { data, error } = await supabase
        .from("risk_assessments")
        .select("*")
        .eq("mother_id", motherId)
        .order("created_at", { ascending: false });

      if (!error) {
        setAssessments(data || []);
      }
    } catch (err) {
      console.error("Error loading assessments:", err);
    } finally {
      setLoadingAssessments(false);
    }
  };

  useEffect(() => {
    if (doctorId) {
      loadMothers();
    }
  }, [doctorId]);

  // Load assessments when mother is selected
  useEffect(() => {
    if (selected?.id) {
      loadAssessments(selected.id);
    }
  }, [selected]);

  const sorted = [...mothers]
    .filter(
      (m) =>
        m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.location?.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const order = { HIGH: 0, MODERATE: 1, LOW: 2 };
      return (order[riskMap[a.id]] ?? 2) - (order[riskMap[b.id]] ?? 2);
    });

  const highRiskCount = mothers.filter((m) => riskMap[m.id] === "HIGH").length;
  const moderateRiskCount = mothers.filter(
    (m) => riskMap[m.id] === "MODERATE"
  ).length;

  const getRiskColor = (risk) => {
    switch (risk) {
      case "HIGH":
        return "bg-red-50 border-red-200 hover:border-red-300";
      case "MODERATE":
        return "bg-yellow-50 border-yellow-200 hover:border-yellow-300";
      default:
        return "bg-green-50 border-green-200 hover:border-green-300";
    }
  };

  const getRiskIcon = (risk) => {
    switch (risk) {
      case "HIGH":
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case "MODERATE":
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      default:
        return <CheckCircle className="w-5 h-5 text-green-600" />;
    }
  };

  const getRiskEmoji = (risk) => {
    switch (risk) {
      case "HIGH":
        return "🔴";
      case "MODERATE":
        return "🟡";
      default:
        return "🟢";
    }
  };

  // Show loading while detecting doctor
  if (loadingProfile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <Loader className="w-12 h-12 animate-spin mx-auto text-blue-600 mb-4" />
          <h1 className="text-xl font-bold text-gray-900">
            Loading Doctor Portal
          </h1>
          <p className="text-gray-600 mt-2">Finding your profile...</p>
        </div>
      </div>
    );
  }

  // Show error if doctor not found
  if (!doctorId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">
              Profile Not Found
            </h1>
            <p className="text-gray-600 mt-2">
              {user?.email
                ? `No doctor found for: ${user.email}`
                : "Please login first"}
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 p-4 rounded-lg mb-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
            <p className="text-yellow-800 text-sm font-semibold mb-2">
              📋 To fix this:
            </p>
            <ul className="text-yellow-700 text-sm list-disc pl-5 space-y-1">
              <li>Ensure your email is registered in the doctors list</li>
              <li>Contact admin to link your account</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Sidebar */}
      <div className="w-96 bg-white border-r border-gray-200 flex flex-col shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white px-6 py-6">
          <div className="flex items-center gap-4">
            <div className="bg-blue-500 p-3 rounded-lg">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Doctor Portal</h1>
              <p className="text-blue-100 text-sm">
                {doctorInfo?.name || "Doctor"}
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 px-4 py-4 bg-gray-50 border-b border-gray-200">
          <div className="bg-white p-3 rounded-lg text-center border border-gray-200">
            <div className="text-2xl font-bold text-gray-900">
              {mothers.length}
            </div>
            <div className="text-xs text-gray-600 mt-1">Patients</div>
          </div>
          <div className="bg-red-50 p-3 rounded-lg text-center border border-red-200">
            <div className="text-2xl font-bold text-red-600">
              {highRiskCount}
            </div>
            <div className="text-xs text-red-600 mt-1">High Risk</div>
          </div>
          <div className="bg-yellow-50 p-3 rounded-lg text-center border border-yellow-200">
            <div className="text-2xl font-bold text-yellow-600">
              {moderateRiskCount}
            </div>
            <div className="text-xs text-yellow-600 mt-1">Moderate</div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => {
              setMainView("patients");
              setSelected(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold flex flex-col items-center gap-1 ${mainView === "patients"
                ? "text-blue-600 bg-blue-50"
                : "text-gray-500"
              }`}
          >
            <Stethoscope className="w-4 h-4" />
            Patients
          </button>
          <button
            onClick={() => {
              setMainView("register");
              setSelected(null);
            }}
            className={`flex-1 py-3 text-xs font-semibold flex flex-col items-center gap-1 ${mainView === "register"
                ? "text-pink-600 bg-pink-50"
                : "text-gray-500"
              }`}
          >
            <UserPlus className="w-4 h-4" />
            Register
          </button>
        </div>

        {/* Success Message */}
        {successMsg && (
          <div className="mx-4 mt-3 p-2 bg-green-50 border border-green-200 rounded-lg text-green-800 text-xs">
            {successMsg}
            <button onClick={() => setSuccessMsg("")} className="float-right">
              ×
            </button>
          </div>
        )}

        {/* Search */}
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search patients..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
        </div>

        {/* Patients List */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600 mb-2" />
              <p className="text-gray-600 text-sm">Loading patients...</p>
            </div>
          ) : sorted.length > 0 ? (
            <div className="space-y-3">
              {sorted.map((m) => {
                const risk = riskMap[m.id] || "LOW";
                return (
                  <div
                    key={m.id}
                    onClick={() => setSelected(m)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all transform hover:scale-102 ${selected?.id === m.id
                        ? "border-blue-600 bg-blue-50 shadow-md"
                        : `border-gray-200 ${getRiskColor(risk)}`
                      }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 text-sm">
                          {m.name}
                        </div>
                        <div className="flex items-center gap-1 text-xs text-gray-600 mt-1">
                          <MapPin className="w-3 h-3" />
                          {m.location}
                        </div>
                      </div>
                      {getRiskIcon(risk)}
                    </div>
                    <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between text-xs">
                      <span
                        className={`px-2 py-1 rounded-full font-semibold ${risk === "HIGH"
                            ? "bg-red-100 text-red-700"
                            : risk === "MODERATE"
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-green-100 text-green-700"
                          }`}
                      >
                        {risk}
                      </span>
                      <span className="text-gray-500">Age: {m.age}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <Heart className="w-12 h-12 mx-auto text-gray-300 mb-3" />
              <p className="text-gray-600 font-medium">No patients assigned</p>
              <p className="text-gray-500 text-sm mt-1">
                Patients will appear when assigned to you
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {selected ? (
          <div className="flex flex-col h-full">
            {/* Patient Header */}
            <div className="bg-white border-b border-gray-200 px-8 py-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selected.name}
                  </h2>
                  <p className="text-gray-600 mt-1 flex items-center gap-2 text-sm">
                    <MapPin className="w-4 h-4" /> {selected.location} · Age{" "}
                    {selected.age}
                  </p>
                </div>
                <div
                  className={`px-5 py-3 rounded-lg font-semibold flex items-center gap-2 ${riskMap[selected.id] === "HIGH"
                      ? "bg-red-100 text-red-700"
                      : riskMap[selected.id] === "MODERATE"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-green-100 text-green-700"
                    }`}
                >
                  <span className="text-xl">
                    {getRiskEmoji(riskMap[selected.id])}
                  </span>
                  {riskMap[selected.id] || "LOW"} Risk
                </div>
              </div>

              {/* Tab buttons */}
              <div className="flex gap-3 mt-4 flex-wrap">
                <button
                  onClick={() => setActiveTab("history")}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${activeTab === "history"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700"
                    }`}
                >
                  <FileText className="w-4 h-4" /> Assessment History
                </button>
                <button
                  onClick={() => setActiveTab("documents")}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${activeTab === "documents"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-700"
                    }`}
                >
                  <Upload className="w-4 h-4" /> Documents
                </button>
                <button
                  onClick={() => setActiveTab("chat")}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${activeTab === "chat"
                      ? "bg-green-600 text-white"
                      : "bg-gray-100 text-gray-700"
                    }`}
                >
                  <MessageCircle className="w-4 h-4" /> Chat History
                </button>
                <button
                  onClick={() => setActiveTab("consultation")}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${activeTab === "consultation"
                      ? "bg-purple-600 text-white"
                      : "bg-gray-100 text-gray-700"
                    }`}
                >
                  <ClipboardList className="w-4 h-4" /> Consultation Details
                </button>
              </div>
            </div>

            {/* Content Grid */}
            <div className="flex-1 overflow-hidden flex gap-6 p-6">
              {/* Patient Details Card */}
              <div className="w-80 bg-white rounded-xl shadow-md border border-gray-200 p-5 overflow-y-auto">
                <h3 className="text-lg font-bold text-gray-900 mb-5 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Clinical Profile
                </h3>
                <div className="space-y-4 text-sm">
                  <div className="pb-3 border-b">
                    <label className="text-xs font-bold text-gray-500 uppercase">
                      Phone
                    </label>
                    <p className="text-gray-900 font-semibold mt-1">
                      {selected.phone || "N/A"}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">
                        BMI
                      </label>
                      <p className="text-gray-900 font-semibold mt-1">
                        {selected.bmi?.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">
                        Gravida
                      </label>
                      <p className="text-gray-900 font-semibold mt-1">
                        {selected.gravida}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">
                        Parity
                      </label>
                      <p className="text-gray-900 font-semibold mt-1">
                        {selected.parity}
                      </p>
                    </div>
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">
                        Language
                      </label>
                      <p className="text-gray-900 font-semibold mt-1 capitalize">
                        {selected.preferred_language}
                      </p>
                    </div>
                  </div>
                  {selected.due_date && (
                    <div>
                      <label className="text-xs font-bold text-gray-500 uppercase">
                        Due Date
                      </label>
                      <p className="text-gray-900 font-semibold mt-1">
                        {new Date(selected.due_date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Main Content Area */}
              <div className="flex-1 bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden flex flex-col">
                {activeTab === "history" ? (
                  <>
                    <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4">
                      <h3 className="text-lg font-bold flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Assessment History ({assessments.length})
                      </h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-5">
                      {loadingAssessments ? (
                        <div className="text-center py-8">
                          <Loader className="w-6 h-6 animate-spin mx-auto text-blue-600" />
                        </div>
                      ) : assessments.length > 0 ? (
                        <div className="space-y-4">
                          {assessments.map((a, idx) => (
                            <div
                              key={a.id || idx}
                              className={`p-4 rounded-lg border-2 ${a.risk_level === "HIGH"
                                  ? "bg-red-50 border-red-200"
                                  : a.risk_level === "MODERATE"
                                    ? "bg-yellow-50 border-yellow-200"
                                    : "bg-green-50 border-green-200"
                                }`}
                            >
                              <div className="flex justify-between items-start mb-3">
                                <div>
                                  <p className="text-xs text-gray-600 flex items-center gap-1">
                                    <Calendar className="w-3 h-3" />
                                    {new Date(a.created_at).toLocaleString()}
                                  </p>
                                </div>
                                <div
                                  className={`px-3 py-1 rounded-full text-sm font-bold ${a.risk_level === "HIGH"
                                      ? "bg-red-200 text-red-800"
                                      : a.risk_level === "MODERATE"
                                        ? "bg-yellow-200 text-yellow-800"
                                        : "bg-green-200 text-green-800"
                                    }`}
                                >
                                  {getRiskEmoji(a.risk_level)} {a.risk_level} (
                                  {(a.risk_score * 100).toFixed(0)}%)
                                </div>
                              </div>

                              <div className="grid grid-cols-4 gap-3 text-sm">
                                {a.systolic_bp && a.diastolic_bp && (
                                  <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-gray-500">
                                      Blood Pressure
                                    </p>
                                    <p className="font-bold">
                                      {a.systolic_bp}/{a.diastolic_bp}
                                    </p>
                                  </div>
                                )}
                                {a.heart_rate && (
                                  <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-gray-500">
                                      Heart Rate
                                    </p>
                                    <p className="font-bold">
                                      {a.heart_rate} bpm
                                    </p>
                                  </div>
                                )}
                                {a.blood_glucose && (
                                  <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-gray-500">
                                      Glucose
                                    </p>
                                    <p className="font-bold">
                                      {a.blood_glucose} mg/dL
                                    </p>
                                  </div>
                                )}
                                {a.hemoglobin && (
                                  <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-gray-500">
                                      Hemoglobin
                                    </p>
                                    <p className="font-bold">
                                      {a.hemoglobin} g/dL
                                    </p>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-12">
                          <FileText className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                          <p className="text-gray-600 font-medium">
                            No assessments yet
                          </p>
                          <p className="text-gray-500 text-sm mt-1">
                            ASHA worker will perform assessments
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                ) : activeTab === "documents" ? (
                  <DocumentManager
                    motherId={selected.id}
                    motherName={selected.name}
                    uploaderId={doctorId?.toString()}
                    uploaderRole="DOCTOR"
                    uploaderName={doctorInfo?.name || "Doctor"}
                  />
                ) : activeTab === "chat" ? (
                  <>
                    <div className="bg-gradient-to-r from-green-600 to-green-700 text-white px-6 py-4">
                      <h3 className="text-lg font-bold flex items-center gap-2">
                        <MessageCircle className="w-5 h-5" />
                        Chat History
                      </h3>
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <PatientChatHistory
                        motherId={selected.id}
                        userRole="DOCTOR"
                        userName={doctorInfo?.name || "Doctor"}
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-6 py-4">
                      <h3 className="text-lg font-bold flex items-center gap-2">
                        <ClipboardList className="w-5 h-5" />
                        Consultation Details
                      </h3>
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <ConsultationForm
                        motherId={selected.id}
                        doctorId={doctorId}
                        doctorName={doctorInfo?.name || "Doctor"}
                        onSave={() => loadAssessments(selected.id)}
                      />
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        ) : mainView === "register" ? (
          <div className="flex-1 overflow-y-auto p-8">
            <MotherRegistrationForm
              assignerId={doctorId}
              assignerRole="DOCTOR"
              onSuccess={(newMother) => {
                setSuccessMsg(`✅ Successfully registered: ${newMother.name}`);
                loadMothers();
                setMainView("patients");
              }}
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Stethoscope className="w-20 h-20 mx-auto mb-4 text-gray-300" />
              <p className="text-xl font-semibold text-gray-900">
                Select a Patient
              </p>
              <p className="text-gray-600 mt-2">
                Choose a patient to view their records and assessments
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
