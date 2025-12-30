import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { supabase } from "../services/auth.js";
import { useAuth } from "../contexts/AuthContext";
import PatientChatHistory from "../components/PatientChatHistory.jsx";
import DocumentManager from "../components/DocumentManager.jsx";
import MotherRegistrationForm from "../components/MotherRegistrationForm.jsx";
import {
  Users,
  Search,
  Phone,
  MapPin,
  AlertCircle,
  Heart,
  TrendingUp,
  Loader,
  RefreshCw,
  Activity,
  FileText,
  ClipboardCheck,
  BarChart2,
  ChevronLeft,
  Calendar,
  Thermometer,
  UserPlus,
} from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

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

export default function ASHAInterface() {
  const { t } = useTranslation();
  const { user } = useAuth();

  // ASHA worker state
  const [ashaWorkerId, setAshaWorkerId] = useState(null);
  const [mothers, setMothers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [riskMap, setRiskMap] = useState({});
  const [analytics, setAnalytics] = useState(null);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // Assessment history for selected mother
  const [motherAssessments, setMotherAssessments] = useState([]);
  const [loadingMotherAssessments, setLoadingMotherAssessments] =
    useState(false);
  const [motherViewTab, setMotherViewTab] = useState("history"); // 'history' | 'chat'

  // Main content view: 'mother' | 'assess' | 'stats' | 'assessment-detail'
  const [mainView, setMainView] = useState("mother");
  const [selectedAssessment, setSelectedAssessment] = useState(null);

  const [assessmentForm, setAssessmentForm] = useState({
    mother_id: "",
    systolic_bp: "",
    diastolic_bp: "",
    heart_rate: "",
    blood_glucose: "",
    hemoglobin: "",
    proteinuria: 0,
    edema: 0,
    headache: 0,
    vision_changes: 0,
    epigastric_pain: 0,
    vaginal_bleeding: 0,
  });
  const [riskResult, setRiskResult] = useState(null);

  // Auto-detect ASHA worker by user_profile_id from asha_workers table
  useEffect(() => {
    const autoDetectAsha = async () => {
      if (!user?.id && !user?.email) {
        setLoadingProfile(false);
        return;
      }

      try {
        // First try: Look up ASHA worker by user_profile_id (auth user ID)
        if (user?.id) {
          const { data, error } = await supabase
            .from("asha_workers")
            .select("id, name, assigned_area, email")
            .eq("user_profile_id", user.id)
            .single();

          if (!error && data) {
            setAshaWorkerId(data.id);
            console.log("✅ Found ASHA worker by user_profile_id:", data.name);
            setLoadingProfile(false);
            return;
          }
        }

        // Second try: Look up by email
        if (user?.email) {
          const { data, error } = await supabase
            .from("asha_workers")
            .select("id, name, assigned_area, email")
            .eq("email", user.email)
            .single();

          if (!error && data) {
            setAshaWorkerId(data.id);
            console.log("✅ Found ASHA worker by email:", data.name);
            setLoadingProfile(false);
            return;
          }
        }

        // Third try: Match by name
        if (user?.full_name) {
          const { data: byName } = await supabase
            .from("asha_workers")
            .select("id, name, assigned_area, email")
            .ilike("name", `%${user.full_name}%`)
            .limit(1);

          if (byName && byName[0]) {
            setAshaWorkerId(byName[0].id);
            console.log("✅ Found ASHA worker by name:", byName[0].name);
            setLoadingProfile(false);
            return;
          }
        }

        setError(
          "Your account is not linked to an ASHA worker profile. Contact admin."
        );
      } catch (err) {
        console.error("Auto-detect error:", err);
        setError("Could not find your ASHA profile");
      } finally {
        setLoadingProfile(false);
      }
    };

    if (user) {
      autoDetectAsha();
    }
  }, [user]);

  // Load data when ASHA ID is available
  useEffect(() => {
    if (ashaWorkerId) {
      loadMothers();
    }
  }, [ashaWorkerId]);

  const loadMothers = async () => {
    if (!ashaWorkerId) return;
    setLoading(true);
    setError("");
    try {
      const { data, error: err } = await supabase
        .from("mothers")
        .select("*")
        .eq("asha_worker_id", Number(ashaWorkerId));
      if (err) throw err;
      setMothers(data || []);

      // Load risk assessments in a single batch query
      if (data && data.length > 0) {
        const motherIds = data.map(m => m.id);
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
        data.forEach(m => {
          if (!risks[m.id]) {
            risks[m.id] = "LOW";
          }
        });

        setRiskMap(risks);
      }

      // Load analytics
      await loadAnalytics();
    } catch (err) {
      setError("Error loading mothers: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    if (!ashaWorkerId) return;
    try {
      const data = await apiCall("GET", `/analytics/asha/${ashaWorkerId}`);
      setAnalytics(data);
    } catch (err) {
      console.error("Analytics error:", err);
    }
  };

  // Load assessments for a specific mother
  const loadMotherAssessments = async (motherId) => {
    setLoadingMotherAssessments(true);
    try {
      const { data, error } = await supabase
        .from("risk_assessments")
        .select("*")
        .eq("mother_id", motherId)
        .order("created_at", { ascending: false });

      if (!error) {
        setMotherAssessments(data || []);
      }
    } catch (err) {
      console.error("Error loading assessments:", err);
    } finally {
      setLoadingMotherAssessments(false);
    }
  };

  // Load assessments when mother is selected
  useEffect(() => {
    if (selected?.id) {
      loadMotherAssessments(selected.id);
    }
  }, [selected]);

  const handleSetManualId = () => {
    if (manualAshaId) {
      setAshaWorkerId(parseInt(manualAshaId, 10));
    }
  };

  const handleAssessRisk = async (e) => {
    e.preventDefault();
    if (!assessmentForm.mother_id) {
      setError("Please select a mother");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const payload = {
        mother_id: assessmentForm.mother_id,
        systolic_bp: assessmentForm.systolic_bp
          ? parseInt(assessmentForm.systolic_bp, 10)
          : null,
        diastolic_bp: assessmentForm.diastolic_bp
          ? parseInt(assessmentForm.diastolic_bp, 10)
          : null,
        heart_rate: assessmentForm.heart_rate
          ? parseInt(assessmentForm.heart_rate, 10)
          : null,
        blood_glucose: assessmentForm.blood_glucose
          ? parseFloat(assessmentForm.blood_glucose)
          : null,
        hemoglobin: assessmentForm.hemoglobin
          ? parseFloat(assessmentForm.hemoglobin)
          : null,
        proteinuria: assessmentForm.proteinuria,
        edema: assessmentForm.edema,
        headache: assessmentForm.headache,
        vision_changes: assessmentForm.vision_changes,
        epigastric_pain: assessmentForm.epigastric_pain,
        vaginal_bleeding: assessmentForm.vaginal_bleeding,
        asha_worker_id: ashaWorkerId,
      };

      const response = await apiCall("POST", "/risk/assess", payload);
      setRiskResult(response);

      const telegramMsg = response.telegram_sent
        ? "📱 Report sent to mother!"
        : "";
      setSuccess(`✅ Assessment completed! ${telegramMsg}`);

      await loadMothers();

      setAssessmentForm({
        mother_id: "",
        systolic_bp: "",
        diastolic_bp: "",
        heart_rate: "",
        blood_glucose: "",
        hemoglobin: "",
        proteinuria: 0,
        edema: 0,
        headache: 0,
        vision_changes: 0,
        epigastric_pain: 0,
        vaginal_bleeding: 0,
      });
    } catch (err) {
      setError("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = mothers.filter(
    (m) =>
      m.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.location?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRiskIcon = (risk) => {
    switch (risk) {
      case "HIGH":
        return "🔴";
      case "MODERATE":
        return "🟡";
      default:
        return "🟢";
    }
  };

  const COLORS = { HIGH: "#ef4444", MODERATE: "#f59e0b", LOW: "#10b981" };

  const riskDistData = analytics
    ? [
      { name: "High", value: analytics.high_risk_count || 0 },
      { name: "Moderate", value: analytics.moderate_risk_count || 0 },
      { name: "Low", value: analytics.low_risk_count || 0 },
    ]
    : [];

  // If still loading profile, show loading
  if (loadingProfile) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <Loader className="w-12 h-12 animate-spin mx-auto text-green-600 mb-4" />
          <h1 className="text-xl font-bold text-gray-900">
            Loading ASHA Portal
          </h1>
          <p className="text-gray-600 mt-2">Finding your profile...</p>
        </div>
      </div>
    );
  }

  // If no ASHA worker ID found, show error
  if (!ashaWorkerId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-6">
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
                ? `No ASHA worker found for: ${user.email}`
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
              <li>Ensure your email is registered in the ASHA workers list</li>
              <li>Contact admin to link your account</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar - Mothers List */}
      <div className="w-80 bg-white border-r flex flex-col shadow-lg">
        {/* Header */}
        <div className="bg-gradient-to-br from-green-600 to-green-800 text-white px-5 py-5">
          <div className="flex items-center gap-3">
            <div className="bg-green-500 p-2 rounded-lg">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold">ASHA Portal</h1>
              <p className="text-green-100 text-xs">ID: {ashaWorkerId}</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex border-b">
          <button
            onClick={() => {
              setSelected(null);
              setMainView("register");
            }}
            className={`flex-1 py-3 text-xs font-semibold flex flex-col items-center gap-1 ${mainView === "register"
                ? "text-pink-600 bg-pink-50"
                : "text-gray-500"
              }`}
          >
            <UserPlus className="w-4 h-4" />
            Register
          </button>
          <button
            onClick={() => {
              setSelected(null);
              setMainView("assess");
            }}
            className={`flex-1 py-3 text-xs font-semibold flex flex-col items-center gap-1 ${mainView === "assess"
                ? "text-green-600 bg-green-50"
                : "text-gray-500"
              }`}
          >
            <ClipboardCheck className="w-4 h-4" />
            Assess
          </button>
          <button
            onClick={() => {
              setSelected(null);
              setMainView("stats");
            }}
            className={`flex-1 py-3 text-xs font-semibold flex flex-col items-center gap-1 ${mainView === "stats"
                ? "text-green-600 bg-green-50"
                : "text-gray-500"
              }`}
          >
            <BarChart2 className="w-4 h-4" />
            My Stats
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mx-3 mt-3 p-2 bg-red-50 border border-red-200 rounded-lg text-red-800 text-xs">
            {error}
            <button onClick={() => setError("")} className="float-right">
              ×
            </button>
          </div>
        )}
        {success && (
          <div className="mx-3 mt-3 p-2 bg-green-50 border border-green-200 rounded-lg text-green-800 text-xs">
            {success}
            <button onClick={() => setSuccess("")} className="float-right">
              ×
            </button>
          </div>
        )}

        {/* Search */}
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search mothers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm"
            />
          </div>
        </div>

        {/* Mothers List */}
        <div className="flex-1 overflow-y-auto p-3">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold text-gray-600 uppercase">
              Mothers ({filtered.length})
            </h2>
            <button
              onClick={loadMothers}
              className="text-green-600 hover:text-green-700"
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>

          {loading && mothers.length === 0 ? (
            <div className="text-center py-8">
              <Loader className="w-6 h-6 animate-spin mx-auto text-green-600" />
            </div>
          ) : filtered.length > 0 ? (
            <div className="space-y-2">
              {filtered.map((m) => (
                <div
                  key={m.id}
                  onClick={() => {
                    setSelected(m);
                    setMainView("mother");
                  }}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${selected?.id === m.id
                      ? "border-green-500 bg-green-50"
                      : "border-gray-200 hover:border-green-300"
                    }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-semibold text-gray-900">
                      {m.name}
                    </div>
                    <span className="text-lg">
                      {getRiskIcon(riskMap[m.id] || "LOW")}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3" /> {m.location}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Heart className="w-10 h-10 mx-auto text-gray-300 mb-2" />
              <p className="text-sm">No mothers assigned</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mother Profile View */}
        {mainView === "mother" && selected && (
          <div className="flex flex-col h-full">
            <div className="bg-white border-b px-8 py-6 shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selected.name}
                  </h2>
                  <p className="text-gray-600 mt-1 text-sm flex items-center gap-2">
                    <MapPin className="w-4 h-4" /> {selected.location} · Age{" "}
                    {selected.age}
                  </p>
                </div>
                <div
                  className={`px-4 py-2 rounded-lg font-semibold flex items-center gap-2 ${riskMap[selected.id] === "HIGH"
                      ? "bg-red-100 text-red-700"
                      : riskMap[selected.id] === "MODERATE"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-green-100 text-green-700"
                    }`}
                >
                  <span className="text-xl">
                    {getRiskIcon(riskMap[selected.id])}
                  </span>
                  {riskMap[selected.id] || "LOW"}
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-hidden flex gap-6 p-6">
              {/* Profile Card */}
              <div className="w-72 bg-white rounded-xl shadow border p-5 overflow-y-auto">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <Heart className="w-5 h-5 text-green-600" /> Profile
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="pb-2 border-b">
                    <p className="text-xs text-gray-500">Phone</p>
                    <p className="font-semibold">{selected.phone || "N/A"}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-gray-500">BMI</p>
                      <p className="font-semibold">
                        {selected.bmi?.toFixed(1)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Gravida</p>
                      <p className="font-semibold">{selected.gravida}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Parity</p>
                      <p className="font-semibold">{selected.parity}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">Language</p>
                      <p className="font-semibold capitalize">
                        {selected.preferred_language}
                      </p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setAssessmentForm({
                      ...assessmentForm,
                      mother_id: selected.id,
                    });
                    setMainView("assess");
                  }}
                  className="w-full mt-5 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700"
                >
                  <Activity className="w-4 h-4 inline mr-2" />
                  New Assessment
                </button>
              </div>

              {/* Main Content with Tabs */}
              <div className="flex-1 bg-white rounded-xl shadow border overflow-hidden flex flex-col">
                {/* Tab Header */}
                <div className="bg-gradient-to-r from-green-600 to-green-700 text-white px-5 py-3 flex items-center gap-4">
                  <button
                    onClick={() => setMotherViewTab("history")}
                    className={`px-3 py-1 rounded-lg text-sm font-semibold ${motherViewTab === "history"
                        ? "bg-white/20"
                        : "opacity-70 hover:opacity-100"
                      }`}
                  >
                    📊 Assessments ({motherAssessments.length})
                  </button>
                  <button
                    onClick={() => setMotherViewTab("documents")}
                    className={`px-3 py-1 rounded-lg text-sm font-semibold ${motherViewTab === "documents"
                        ? "bg-white/20"
                        : "opacity-70 hover:opacity-100"
                      }`}
                  >
                    📄 Documents
                  </button>
                  <button
                    onClick={() => setMotherViewTab("chat")}
                    className={`px-3 py-1 rounded-lg text-sm font-semibold ${motherViewTab === "chat"
                        ? "bg-white/20"
                        : "opacity-70 hover:opacity-100"
                      }`}
                  >
                    💬 Chat History
                  </button>
                </div>

                {/* Tab Content */}
                {motherViewTab === "history" ? (
                  <div className="flex-1 overflow-y-auto p-4">
                    {loadingMotherAssessments ? (
                      <div className="text-center py-8">
                        <Loader className="w-6 h-6 animate-spin mx-auto text-green-600" />
                      </div>
                    ) : motherAssessments.length > 0 ? (
                      <div className="space-y-3">
                        {motherAssessments.map((a, idx) => (
                          <div
                            key={a.id || idx}
                            className={`p-4 rounded-lg border-2 ${a.risk_level === "HIGH"
                                ? "bg-red-50 border-red-200"
                                : a.risk_level === "MODERATE"
                                  ? "bg-yellow-50 border-yellow-200"
                                  : "bg-green-50 border-green-200"
                              }`}
                          >
                            <div className="flex justify-between items-start mb-2">
                              <p className="text-xs text-gray-600">
                                📅 {new Date(a.created_at).toLocaleString()}
                              </p>
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-bold ${a.risk_level === "HIGH"
                                    ? "bg-red-200 text-red-800"
                                    : a.risk_level === "MODERATE"
                                      ? "bg-yellow-200 text-yellow-800"
                                      : "bg-green-200 text-green-800"
                                  }`}
                              >
                                {getRiskIcon(a.risk_level)} {a.risk_level} (
                                {(a.risk_score * 100).toFixed(0)}%)
                              </span>
                            </div>

                            <div className="grid grid-cols-4 gap-2 text-xs">
                              {a.systolic_bp && a.diastolic_bp && (
                                <div className="bg-white/60 p-2 rounded text-center">
                                  <p className="text-gray-500">BP</p>
                                  <p className="font-bold">
                                    {a.systolic_bp}/{a.diastolic_bp}
                                  </p>
                                </div>
                              )}
                              {a.heart_rate && (
                                <div className="bg-white/60 p-2 rounded text-center">
                                  <p className="text-gray-500">HR</p>
                                  <p className="font-bold">{a.heart_rate}</p>
                                </div>
                              )}
                              {a.blood_glucose && (
                                <div className="bg-white/60 p-2 rounded text-center">
                                  <p className="text-gray-500">Glucose</p>
                                  <p className="font-bold">{a.blood_glucose}</p>
                                </div>
                              )}
                              {a.hemoglobin && (
                                <div className="bg-white/60 p-2 rounded text-center">
                                  <p className="text-gray-500">Hb</p>
                                  <p className="font-bold">{a.hemoglobin}</p>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <FileText className="w-10 h-10 mx-auto text-gray-300 mb-2" />
                        <p className="text-sm">No assessments yet</p>
                        <p className="text-xs mt-1">
                          Click "New Assessment" to start
                        </p>
                      </div>
                    )}
                  </div>
                ) : motherViewTab === "documents" ? (
                  <DocumentManager
                    motherId={selected.id}
                    motherName={selected.name}
                    uploaderId={ashaWorkerId?.toString()}
                    uploaderRole="ASHA"
                    uploaderName="ASHA Worker"
                  />
                ) : (
                  <div className="flex-1 overflow-hidden">
                    <PatientChatHistory
                      motherId={selected.id}
                      userRole="ASHA"
                      userName="ASHA Worker"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Risk Assessment View */}
        {mainView === "assess" && (
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                  <ClipboardCheck className="w-6 h-6 text-green-600" />
                  Risk Assessment
                </h2>

                <form onSubmit={handleAssessRisk} className="space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Select Mother *
                    </label>
                    <select
                      value={assessmentForm.mother_id}
                      onChange={(e) =>
                        setAssessmentForm({
                          ...assessmentForm,
                          mother_id: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-green-500"
                      required
                    >
                      <option value="">Choose a mother...</option>
                      {mothers.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} - {m.location}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Systolic BP
                      </label>
                      <input
                        type="number"
                        placeholder="120"
                        value={assessmentForm.systolic_bp}
                        onChange={(e) =>
                          setAssessmentForm({
                            ...assessmentForm,
                            systolic_bp: e.target.value,
                          })
                        }
                        className="w-full px-4 py-3 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Diastolic BP
                      </label>
                      <input
                        type="number"
                        placeholder="80"
                        value={assessmentForm.diastolic_bp}
                        onChange={(e) =>
                          setAssessmentForm({
                            ...assessmentForm,
                            diastolic_bp: e.target.value,
                          })
                        }
                        className="w-full px-4 py-3 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Heart Rate (bpm)
                      </label>
                      <input
                        type="number"
                        placeholder="80"
                        value={assessmentForm.heart_rate}
                        onChange={(e) =>
                          setAssessmentForm({
                            ...assessmentForm,
                            heart_rate: e.target.value,
                          })
                        }
                        className="w-full px-4 py-3 border rounded-lg"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Blood Glucose
                      </label>
                      <input
                        type="number"
                        placeholder="100"
                        value={assessmentForm.blood_glucose}
                        onChange={(e) =>
                          setAssessmentForm({
                            ...assessmentForm,
                            blood_glucose: e.target.value,
                          })
                        }
                        className="w-full px-4 py-3 border rounded-lg"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Hemoglobin (g/dL)
                    </label>
                    <input
                      type="number"
                      placeholder="12.0"
                      step="0.1"
                      value={assessmentForm.hemoglobin}
                      onChange={(e) =>
                        setAssessmentForm({
                          ...assessmentForm,
                          hemoglobin: e.target.value,
                        })
                      }
                      className="w-full px-4 py-3 border rounded-lg"
                    />
                  </div>

                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm font-semibold text-gray-700 mb-3">
                      Clinical Symptoms
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { key: "proteinuria", label: "Proteinuria" },
                        { key: "edema", label: "Edema/Swelling" },
                        { key: "headache", label: "Severe Headache" },
                        { key: "vision_changes", label: "Vision Changes" },
                        { key: "epigastric_pain", label: "Epigastric Pain" },
                        { key: "vaginal_bleeding", label: "Vaginal Bleeding" },
                      ].map((s) => (
                        <label
                          key={s.key}
                          className="flex items-center gap-2 text-sm cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={assessmentForm[s.key] === 1}
                            onChange={(e) =>
                              setAssessmentForm({
                                ...assessmentForm,
                                [s.key]: e.target.checked ? 1 : 0,
                              })
                            }
                            className="w-4 h-4 text-green-600 rounded"
                          />
                          {s.label}
                        </label>
                      ))}
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-4 bg-green-600 text-white rounded-lg font-bold text-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? "Assessing..." : "Submit Assessment"}
                  </button>
                </form>

                {riskResult && (
                  <div
                    className={`mt-6 p-5 rounded-lg border-2 ${riskResult.risk_level === "HIGH"
                        ? "bg-red-50 border-red-300"
                        : riskResult.risk_level === "MODERATE"
                          ? "bg-yellow-50 border-yellow-300"
                          : "bg-green-50 border-green-300"
                      }`}
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-3xl">
                        {getRiskIcon(riskResult.risk_level)}
                      </span>
                      <div>
                        <p className="font-bold text-lg">
                          {riskResult.risk_level} RISK
                        </p>
                        <p className="text-sm">
                          Score: {(riskResult.risk_score * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                    {riskResult.risk_factors?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-semibold mb-1">
                          Risk Factors:
                        </p>
                        <ul className="text-sm list-disc pl-5">
                          {riskResult.risk_factors.map((f, i) => (
                            <li key={i}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {riskResult.telegram_sent && (
                      <p className="mt-3 text-sm bg-blue-100 text-blue-800 p-2 rounded">
                        📱 Report sent to mother via Telegram!
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* My Stats View */}
        {mainView === "stats" && (
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                <BarChart2 className="w-6 h-6 text-green-600" />
                My Performance Stats
              </h2>

              {analytics ? (
                <div className="space-y-6">
                  {/* Stats Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white p-5 rounded-xl shadow border-l-4 border-blue-500">
                      <p className="text-3xl font-bold text-blue-600">
                        {analytics.total_mothers}
                      </p>
                      <p className="text-sm text-gray-600">Assigned Mothers</p>
                    </div>
                    <div className="bg-white p-5 rounded-xl shadow border-l-4 border-purple-500">
                      <p className="text-3xl font-bold text-purple-600">
                        {analytics.total_assessments}
                      </p>
                      <p className="text-sm text-gray-600">Assessments Done</p>
                    </div>
                    <div className="bg-white p-5 rounded-xl shadow border-l-4 border-red-500">
                      <p className="text-3xl font-bold text-red-600">
                        {analytics.high_risk_count}
                      </p>
                      <p className="text-sm text-gray-600">High Risk Found</p>
                    </div>
                    <div className="bg-white p-5 rounded-xl shadow border-l-4 border-green-500">
                      <p className="text-3xl font-bold text-green-600">
                        {analytics.low_risk_count}
                      </p>
                      <p className="text-sm text-gray-600">Low Risk</p>
                    </div>
                  </div>

                  <div className="grid lg:grid-cols-2 gap-6">
                    {/* Risk Distribution Chart */}
                    {riskDistData.some((d) => d.value > 0) && (
                      <div className="bg-white p-5 rounded-xl shadow">
                        <h3 className="font-bold text-gray-900 mb-4">
                          Risk Distribution
                        </h3>
                        <ResponsiveContainer width="100%" height={200}>
                          <PieChart>
                            <Pie
                              data={riskDistData}
                              dataKey="value"
                              cx="50%"
                              cy="50%"
                              outerRadius={70}
                              label
                            >
                              <Cell fill={COLORS.HIGH} />
                              <Cell fill={COLORS.MODERATE} />
                              <Cell fill={COLORS.LOW} />
                            </Pie>
                            <Tooltip />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {/* Recent Assessments */}
                    <div className="bg-white p-5 rounded-xl shadow">
                      <h3 className="font-bold text-gray-900 mb-4">
                        Recent Assessments
                      </h3>
                      {analytics.recent_assessments?.length > 0 ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                          {analytics.recent_assessments.map((a) => (
                            <div
                              key={a.id}
                              onClick={() => {
                                setSelectedAssessment(a);
                                setMainView("assessment-detail");
                              }}
                              className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 flex justify-between items-center"
                            >
                              <div>
                                <p className="font-semibold text-sm">
                                  {a.mother_name}
                                </p>
                                <p className="text-xs text-gray-500">
                                  <Calendar className="w-3 h-3 inline mr-1" />
                                  {new Date(a.created_at).toLocaleDateString()}
                                </p>
                              </div>
                              <span
                                className={`px-3 py-1 rounded-full text-xs font-bold ${a.risk_level === "HIGH"
                                    ? "bg-red-100 text-red-700"
                                    : a.risk_level === "MODERATE"
                                      ? "bg-yellow-100 text-yellow-700"
                                      : "bg-green-100 text-green-700"
                                  }`}
                              >
                                {getRiskIcon(a.risk_level)} {a.risk_level}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 text-sm">
                          No assessments yet
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Loader className="w-8 h-8 animate-spin mx-auto text-green-600 mb-4" />
                  <p className="text-gray-500">Loading stats...</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Assessment Detail View */}
        {mainView === "assessment-detail" && selectedAssessment && (
          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-2xl mx-auto">
              <button
                onClick={() => setMainView("stats")}
                className="flex items-center gap-2 text-green-600 hover:text-green-700 mb-6"
              >
                <ChevronLeft className="w-5 h-5" /> Back to Stats
              </button>

              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-4 mb-6 pb-6 border-b">
                  <span className="text-4xl">
                    {getRiskIcon(selectedAssessment.risk_level)}
                  </span>
                  <div>
                    <h2 className="text-xl font-bold">
                      {selectedAssessment.mother_name}
                    </h2>
                    <p className="text-gray-600">
                      <Calendar className="w-4 h-4 inline mr-1" />
                      {new Date(selectedAssessment.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                <div
                  className={`p-4 rounded-lg mb-6 ${selectedAssessment.risk_level === "HIGH"
                      ? "bg-red-50"
                      : selectedAssessment.risk_level === "MODERATE"
                        ? "bg-yellow-50"
                        : "bg-green-50"
                    }`}
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm font-semibold text-gray-600">
                        Risk Level
                      </p>
                      <p className="text-2xl font-bold">
                        {selectedAssessment.risk_level}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-600">
                        Score
                      </p>
                      <p className="text-2xl font-bold">
                        {(selectedAssessment.risk_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-gray-500 text-center">
                  Assessment ID: {selectedAssessment.id?.slice(0, 8)}...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Register New Mother View */}
        {mainView === "register" && (
          <div className="flex-1 overflow-y-auto p-8">
            <MotherRegistrationForm
              assignerId={ashaWorkerId}
              assignerRole="ASHA"
              onSuccess={(newMother) => {
                setSuccess(`✅ Successfully registered: ${newMother.name}`);
                loadMothers();
              }}
            />
          </div>
        )}

        {/* Empty State */}
        {mainView === "mother" && !selected && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-xl font-semibold text-gray-900">
                Select a Mother
              </p>
              <p className="text-gray-600 mt-2">
                Choose from the list or start a new assessment
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
