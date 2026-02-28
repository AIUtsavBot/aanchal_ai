import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import {
    Heart, Baby, ClipboardCheck, AlertTriangle, CheckCircle, Clock,
    User, Thermometer, Activity, Scale, Eye, Droplets, Loader,
    Plus, FileText, Calendar, Stethoscope, RefreshCw, ChevronDown,
    ChevronUp, Edit2, Save, X, UserPlus
} from 'lucide-react';
import { showToast } from '../../utils/FixedPatterns';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const MAX_VISIBLE_ITEMS = 5;
const ITEMS_PER_PAGE = 5;

export const PostnatalAssessments = ({ ashaWorkerId, doctorId, userRole, onUpdate }) => {
    const [activeSubTab, setActiveSubTab] = useState('overview');
    const [mothers, setMothers] = useState([]);
    const [children, setChildren] = useState([]);
    const [selectedMother, setSelectedMother] = useState(null);
    const [selectedChild, setSelectedChild] = useState(null);
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(null);
    const [expandedAssessment, setExpandedAssessment] = useState(null); // 'mother' or 'child'

    // Assessment form states
    const [motherAssessment, setMotherAssessment] = useState({
        assessment_date: new Date().toISOString().split('T')[0],
        days_postpartum: 0,
        // Physical Health
        temperature: '',
        blood_pressure_systolic: '',
        blood_pressure_diastolic: '',
        pulse_rate: '',
        // Postnatal Checks
        uterine_involution: 'normal',
        lochia_status: 'normal',
        episiotomy_wound: 'healing_well',
        cesarean_wound: 'not_applicable',
        breast_condition: 'normal',
        breastfeeding_established: true,
        // Mental Health
        mood_status: 'stable',
        sleep_quality: 'adequate',
        postpartum_depression_risk: 'low',
        bonding_with_baby: 'good',
        // Complications
        fever: false,
        excessive_bleeding: false,
        foul_discharge: false,
        breast_engorgement: false,
        mastitis: false,
        urinary_issues: false,
        // Notes
        notes: '',
        recommendations: '',
        nutrition_advice: '',
        medications: '',
        next_visit_date: '',
        // Risk & Referral
        overall_risk_level: 'low',
        referral_needed: false,
        referral_reason: '',
        referral_facility: ''
    });

    const [childAssessment, setChildAssessment] = useState({
        assessment_date: new Date().toISOString().split('T')[0],
        age_days: 0,
        // Physical Measurements
        weight_kg: '',
        length_cm: '',
        head_circumference_cm: '',
        // Vital Signs
        temperature: '',
        heart_rate: '',
        respiratory_rate: '',
        // Feeding
        feeding_type: 'exclusive_breastfeeding',
        feeding_frequency: '',
        feeding_issues: [],
        // Physical Examination
        skin_color: 'normal',
        jaundice_level: 'none',
        umbilical_cord: 'clean_dry',
        fontanelle: 'normal',
        eyes: 'normal',
        reflexes: 'present',
        muscle_tone: 'normal',
        // Danger Signs
        not_feeding_well: false,
        convulsions: false,
        fast_breathing: false,
        chest_indrawing: false,
        high_fever: false,
        hypothermia: false,
        jaundice_extending: false,
        umbilical_infection: false,
        // Notes
        notes: '',
        recommendations: '',
        nutrition_advice: '',
        medications: '',
        next_visit_date: '',
        // Risk & Referral
        overall_risk_level: 'low',
        referral_needed: false,
        referral_reason: '',
        referral_facility: ''
    });

    const [newChild, setNewChild] = useState({
        name: '',
        birth_date: new Date().toISOString().split('T')[0],
        gender: 'male',
        birth_weight_kg: '',
        mother_id: ''
    });

    useEffect(() => {
        const abortController = new AbortController();
        loadData(abortController.signal);

        return () => {
            abortController.abort();
        };
    }, [ashaWorkerId, doctorId]);

    const loadData = async (signal = null) => {
        setLoading(true);
        try {
            // Use backend API instead of direct Supabase calls
            const { postnatalAPI } = await import('../../services/api.js');

            // Load postnatal mothers via API (cached on backend)
            const mothersResponse = await postnatalAPI.getMothers(ashaWorkerId, doctorId);
            setMothers(mothersResponse.mothers || []);

            // Load children if we have mothers
            if (mothersResponse.mothers && mothersResponse.mothers.length > 0) {
                try {
                    const childrenResponse = await postnatalAPI.getChildren(
                        null, // mother_id (get all)
                        ashaWorkerId,
                        doctorId
                    );
                    setChildren(childrenResponse.children || []);
                } catch (childErr) {
                    console.log('Children fetch error:', childErr);
                    setChildren([]);
                }
            }

        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error loading postnatal data:', err);
                // Still try to load from Supabase as fallback
                try {
                    let query = supabase
                        .from('mothers')
                        .select('*')
                        .eq('status', 'postnatal');

                    if (signal) query = query.abortSignal(signal);
                    if (ashaWorkerId) query = query.eq('asha_worker_id', ashaWorkerId);
                    if (doctorId) query = query.eq('doctor_id', doctorId);

                    const { data: mothersData } = await query;
                    setMothers(mothersData || []);
                } catch (fallbackErr) {
                    console.error('Fallback error:', fallbackErr);
                }
            }
        } finally {
            setLoading(false);
        }
    };

    const loadAssessments = async (motherId = null, childId = null) => {
        if (!motherId && !childId) return;

        try {
            // Use backend API for cached assessment history
            const { postnatalAPI } = await import('../../services/api.js');
            const response = await postnatalAPI.getAssessmentHistory(motherId, childId);
            setAssessments(response.assessments || []);
        } catch (err) {
            console.error('Error loading assessments:', err);
            // Fallback to direct Supabase query
            try {
                let query = supabase.from('postnatal_assessments').select('*');

                if (motherId) query = query.eq('mother_id', motherId);
                if (childId) query = query.eq('child_id', childId);

                query = query.order('assessment_date', { ascending: false });

                const { data } = await query;
                setAssessments(data || []);
            } catch (fallbackErr) {
                console.error('Fallback error:', fallbackErr);
                setAssessments([]);
            }
        }
    };

    const cleanData = (data) => {
        const cleaned = { ...data };
        const numberFields = [
            'age_days', 'weight_kg', 'length_cm', 'head_circumference_cm',
            'temperature', 'heart_rate', 'respiratory_rate',
            'blood_pressure_systolic', 'blood_pressure_diastolic', 'pulse_rate'
        ];

        Object.keys(cleaned).forEach(key => {
            if (cleaned[key] === '') {
                cleaned[key] = null;
            } else if (numberFields.includes(key) && cleaned[key] !== null) {
                cleaned[key] = Number(cleaned[key]);
            }
        });
        return cleaned;
    };

    const submitMotherAssessment = async () => {
        if (!selectedMother) return;

        setLoading(true);
        try {
            // Use backend API for assessment creation
            const { postnatalAPI } = await import('../../services/api.js');

            const assessmentData = {
                mother_id: selectedMother.id,
                assessor_id: ashaWorkerId || doctorId,
                assessor_role: userRole,
                ...motherAssessment
            };

            await postnatalAPI.createMotherAssessment(assessmentData);

            // Success notification (non-blocking)
            const notification = document.createElement('div');
            notification.textContent = '✅ Assessment saved successfully!';
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#10b981;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 3000);

            setShowForm(null);
            await loadAssessments(selectedMother.id);
            if (onUpdate) onUpdate();
        } catch (err) {
            console.error('Error saving assessment:', err);

            // Error notification (non-blocking)
            const notification = document.createElement('div');
            notification.textContent = `❌ Failed to save: ${err.message || 'Unknown error'}`;
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#ef4444;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 4000);
        } finally {
            setLoading(false);
        }
    };

    const submitChildAssessment = async () => {
        if (!selectedChild) return;

        setLoading(true);
        try {
            const assessmentData = cleanData({
                child_id: selectedChild.id,
                mother_id: selectedChild.mother_id,
                // assessment_type is added by backend
                assessor_id: ashaWorkerId || doctorId,
                assessor_role: userRole,
                ...childAssessment
            });

            // Use backend API
            const { postnatalAPI } = await import('../../services/api.js');
            await postnatalAPI.createChildAssessment(assessmentData);

            // Success notification (non-blocking)
            const notification = document.createElement('div');
            notification.textContent = 'Child assessment saved successfully!';
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#10b981;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 3000);

            setShowForm(null);
            await loadAssessments(null, selectedChild.id);
            if (onUpdate) onUpdate();
        } catch (err) {
            console.error('Error saving assessment:', err);

            // Error notification (non-blocking)
            const notification = document.createElement('div');
            notification.textContent = `Failed to save: ${err.message || 'Unknown error'}`;
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#ef4444;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 4000);
        } finally {
            setLoading(false);
        }
    };

    const handleRegisterChild = async () => {
        if (!newChild.name || !newChild.mother_id || !newChild.birth_date || !newChild.gender) {
            showToast('Please fill all required fields', 'error');
            return;
        }

        setLoading(true);
        try {
            const { postnatalAPI } = await import('../../services/api.js');

            const childData = {
                ...newChild,
                asha_worker_id: ashaWorkerId,
                doctor_id: doctorId,
                birth_weight_kg: newChild.birth_weight_kg ? parseFloat(newChild.birth_weight_kg) : null
            };

            await postnatalAPI.registerChild(childData);

            // Success notification
            const notification = document.createElement('div');
            notification.textContent = '✅ Child registered successfully!';
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#10b981;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 3000);

            setShowForm(null);
            setNewChild({
                name: '',
                birth_date: new Date().toISOString().split('T')[0],
                gender: 'male',
                birth_weight_kg: '',
                mother_id: ''
            });

            // Refresh list
            loadData();
            if (onUpdate) onUpdate();

        } catch (err) {
            console.error('Error registering child:', err);
            // Error notification
            const notification = document.createElement('div');
            notification.textContent = `❌ Failed to register: ${err.response?.data?.detail || err.message}`;
            notification.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 24px;background:#ef4444;color:white;border-radius:8px;z-index:10000';
            document.body.appendChild(notification);
            setTimeout(() => document.body.removeChild(notification), 5000);
        } finally {
            setLoading(false);
        }
    };

    const getRiskBadge = (level) => {
        const badges = {
            low: { color: '#10b981', bg: '#d1fae5', label: 'Low Risk' },
            medium: { color: '#f59e0b', bg: '#fef3c7', label: 'Medium Risk' },
            high: { color: '#ef4444', bg: '#fee2e2', label: 'High Risk' },
            critical: { color: '#ef4444', bg: '#fee2e2', label: 'Critical' }
        };
        const badge = badges[level?.toLowerCase()] || badges.low;
        return (
            <span style={{
                background: badge.bg,
                color: badge.color,
                padding: '0.25rem 0.75rem',
                borderRadius: '1rem',
                fontSize: '0.75rem',
                fontWeight: 600
            }}>
                {badge.label}
            </span>
        );
    };

    const renderAssessmentCard = (a, type) => {
        const riskLevel = a.overall_risk_level?.toUpperCase() || 'LOW';
        let emoji = "✅";
        let textClass = "bg-green-200 text-emerald-700";

        if (riskLevel === 'HIGH' || riskLevel === 'CRITICAL') {
            emoji = "🚨";
            textClass = "bg-red-200 text-red-800";
        } else if (riskLevel === 'MEDIUM' || riskLevel === 'MODERATE') {
            emoji = "⚠️";
            textClass = "bg-yellow-200 text-amber-700";
        }

        // Type-based styling
        const typeColor = type === 'mother' ? 'purple' : 'blue';
        const typeBg = type === 'mother' ? 'bg-blue-50/50' : 'bg-sky-50/50';
        const typeBorder = type === 'mother' ? 'border-sky-100' : 'border-blue-100';

        // Risk still overrides border if high/critical
        let borderClass = typeBorder;
        if (riskLevel === 'HIGH' || riskLevel === 'CRITICAL') borderClass = 'border-red-300 bg-red-50/50';
        else if (riskLevel === 'MEDIUM' || riskLevel === 'MODERATE') borderClass = 'border-yellow-300 bg-amber-50/50';
        else borderClass = `${typeBorder} ${typeBg}`;

        return (
            <div key={a.id || Math.random()} className={`mb-4 p-4 rounded-lg border ${borderClass} shadow-sm transition-all hover:shadow-md shadow-blue-500/5`}>
                {/* Header */}
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <p className="text-xs text-slate-500 flex items-center gap-2">
                            <span className="flex items-center gap-1"><Calendar size={12} /> {new Date(a.assessment_date).toLocaleDateString()}</span>
                            {type === 'mother' && <span className="bg-white/50 px-1.5 rounded border border-blue-200/40">Day {a.days_postpartum !== undefined && a.days_postpartum !== null ? a.days_postpartum : '?'}</span>}
                            {type === 'child' && <span className="bg-white/50 px-1.5 rounded border border-blue-200/40">Age: {a.age_days !== undefined && a.age_days !== null ? a.age_days : '?'} days</span>}
                        </p>
                        <p className="text-xs text-blue-600 font-medium mt-1 flex items-center gap-1">
                            {a.assessor_role === 'doctor' ? '👨‍⚕️' : '👩‍⚕️'} {a.assessor_role === 'doctor' ? 'Doctor Checked' : 'ASHA Checked'}
                        </p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${textClass}`}>
                        {emoji} {riskLevel}
                    </div>
                </div>

                {/* Vitals Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm mb-3">
                    {type === 'mother' ? (
                        <>
                            {a.blood_pressure_systolic && (
                                <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-slate-400">BP</p>
                                    <p className="font-bold">{a.blood_pressure_systolic}/{a.blood_pressure_diastolic}</p>
                                </div>
                            )}
                            {a.temperature && (
                                <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-slate-400">Temp</p>
                                    <p className="font-bold">{a.temperature}°C</p>
                                </div>
                            )}
                            {a.pulse_rate && (
                                <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-slate-400">Pulse</p>
                                    <p className="font-bold">{a.pulse_rate} bpm</p>
                                </div>
                            )}
                            <div className="bg-white/60 p-2 rounded">
                                <p className="text-xs text-slate-400">Involution</p>
                                <p className="font-medium">{a.uterine_involution?.replace('_', ' ') || '-'}</p>
                            </div>
                        </>
                    ) : (
                        <>
                            {a.weight_kg && (
                                <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-slate-400">Weight</p>
                                    <p className="font-bold">{a.weight_kg} kg</p>
                                </div>
                            )}
                            {a.temperature && (
                                <div className="bg-white/60 p-2 rounded">
                                    <p className="text-xs text-slate-400">Temp</p>
                                    <p className="font-bold">{a.temperature}°C</p>
                                </div>
                            )}
                            <div className="bg-white/60 p-2 rounded">
                                <p className="text-xs text-slate-400">Feeding</p>
                                <p className="font-medium truncate">{a.feeding_type?.replace('_', ' ') || '-'}</p>
                            </div>
                            <div className="bg-white/60 p-2 rounded">
                                <p className="text-xs text-slate-400">Jaundice</p>
                                <p className="font-medium">{a.jaundice_level?.replace('_', ' ') || 'None'}</p>
                            </div>
                        </>
                    )}
                </div>

                {/* Danger Signs */}
                {type === 'mother' ? (
                    (a.fever || a.excessive_bleeding || a.foul_discharge || a.breast_engorgement || a.mastitis || a.urinary_issues) && (
                        <div className="bg-red-100/50 p-2 rounded text-xs mb-3 border border-red-200">
                            <p className="font-bold text-red-800 mb-1 flex items-center gap-1">⚠️ Danger Signs Detected:</p>
                            <div className="flex flex-wrap gap-1">
                                {a.fever && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Fever</span>}
                                {a.excessive_bleeding && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Bleeding</span>}
                                {a.foul_discharge && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Foul Discharge</span>}
                                {a.breast_engorgement && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Engorgement</span>}
                                {a.mastitis && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Mastitis</span>}
                                {a.urinary_issues && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Urinary Issues</span>}
                            </div>
                        </div>
                    )
                ) : (
                    (a.not_feeding_well || a.convulsions || a.fast_breathing || a.chest_indrawing || a.high_fever || a.hypothermia || a.jaundice_extending || a.umbilical_infection) && (
                        <div className="bg-red-100/50 p-2 rounded text-xs mb-3 border border-red-200">
                            <p className="font-bold text-red-800 mb-1 flex items-center gap-1">⚠️ IMNCI Danger Signs:</p>
                            <div className="flex flex-wrap gap-1">
                                {a.not_feeding_well && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Not Feeding</span>}
                                {a.convulsions && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Convulsions</span>}
                                {a.fast_breathing && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Fast Breathing</span>}
                                {a.chest_indrawing && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Chest Indrawing</span>}
                                {a.high_fever && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">High Fever</span>}
                                {a.hypothermia && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Hypothermia</span>}
                                {a.jaundice_extending && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Ext. Jaundice</span>}
                                {a.umbilical_infection && <span className="bg-white/60 backdrop-blur-lg px-2 py-0.5 rounded text-red-700 border border-red-100">Infection</span>}
                            </div>
                        </div>
                    )
                )}

                {/* Plan Section */}
                <div className="space-y-2 border-t border-blue-200/40/50 pt-2">
                    {/* Medications */}
                    {a.medications && (
                        <div className="bg-blue-50/50 p-2 rounded text-xs">
                            <p className="font-bold text-blue-700 mb-1">💊 Medications</p>
                            <p className="text-slate-600">{a.medications}</p>
                        </div>
                    )}
                    {/* Nutrition */}
                    {a.nutrition_advice && (
                        <div className="bg-emerald-50/50 p-2 rounded text-xs">
                            <p className="font-bold text-emerald-700 mb-1">🍎 Nutrition</p>
                            <p className="text-slate-600">{a.nutrition_advice}</p>
                        </div>
                    )}
                    {/* Notes */}
                    {a.notes && (
                        <div className="bg-blue-50/30 p-2 rounded text-xs">
                            <p className="font-bold text-slate-600 mb-1">📝 Notes</p>
                            <p className="text-slate-500">{a.notes}</p>
                        </div>
                    )}
                    {/* Next Visit */}
                    {a.next_visit_date && (
                        <div className="bg-sky-50/50 p-2 rounded text-xs flex justify-between items-center">
                            <span className="font-bold text-sky-700">📅 Next Visit:</span>
                            <span className="text-blue-900 font-medium">
                                {new Date(a.next_visit_date).toLocaleDateString()}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    // Overview Tab
    const renderOverview = () => (
        <div className="assessment-overview">
            <div className="overview-header">
                <h3>📋 Postnatal Care Overview</h3>
                <p>Monitor health of mothers and children after delivery</p>
            </div>

            <div className="overview-stats">
                <div className="stat-box mothers">
                    <div className="stat-icon">👩</div>
                    <div className="stat-info">
                        <h4>{mothers.length}</h4>
                        <p>Postnatal Mothers</p>
                    </div>
                </div>
                <div className="stat-box children">
                    <div className="stat-icon">👶</div>
                    <div className="stat-info">
                        <h4>{children.length}</h4>
                        <p>Registered Children</p>
                    </div>
                </div>
                <div className="stat-box assessments">
                    <div className="stat-icon">📝</div>
                    <div className="stat-info">
                        <h4>{assessments.length}</h4>
                        <p>Total Assessments</p>
                    </div>
                </div>
            </div>

            <div className="assessment-schedule">
                <h4>📅 Recommended Postnatal Visit Schedule</h4>
                <div className="schedule-timeline">
                    <div className="timeline-item">
                        <div className="timeline-marker day-1">Day 1</div>
                        <div className="timeline-content">
                            <strong>First Check (Within 24 hours)</strong>
                            <p>Birth vitals, feeding initiation, cord care</p>
                        </div>
                    </div>
                    <div className="timeline-item">
                        <div className="timeline-marker day-3">Day 3</div>
                        <div className="timeline-content">
                            <strong>Second Check</strong>
                            <p>Jaundice screening, weight check, breastfeeding assessment</p>
                        </div>
                    </div>
                    <div className="timeline-item">
                        <div className="timeline-marker day-7">Day 7</div>
                        <div className="timeline-content">
                            <strong>Third Check</strong>
                            <p>Cord separation, immunization (BCG, OPV, Hep-B)</p>
                        </div>
                    </div>
                    <div className="timeline-item">
                        <div className="timeline-marker week-6">Week 6</div>
                        <div className="timeline-content">
                            <strong>Final Postnatal Check</strong>
                            <p>Complete mother-child assessment, immunization schedule</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderClinicalProfile = (mother) => (
        <div className="bg-white/60 backdrop-blur-lg rounded-xl shadow-md shadow-blue-500/5 border border-blue-200/40 p-5 overflow-y-auto mb-4 flex-shrink-0" style={{ width: '280px' }}>
            <h3 className="text-lg font-bold text-slate-800 mb-5 flex items-center gap-2">
                <Activity className="w-5 h-5 text-sky-600" />
                Clinical Profile
            </h3>
            <div className="space-y-4 text-sm">
                <div className="pb-3 border-b">
                    <label className="text-xs font-bold text-slate-400 uppercase">Phone</label>
                    <p className="text-slate-800 font-semibold mt-1">{mother.phone || "N/A"}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Age</label>
                        <p className="text-slate-800 font-semibold mt-1">{mother.age}</p>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Gravida</label>
                        <p className="text-slate-800 font-semibold mt-1">{mother.gravida || '-'}</p>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Parity</label>
                        <p className="text-slate-800 font-semibold mt-1">{mother.parity || '-'}</p>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Language</label>
                        <p className="text-slate-800 font-semibold mt-1 capitalize">{mother.preferred_language || '-'}</p>
                    </div>
                </div>
                {mother.delivery_date && (
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Delivery Date</label>
                        <p className="text-slate-800 font-semibold mt-1">
                            {new Date(mother.delivery_date).toLocaleDateString()}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );




    const renderChildClinicalProfile = (child) => (
        <div className="bg-white/60 backdrop-blur-lg rounded-xl shadow-md shadow-blue-500/5 border border-blue-200/40 p-5 overflow-y-auto mb-4 flex-shrink-0" style={{ width: '280px' }}>
            <h3 className="text-lg font-bold text-slate-800 mb-5 flex items-center gap-2">
                <Baby className="w-5 h-5 text-sky-600" />
                Child Profile
            </h3>
            <div className="space-y-4 text-sm">
                <div className="pb-3 border-b">
                    <label className="text-xs font-bold text-slate-400 uppercase">Name</label>
                    <p className="text-slate-800 font-semibold mt-1">{child.name}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 pb-3 border-b">
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Gender</label>
                        <p className="text-slate-800 font-semibold mt-1 capitalize">{child.gender}</p>
                    </div>
                    <div>
                        <label className="text-xs font-bold text-slate-400 uppercase">Birth Weight</label>
                        <p className="text-slate-800 font-semibold mt-1">{child.birth_weight_kg ? `${child.birth_weight_kg} kg` : 'N/A'}</p>
                    </div>
                </div>
                <div>
                    <label className="text-xs font-bold text-slate-400 uppercase">Date of Birth</label>
                    <p className="text-slate-800 font-semibold mt-1">
                        {child.birth_date ? new Date(child.birth_date).toLocaleDateString() : 'N/A'}
                    </p>
                </div>
            </div>
        </div>
    );


    // Mother Assessments Tab
    const renderMotherAssessments = () => (
        <div className="mother-assessments">
            <div className="section-header">
                <h3>👩 Mother's Postnatal Health</h3>
                <p>Monitor recovery, breastfeeding, and mental health</p>
            </div>

            {/* Mother List */}
            <div className="patient-list">
                {mothers.length === 0 ? (
                    <div className="empty-state">
                        <User size={48} />
                        <p>No postnatal mothers found</p>
                        <span>Mothers will appear here after delivery completion</span>
                    </div>
                ) : (
                    <div className="patient-cards">
                        {mothers.map(mother => (
                            <div
                                key={mother.id}
                                className={`patient-card ${selectedMother?.id === mother.id ? 'selected' : ''}`}
                                onClick={() => {
                                    setSelectedMother(mother);
                                    loadAssessments(mother.id);
                                }}
                            >
                                <div className="patient-avatar">
                                    {mother.name?.charAt(0) || 'M'}
                                </div>
                                <div className="patient-info">
                                    <h4>{mother.name}</h4>
                                    <p>Age: {mother.age} · {mother.location}</p>
                                </div>
                                <div className="patient-status">
                                    {getRiskBadge('low')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Assessment Form / Details */}
            {selectedMother && (
                <div className="assessment-panel">
                    {/* Header */}
                    <div className="bg-white/60 backdrop-blur-lg border-b border-blue-200/40 px-8 py-6 shadow-sm mb-6 rounded-lg">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3">
                                    <h2 className="text-2xl font-bold text-slate-800">{selectedMother.name}</h2>
                                    <span className="bg-sky-100 text-blue-600 px-3 py-1 rounded-full text-xs font-bold border border-sky-200 uppercase tracking-wide">
                                        Postnatal
                                    </span>
                                </div>
                                <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm">
                                    <Clock className="w-4 h-4" /> Delivered: {selectedMother.delivery_date ? new Date(selectedMother.delivery_date).toLocaleDateString() : 'N/A'} · Location: {selectedMother.location}
                                </p>
                            </div>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSelectedMother(null)}
                                    className="px-4 py-2 rounded-lg font-semibold text-sm bg-blue-50/40 text-slate-600 flex items-center gap-2 hover:bg-blue-100/50"
                                >
                                    <X size={16} /> Close
                                </button>
                            </div>
                        </div>

                        {/* Tab buttons */}
                        <div className="flex gap-3 mt-4 flex-wrap">
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm !== 'mother' ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white" : "bg-blue-50/40 text-slate-600"}`}
                                onClick={() => setShowForm(null)}
                            >
                                <FileText className="w-4 h-4" /> Assessment History
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm === 'mother' ? "bg-green-600 text-white" : "bg-blue-50/40 text-slate-600"}`}
                                onClick={() => setShowForm('mother')}
                            >
                                <Plus className="w-4 h-4" /> New Assessment
                            </button>
                        </div>
                    </div>

                    <div className="flex flex-col lg:flex-row gap-6 items-start">
                        {/* Left Panel: Clinical Profile */}
                        {renderClinicalProfile(selectedMother)}

                        {/* Right Panel: Content */}
                        <div className="flex-1 min-w-0 bg-white/60 backdrop-blur-lg rounded-xl shadow-md shadow-blue-500/5 border border-blue-200/40 overflow-y-auto flex flex-col p-6">
                            {showForm === 'mother' ? (
                                <div className="assessment-form">
                                    <h5>📝 Mother Postnatal Assessment Form</h5>
                                    {/* Form Fields Injected Here */}
                                    <div className="form-section">
                                        <h6>Physical Health</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Temperature (°C)</label>
                                                <input type="number" step="0.1" value={motherAssessment.temperature} onChange={e => setMotherAssessment({ ...motherAssessment, temperature: e.target.value })} placeholder="e.g., 37.0" />
                                            </div>
                                            <div className="form-field">
                                                <label>BP (Systolic)</label>
                                                <input type="number" value={motherAssessment.blood_pressure_systolic} onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_systolic: e.target.value })} placeholder="e.g., 120" />
                                            </div>
                                            <div className="form-field">
                                                <label>BP (Diastolic)</label>
                                                <input type="number" value={motherAssessment.blood_pressure_diastolic} onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_diastolic: e.target.value })} placeholder="e.g., 80" />
                                            </div>
                                            <div className="form-field">
                                                <label>Pulse Rate</label>
                                                <input type="number" value={motherAssessment.pulse_rate} onChange={e => setMotherAssessment({ ...motherAssessment, pulse_rate: e.target.value })} placeholder="bpm" />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Postnatal Recovery</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Uterine Involution</label>
                                                <select value={motherAssessment.uterine_involution} onChange={e => setMotherAssessment({ ...motherAssessment, uterine_involution: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="subinvolution">Subinvolution</option>
                                                    <option value="tender">Tender</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Lochia Status</label>
                                                <select value={motherAssessment.lochia_status} onChange={e => setMotherAssessment({ ...motherAssessment, lochia_status: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="foul_smelling">Foul Smelling</option>
                                                    <option value="excessive">Excessive</option>
                                                    <option value="absent">Absent</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Breast Condition</label>
                                                <select value={motherAssessment.breast_condition} onChange={e => setMotherAssessment({ ...motherAssessment, breast_condition: e.target.value })}>
                                                    <option value="normal">Normal</option>
                                                    <option value="engorged">Engorged</option>
                                                    <option value="cracked_nipples">Cracked Nipples</option>
                                                    <option value="mastitis">Mastitis Signs</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Episiotomy Wound</label>
                                                <select value={motherAssessment.episiotomy_wound} onChange={e => setMotherAssessment({ ...motherAssessment, episiotomy_wound: e.target.value })}>
                                                    <option value="healing_well">Healing Well</option>
                                                    <option value="infected">Infected</option>
                                                    <option value="dehisced">Dehisced (Open)</option>
                                                    <option value="not_applicable">N/A</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>C-Section Wound</label>
                                                <select value={motherAssessment.cesarean_wound} onChange={e => setMotherAssessment({ ...motherAssessment, cesarean_wound: e.target.value })}>
                                                    <option value="healing_well">Healing Well</option>
                                                    <option value="infected">Infected</option>
                                                    <option value="dehisced">Dehisced</option>
                                                    <option value="not_applicable">N/A</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Breastfeeding Established?</label>
                                                <div className="toggle-switch">
                                                    <label>
                                                        <input type="checkbox" checked={motherAssessment.breastfeeding_established} onChange={e => setMotherAssessment({ ...motherAssessment, breastfeeding_established: e.target.checked })} />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{motherAssessment.breastfeeding_established ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Mental Health (PPD Screening)</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Mood Status</label>
                                                <select value={motherAssessment.mood_status} onChange={e => setMotherAssessment({ ...motherAssessment, mood_status: e.target.value })}>
                                                    <option value="stable">Stable & Happy</option>
                                                    <option value="anxious">Anxious</option>
                                                    <option value="sad">Persistently Sad</option>
                                                    <option value="overwhelmed">Overwhelmed</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>PPD Risk</label>
                                                <select value={motherAssessment.postpartum_depression_risk} onChange={e => setMotherAssessment({ ...motherAssessment, postpartum_depression_risk: e.target.value })}>
                                                    <option value="low">Low</option>
                                                    <option value="medium">Medium</option>
                                                    <option value="high">High</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Sleep Quality</label>
                                                <select value={motherAssessment.sleep_quality} onChange={e => setMotherAssessment({ ...motherAssessment, sleep_quality: e.target.value })}>
                                                    <option value="adequate">Adequate</option>
                                                    <option value="poor">Poor</option>
                                                    <option value="insomnia">Insomnia</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Bonding with Baby</label>
                                                <select value={motherAssessment.bonding_with_baby} onChange={e => setMotherAssessment({ ...motherAssessment, bonding_with_baby: e.target.value })}>
                                                    <option value="good">Good</option>
                                                    <option value="developing">Developing</option>
                                                    <option value="poor">Poor/Detached</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Risk Assessment & Referral</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Overall Risk Level</label>
                                                <select value={motherAssessment.overall_risk_level} onChange={e => setMotherAssessment({ ...motherAssessment, overall_risk_level: e.target.value })} className={`risk-select ${motherAssessment.overall_risk_level}`}>
                                                    <option value="low">Low Risk</option>
                                                    <option value="medium">Medium Risk</option>
                                                    <option value="high">High Risk</option>
                                                    <option value="critical">Critical</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Referral Needed?</label>
                                                <div className="toggle-switch">
                                                    <label>
                                                        <input type="checkbox" checked={motherAssessment.referral_needed} onChange={e => setMotherAssessment({ ...motherAssessment, referral_needed: e.target.checked })} />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{motherAssessment.referral_needed ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                            {motherAssessment.referral_needed && (
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Referral Facility</label>
                                                        <input type="text" value={motherAssessment.referral_facility} onChange={e => setMotherAssessment({ ...motherAssessment, referral_facility: e.target.value })} placeholder="e.g. District Hospital" />
                                                    </div>
                                                    <div className="form-field">
                                                        <label>Reason for Referral</label>
                                                        <input type="text" value={motherAssessment.referral_reason} onChange={e => setMotherAssessment({ ...motherAssessment, referral_reason: e.target.value })} placeholder="Reason..." />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Danger Signs (Check if present)</h6>
                                        <div className="checkbox-grid">
                                            {[
                                                { key: 'fever', label: 'High Fever (>38°C)' },
                                                { key: 'excessive_bleeding', label: 'Excessive Bleeding' },
                                                { key: 'foul_discharge', label: 'Foul-smelling Discharge' },
                                                { key: 'breast_engorgement', label: 'Breast Engorgement' },
                                                { key: 'mastitis', label: 'Signs of Mastitis' },
                                                { key: 'urinary_issues', label: 'Urinary Problems' }
                                            ].map(item => (
                                                <label key={item.key} className="checkbox-item">
                                                    <input type="checkbox" checked={motherAssessment[item.key]} onChange={e => setMotherAssessment({ ...motherAssessment, [item.key]: e.target.checked })} />
                                                    <span>{item.label}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>{userRole === 'doctor' ? 'Notes, Nutrition & Medications' : 'Remarks'}</h6>
                                        {userRole === 'doctor' ? (
                                            <>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Clinical Notes</label>
                                                        <textarea value={motherAssessment.notes} onChange={e => setMotherAssessment({ ...motherAssessment, notes: e.target.value })} placeholder="Enter observations..." rows={3} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Recommendations</label>
                                                        <textarea value={motherAssessment.recommendations} onChange={e => setMotherAssessment({ ...motherAssessment, recommendations: e.target.value })} placeholder="Enter recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Nutrition Advice</label>
                                                        <textarea value={motherAssessment.nutrition_advice} onChange={e => setMotherAssessment({ ...motherAssessment, nutrition_advice: e.target.value })} placeholder="Dietary recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Medications</label>
                                                        <textarea value={motherAssessment.medications} onChange={e => setMotherAssessment({ ...motherAssessment, medications: e.target.value })} placeholder="Prescribed medicines..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Next Visit Date</label>
                                                        <input type="date" min={new Date().toISOString().split('T')[0]} value={motherAssessment.next_visit_date} onChange={e => setMotherAssessment({ ...motherAssessment, next_visit_date: e.target.value })} />
                                                    </div>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="form-row">
                                                <div className="form-field full">
                                                    <label>Remarks</label>
                                                    <textarea value={motherAssessment.notes} onChange={e => setMotherAssessment({ ...motherAssessment, notes: e.target.value })} placeholder="Enter remarks..." rows={3} />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="form-actions">
                                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                                            <X size={16} /> Cancel
                                        </button>
                                        <button className="btn-primary" onClick={submitMotherAssessment}>
                                            <Save size={16} /> Save Assessment
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="assessment-history">
                                    <div className="flex justify-between items-center mb-4">
                                        <h5>📜 Assessment History</h5>
                                        <span className="text-xs text-slate-400 bg-blue-50/40 px-2 py-1 rounded">Latest on top</span>
                                    </div>
                                    {assessments.length === 0 ? (
                                        <div className="text-center py-8 text-slate-400">
                                            <ClipboardCheck size={32} className="mx-auto mb-2 opacity-50" />
                                            <p>No assessments recorded yet</p>
                                        </div>
                                    ) : (
                                        <div className="history-list space-y-4">
                                            {assessments.map((a, i) => renderAssessmentCard(a, 'mother'))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );


    // Child Assessments Tab
    const renderChildAssessments = () => (
        <div className="child-assessments">
            <div className="section-header">
                <h3>👶 Child Health Checks</h3>
                <p>Monitor newborn and infant health, growth, and development</p>
                <button
                    className="btn-primary"
                    style={{ marginTop: '10px' }}
                    onClick={() => setShowForm('register_child')}
                >
                    <UserPlus size={16} /> Register Child
                </button>
            </div>

            {/* Child Registration Form */}
            {showForm === 'register_child' && (
                <div className="assessment-panel">
                    <div className="panel-header">
                        <h4>👶 Register New Child</h4>
                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                            <X size={16} /> Cancel
                        </button>
                    </div>
                    <div className="assessment-form">
                        <div className="form-section">
                            <h6>Child Details</h6>
                            <div className="form-row">
                                <div className="form-field">
                                    <label>Name</label>
                                    <input
                                        type="text"
                                        value={newChild.name}
                                        onChange={e => setNewChild({ ...newChild, name: e.target.value })}
                                        placeholder="Enter child name"
                                    />
                                </div>
                                <div className="form-field">
                                    <label>Birth Date *</label>
                                    <input
                                        type="date"
                                        max={new Date().toISOString().split('T')[0]}
                                        value={newChild.birth_date}
                                        onChange={e => setNewChild({ ...newChild, birth_date: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-field">
                                    <label>Gender *</label>
                                    <select
                                        value={newChild.gender}
                                        onChange={e => setNewChild({ ...newChild, gender: e.target.value })}
                                    >
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                <div className="form-field">
                                    <label>Birth Weight (kg)</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={newChild.birth_weight_kg}
                                        onChange={e => setNewChild({ ...newChild, birth_weight_kg: e.target.value })}
                                        placeholder="e.g. 3.2"
                                    />
                                </div>
                            </div>
                            <div className="form-actions">
                                <button className="btn-secondary" onClick={() => setShowForm(null)}>Cancel</button>
                                <button className="btn-primary" onClick={handleRegisterChild}>Register Child</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Child List */}
            <div className="patient-list">
                {children.length === 0 ? (
                    <div className="empty-state">
                        <Baby size={48} />
                        <p>No children registered yet</p>
                        <span>Children will appear after being added during delivery completion or registration</span>
                    </div>
                ) : (
                    <div className="patient-cards">
                        {children.map(child => (
                            <div
                                key={child.id}
                                className={`patient-card child ${selectedChild?.id === child.id ? 'selected' : ''}`}
                                onClick={() => {
                                    setSelectedChild(child);
                                    loadAssessments(null, child.id);
                                }}
                            >
                                <div className="patient-avatar child">
                                    {child.gender === 'male' ? '👦' : '👧'}
                                </div>
                                <div className="patient-info">
                                    <h4>{child.name}</h4>
                                    <p>Born: {child.birth_date}</p>
                                    <p>Weight: {child.birth_weight_kg || '?'} kg</p>
                                </div>
                                <div className="patient-status">
                                    {getRiskBadge('low')}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Assessment Form / Details for Child */}
            {selectedChild && (
                <div className="assessment-panel">
                    {/* Header */}
                    <div className="bg-white/60 backdrop-blur-lg border-b border-blue-200/40 px-8 py-6 shadow-sm mb-6 rounded-lg">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-3">
                                    <h2 className="text-2xl font-bold text-slate-800">{selectedChild.name}</h2>
                                    <span className="bg-sky-100/50 text-blue-700 px-3 py-1 rounded-full text-xs font-bold border border-blue-200 uppercase tracking-wide">
                                        Child
                                    </span>
                                </div>
                                <p className="text-slate-500 mt-1 flex items-center gap-2 text-sm">
                                    <Calendar className="w-4 h-4" /> Born: {selectedChild.birth_date} · {selectedChild.gender === 'male' ? 'Boy' : 'Girl'}
                                </p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setSelectedChild(null)}
                                    className="px-4 py-2 rounded-lg font-semibold text-sm bg-blue-50/40 text-slate-600 flex items-center gap-2 hover:bg-blue-100/50"
                                >
                                    <X size={16} /> Close
                                </button>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="flex gap-3 mt-4 flex-wrap">
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm !== 'child' ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white" : "bg-blue-50/40 text-slate-600"}`}
                                onClick={() => setShowForm(null)}
                            >
                                <FileText className="w-4 h-4" /> Health History
                            </button>
                            <button
                                className={`px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2 ${showForm === 'child' ? "bg-green-600 text-white" : "bg-blue-50/40 text-slate-600"}`}
                                onClick={() => setShowForm('child')}
                            >
                                <Plus className="w-4 h-4" /> New Health Check
                            </button>
                        </div>
                    </div>

                    <div className="flex flex-col lg:flex-row gap-6 items-start">
                        {/* Left: Clinical Profile */}
                        {renderChildClinicalProfile(selectedChild)}

                        {/* Right: Content */}
                        <div className="flex-1 min-w-0 bg-white/60 backdrop-blur-lg rounded-xl shadow-md shadow-blue-500/5 border border-blue-200/40 overflow-y-auto flex flex-col p-6">
                            {showForm === 'child' ? (
                                <div className="assessment-form">
                                    <h5>📝 Child Health Check Form</h5>

                                    <div className="form-section">
                                        <h6>Growth Measurements</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Weight (kg)</label>
                                                <input
                                                    type="number"
                                                    step="0.01"
                                                    value={childAssessment.weight_kg}
                                                    onChange={e => setChildAssessment({ ...childAssessment, weight_kg: e.target.value })}
                                                    placeholder="e.g., 3.5"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Length (cm)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.length_cm}
                                                    onChange={e => setChildAssessment({ ...childAssessment, length_cm: e.target.value })}
                                                    placeholder="e.g., 50"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Head Circumference (cm)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.head_circumference_cm}
                                                    onChange={e => setChildAssessment({ ...childAssessment, head_circumference_cm: e.target.value })}
                                                    placeholder="e.g., 35"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Vital Signs</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Temperature (°C)</label>
                                                <input
                                                    type="number"
                                                    step="0.1"
                                                    value={childAssessment.temperature}
                                                    onChange={e => setChildAssessment({ ...childAssessment, temperature: e.target.value })}
                                                    placeholder="e.g., 36.8"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Heart Rate (bpm)</label>
                                                <input
                                                    type="number"
                                                    value={childAssessment.heart_rate}
                                                    onChange={e => setChildAssessment({ ...childAssessment, heart_rate: e.target.value })}
                                                    placeholder="e.g., 140"
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>Respiratory Rate</label>
                                                <input
                                                    type="number"
                                                    value={childAssessment.respiratory_rate}
                                                    onChange={e => setChildAssessment({ ...childAssessment, respiratory_rate: e.target.value })}
                                                    placeholder="breaths/min"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Feeding Assessment</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Feeding Type</label>
                                                <select
                                                    value={childAssessment.feeding_type}
                                                    onChange={e => setChildAssessment({ ...childAssessment, feeding_type: e.target.value })}
                                                >
                                                    <option value="exclusive_breastfeeding">Exclusive Breastfeeding</option>
                                                    <option value="mixed">Mixed Feeding</option>
                                                    <option value="formula">Formula Only</option>
                                                    <option value="complementary">Complementary Foods Started</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Feeding Frequency</label>
                                                <input
                                                    type="text"
                                                    value={childAssessment.feeding_frequency}
                                                    onChange={e => setChildAssessment({ ...childAssessment, feeding_frequency: e.target.value })}
                                                    placeholder="e.g., 8-10 times/day"
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Physical Examination</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Skin Color</label>
                                                <select
                                                    value={childAssessment.skin_color}
                                                    onChange={e => setChildAssessment({ ...childAssessment, skin_color: e.target.value })}
                                                >
                                                    <option value="normal">Normal/Pink</option>
                                                    <option value="pale">Pale</option>
                                                    <option value="cyanotic">Bluish (Cyanotic)</option>
                                                    <option value="jaundiced">Yellow (Jaundiced)</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Jaundice Level</label>
                                                <select
                                                    value={childAssessment.jaundice_level}
                                                    onChange={e => setChildAssessment({ ...childAssessment, jaundice_level: e.target.value })}
                                                >
                                                    <option value="none">None</option>
                                                    <option value="mild_face">Mild (Face only)</option>
                                                    <option value="moderate">Moderate (Up to trunk)</option>
                                                    <option value="severe">Severe (Palms/Soles)</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Umbilical Cord</label>
                                                <select
                                                    value={childAssessment.umbilical_cord}
                                                    onChange={e => setChildAssessment({ ...childAssessment, umbilical_cord: e.target.value })}
                                                >
                                                    <option value="clean_dry">Clean & Dry</option>
                                                    <option value="moist">Moist/Sticky</option>
                                                    <option value="infected">Infected/Redness</option>
                                                    <option value="separated">Separated</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Fontanelle</label>
                                                <select
                                                    value={childAssessment.fontanelle}
                                                    onChange={e => setChildAssessment({ ...childAssessment, fontanelle: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="bulging">Bulging</option>
                                                    <option value="sunken">Sunken</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Eyes</label>
                                                <select
                                                    value={childAssessment.eyes}
                                                    onChange={e => setChildAssessment({ ...childAssessment, eyes: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="discharge">Discharge</option>
                                                    <option value="swelling">Swelling</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Reflexes</label>
                                                <select
                                                    value={childAssessment.reflexes}
                                                    onChange={e => setChildAssessment({ ...childAssessment, reflexes: e.target.value })}
                                                >
                                                    <option value="present">Present</option>
                                                    <option value="weak">Weak</option>
                                                    <option value="absent">Absent</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Muscle Tone</label>
                                                <select
                                                    value={childAssessment.muscle_tone}
                                                    onChange={e => setChildAssessment({ ...childAssessment, muscle_tone: e.target.value })}
                                                >
                                                    <option value="normal">Normal</option>
                                                    <option value="hypotonic">Floppy (Hypotonic)</option>
                                                    <option value="hypertonic">Stiff (Hypertonic)</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>⚠️ IMNCI Danger Signs (Check if present)</h6>
                                        <div className="checkbox-grid danger-signs">
                                            {[
                                                { key: 'not_feeding_well', label: 'Not feeding well' },
                                                { key: 'convulsions', label: 'Convulsions/Fits' },
                                                { key: 'fast_breathing', label: 'Fast breathing (>60/min)' },
                                                { key: 'chest_indrawing', label: 'Severe chest indrawing' },
                                                { key: 'high_fever', label: 'High fever (>38°C)' },
                                                { key: 'hypothermia', label: 'Hypothermia (<35.5°C)' },
                                                { key: 'jaundice_extending', label: 'Jaundice extending to palms' },
                                                { key: 'umbilical_infection', label: 'Umbilical infection/bleeding' }
                                            ].map(item => (
                                                <label key={item.key} className="checkbox-item danger">
                                                    <input
                                                        type="checkbox"
                                                        checked={childAssessment[item.key]}
                                                        onChange={e => setChildAssessment({ ...childAssessment, [item.key]: e.target.checked })}
                                                    />
                                                    <span>{item.label}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="form-section">
                                        <h6>Risk Assessment & Referral</h6>
                                        <div className="form-row">
                                            <div className="form-field">
                                                <label>Overall Risk Level</label>
                                                <select
                                                    value={childAssessment.overall_risk_level}
                                                    onChange={e => setChildAssessment({ ...childAssessment, overall_risk_level: e.target.value })}
                                                    className={`risk-select ${childAssessment.overall_risk_level}`}
                                                >
                                                    <option value="low">Low Risk</option>
                                                    <option value="medium">Medium Risk</option>
                                                    <option value="high">High Risk</option>
                                                    <option value="critical">Critical</option>
                                                </select>
                                            </div>
                                            <div className="form-field">
                                                <label>Referral Needed?</label>
                                                <div className="toggle-switch">
                                                    <label>
                                                        <input
                                                            type="checkbox"
                                                            checked={childAssessment.referral_needed}
                                                            onChange={e => setChildAssessment({ ...childAssessment, referral_needed: e.target.checked })}
                                                        />
                                                        <span className="slider"></span>
                                                        <span className="label-text">{childAssessment.referral_needed ? 'Yes' : 'No'}</span>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                        {childAssessment.referral_needed && (
                                            <div className="form-row">
                                                <div className="form-field">
                                                    <label>Referral Facility</label>
                                                    <input
                                                        type="text"
                                                        value={childAssessment.referral_facility}
                                                        onChange={e => setChildAssessment({ ...childAssessment, referral_facility: e.target.value })}
                                                        placeholder="e.g. District Hospital"
                                                    />
                                                </div>
                                                <div className="form-field">
                                                    <label>Reason for Referral</label>
                                                    <input
                                                        type="text"
                                                        value={childAssessment.referral_reason}
                                                        onChange={e => setChildAssessment({ ...childAssessment, referral_reason: e.target.value })}
                                                        placeholder="Reason..."
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="form-section">
                                        <h6>{userRole === 'doctor' ? 'Notes, Nutrition & Medications' : 'Remarks'}</h6>
                                        {userRole === 'doctor' ? (
                                            <>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Clinical Notes</label>
                                                        <textarea value={childAssessment.notes} onChange={e => setChildAssessment({ ...childAssessment, notes: e.target.value })} placeholder="Enter observations..." rows={3} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Recommendations</label>
                                                        <textarea value={childAssessment.recommendations} onChange={e => setChildAssessment({ ...childAssessment, recommendations: e.target.value })} placeholder="Enter recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Nutrition Advice</label>
                                                        <textarea value={childAssessment.nutrition_advice} onChange={e => setChildAssessment({ ...childAssessment, nutrition_advice: e.target.value })} placeholder="Dietary recommendations..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field full">
                                                        <label>Medications</label>
                                                        <textarea value={childAssessment.medications} onChange={e => setChildAssessment({ ...childAssessment, medications: e.target.value })} placeholder="Prescribed medicines..." rows={2} />
                                                    </div>
                                                </div>
                                                <div className="form-row">
                                                    <div className="form-field">
                                                        <label>Next Visit Date</label>
                                                        <input type="date" min={new Date().toISOString().split('T')[0]} value={childAssessment.next_visit_date} onChange={e => setChildAssessment({ ...childAssessment, next_visit_date: e.target.value })} />
                                                    </div>
                                                </div>
                                            </>
                                        ) : (
                                            <div className="form-row">
                                                <div className="form-field full">
                                                    <label>Remarks</label>
                                                    <textarea value={childAssessment.notes} onChange={e => setChildAssessment({ ...childAssessment, notes: e.target.value })} placeholder="Enter remarks..." rows={3} />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div className="form-actions">
                                        <button className="btn-secondary" onClick={() => setShowForm(null)}>
                                            <X size={16} /> Cancel
                                        </button>
                                        <button className="btn-primary" onClick={submitChildAssessment}>
                                            <Save size={16} /> Save Health Check
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="assessment-history">
                                    <div className="flex justify-between items-center mb-4">
                                        <h5>📜 Health Check History</h5>
                                        <span className="text-xs text-slate-400 bg-blue-50/40 px-2 py-1 rounded">Latest on top</span>
                                    </div>
                                    {assessments.length === 0 ? (
                                        <div className="text-center py-8 text-slate-400">
                                            <Baby size={32} className="mx-auto mb-2 opacity-50" />
                                            <p>No health checks recorded yet</p>
                                        </div>
                                    ) : (
                                        <div className="history-list space-y-4">
                                            {assessments.map((a, i) => renderAssessmentCard(a, 'child'))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );


    const subTabs = [
        { id: 'overview', label: 'Overview', icon: ClipboardCheck },
        { id: 'mother', label: 'Mother Care', icon: Heart },
        { id: 'child', label: 'Child Health', icon: Baby },
    ];

    if (loading) {
        return (
            <div className="loading-container">
                <Loader className="spinner" size={32} />
                <p>Loading postnatal data...</p>
            </div>
        );
    }

    return (
        <div className="postnatal-assessments">
            {/* Sub-tabs */}
            <div className="sub-tabs">
                {subTabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`sub-tab ${activeSubTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveSubTab(tab.id)}
                    >
                        <tab.icon size={16} />
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="sub-content">
                {activeSubTab === 'overview' && renderOverview()}
                {activeSubTab === 'mother' && renderMotherAssessments()}
                {activeSubTab === 'child' && renderChildAssessments()}
            </div>
        </div>
    );
};

export default PostnatalAssessments;
