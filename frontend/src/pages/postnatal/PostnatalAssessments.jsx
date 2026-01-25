import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import {
    Heart, Baby, ClipboardCheck, AlertTriangle, CheckCircle, Clock,
    User, Thermometer, Activity, Scale, Eye, Droplets, Loader,
    Plus, FileText, Calendar, Stethoscope, RefreshCw, ChevronDown,
    ChevronUp, Edit2, Save, X
} from 'lucide-react';

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
        next_visit_date: ''
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
        next_visit_date: ''
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
            // Load postnatal mothers (status = 'postnatal')
            let query = supabase
                .from('mothers')
                .select('*')
                .eq('status', 'postnatal');

            if (signal) query = query.abortSignal(signal);
            if (ashaWorkerId) query = query.eq('asha_worker_id', ashaWorkerId);
            if (doctorId) query = query.eq('doctor_id', doctorId);

            const { data: mothersData, error: mothersError } = await query;
            if (mothersError) throw mothersError;

            setMothers(mothersData || []);

            // Load children (if table exists)
            try {
                const motherIds = (mothersData || []).map(m => m.id);
                if (motherIds.length > 0) {
                    let childQuery = supabase
                        .from('children')
                        .select('*')
                        .in('mother_id', motherIds);

                    if (signal) childQuery = childQuery.abortSignal(signal);

                    const { data: childrenData } = await childQuery;
                    setChildren(childrenData || []);
                }
            } catch (childErr) {
                console.log('Children fetch error:', childErr);
                setChildren([]);
            }

        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Error loading data:', err);
            }
        } finally {
            setLoading(false);
        }
    };

    const loadAssessments = async (motherId = null, childId = null) => {
        try {
            // Try to load assessments from postnatal_assessments table
            let query = supabase.from('postnatal_assessments').select('*');

            if (motherId) query = query.eq('mother_id', motherId);
            if (childId) query = query.eq('child_id', childId);

            query = query.order('assessment_date', { ascending: false });

            const { data } = await query;
            setAssessments(data || []);
        } catch {
            setAssessments([]);
        }
    };

    const cleanData = (data) => {
        const cleaned = { ...data };
        Object.keys(cleaned).forEach(key => {
            if (cleaned[key] === '') {
                cleaned[key] = null;
            }
        });
        return cleaned;
    };

    const submitMotherAssessment = async () => {
        if (!selectedMother) return;

        setLoading(true);
        try {
            const assessmentData = cleanData({
                mother_id: selectedMother.id,
                assessment_type: 'mother_postnatal',
                assessor_id: ashaWorkerId || doctorId,
                assessor_role: userRole,
                ...motherAssessment
            });

            const { error } = await supabase.from('postnatal_assessments').insert(assessmentData);
            if (error) throw error;

            // Success notification (non-blocking)
            const notification = document.createElement('div');
            notification.textContent = 'Assessment saved successfully!';
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
            notification.textContent = `Failed to save: ${err.message || 'Unknown error'}`;
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
                assessment_type: 'child_checkup',
                assessor_id: ashaWorkerId || doctorId,
                assessor_role: userRole,
                ...childAssessment
            });

            const { error } = await supabase.from('postnatal_assessments').insert(assessmentData);
            if (error) throw error;

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

    const getRiskBadge = (level) => {
        const badges = {
            low: { color: '#10b981', bg: '#d1fae5', label: 'Low Risk' },
            medium: { color: '#f59e0b', bg: '#fef3c7', label: 'Medium Risk' },
            high: { color: '#ef4444', bg: '#fee2e2', label: 'High Risk' }
        };
        const badge = badges[level] || badges.low;
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
                    <div className="panel-header">
                        <div className="panel-title">
                            <h4>{selectedMother.name}'s Postnatal Care</h4>
                            <span>Phone: {selectedMother.phone}</span>
                        </div>
                        <button
                            className="btn-primary"
                            onClick={() => setShowForm('mother')}
                        >
                            <Plus size={16} /> New Assessment
                        </button>
                    </div>

                    {showForm === 'mother' ? (
                        <div className="assessment-form">
                            <h5>📝 Mother Postnatal Assessment Form</h5>

                            <div className="form-section">
                                <h6>Physical Health</h6>
                                <div className="form-row">
                                    <div className="form-field">
                                        <label>Temperature (°C)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={motherAssessment.temperature}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, temperature: e.target.value })}
                                            placeholder="e.g., 37.0"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>BP (Systolic)</label>
                                        <input
                                            type="number"
                                            value={motherAssessment.blood_pressure_systolic}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_systolic: e.target.value })}
                                            placeholder="e.g., 120"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>BP (Diastolic)</label>
                                        <input
                                            type="number"
                                            value={motherAssessment.blood_pressure_diastolic}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, blood_pressure_diastolic: e.target.value })}
                                            placeholder="e.g., 80"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>Pulse Rate</label>
                                        <input
                                            type="number"
                                            value={motherAssessment.pulse_rate}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, pulse_rate: e.target.value })}
                                            placeholder="bpm"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-section">
                                <h6>Postnatal Recovery</h6>
                                <div className="form-row">
                                    <div className="form-field">
                                        <label>Uterine Involution</label>
                                        <select
                                            value={motherAssessment.uterine_involution}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, uterine_involution: e.target.value })}
                                        >
                                            <option value="normal">Normal</option>
                                            <option value="subinvolution">Subinvolution</option>
                                            <option value="tender">Tender</option>
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label>Lochia Status</label>
                                        <select
                                            value={motherAssessment.lochia_status}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, lochia_status: e.target.value })}
                                        >
                                            <option value="normal">Normal</option>
                                            <option value="foul_smelling">Foul Smelling</option>
                                            <option value="excessive">Excessive</option>
                                            <option value="absent">Absent</option>
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label>Breast Condition</label>
                                        <select
                                            value={motherAssessment.breast_condition}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, breast_condition: e.target.value })}
                                        >
                                            <option value="normal">Normal</option>
                                            <option value="engorged">Engorged</option>
                                            <option value="cracked_nipples">Cracked Nipples</option>
                                            <option value="mastitis">Mastitis Signs</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="form-section">
                                <h6>Mental Health (PPD Screening)</h6>
                                <div className="form-row">
                                    <div className="form-field">
                                        <label>Mood Status</label>
                                        <select
                                            value={motherAssessment.mood_status}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, mood_status: e.target.value })}
                                        >
                                            <option value="stable">Stable & Happy</option>
                                            <option value="anxious">Anxious</option>
                                            <option value="sad">Persistently Sad</option>
                                            <option value="overwhelmed">Overwhelmed</option>
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label>Sleep Quality</label>
                                        <select
                                            value={motherAssessment.sleep_quality}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, sleep_quality: e.target.value })}
                                        >
                                            <option value="adequate">Adequate</option>
                                            <option value="poor">Poor</option>
                                            <option value="insomnia">Insomnia</option>
                                        </select>
                                    </div>
                                    <div className="form-field">
                                        <label>Bonding with Baby</label>
                                        <select
                                            value={motherAssessment.bonding_with_baby}
                                            onChange={e => setMotherAssessment({ ...motherAssessment, bonding_with_baby: e.target.value })}
                                        >
                                            <option value="good">Good</option>
                                            <option value="developing">Developing</option>
                                            <option value="poor">Poor/Detached</option>
                                        </select>
                                    </div>
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
                                            <input
                                                type="checkbox"
                                                checked={motherAssessment[item.key]}
                                                onChange={e => setMotherAssessment({ ...motherAssessment, [item.key]: e.target.checked })}
                                            />
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
                            <h5>📜 Assessment History</h5>
                            {assessments.length === 0 ? (
                                <p className="no-records">No assessments recorded yet</p>
                            ) : (
                                <div className="history-list">
                                    {assessments.map((a, i) => (
                                        <div
                                            key={i}
                                            className={`history-item ${expandedAssessment === i ? 'expanded' : ''}`}
                                            onClick={() => setExpandedAssessment(expandedAssessment === i ? null : i)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <div className="history-date">
                                                <Calendar size={14} />
                                                {a.assessment_date}
                                            </div>
                                            <div className="history-details">
                                                <div className="flex gap-2 mb-1">
                                                    <span className={`px-2 py-0.5 text-xs rounded-full ${a.assessor_role === 'doctor' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                                                        {a.assessor_role === 'doctor' ? '👨‍⚕️ Doctor' : '👩‍⚕️ ASHA'}
                                                    </span>
                                                    {expandedAssessment !== i && <span className="text-xs text-gray-500">Click to view details</span>}
                                                </div>
                                                <span>Day {a.days_postpartum || '?'} postpartum</span>

                                                {expandedAssessment === i && (
                                                    <div className="assessment-details-expanded" style={{ marginTop: '12px', padding: '12px', background: '#f9fafb', borderRadius: '8px', fontSize: '13px' }} onClick={(e) => e.stopPropagation()}>
                                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                                            {a.days_postpartum && <div><strong>Days Postpartum:</strong> {a.days_postpartum}</div>}
                                                            {a.systolic_bp && <div><strong>Blood Pressure:</strong> {a.systolic_bp}/{a.diastolic_bp} mmHg</div>}
                                                            {a.heart_rate && <div><strong>Heart Rate:</strong> {a.heart_rate} bpm</div>}
                                                            {a.temperature && <div><strong>Temperature:</strong> {a.temperature}°C</div>}
                                                            {a.uterine_involution && <div><strong>Uterine Involution:</strong> {a.uterine_involution}</div>}
                                                            {a.lochia && <div><strong>Lochia:</strong> {a.lochia}</div>}
                                                            {a.perineal_healing && <div><strong>Perineal Healing:</strong> {a.perineal_healing}</div>}
                                                            {a.breastfeeding_status && <div><strong>Breastfeeding:</strong> {a.breastfeeding_status}</div>}
                                                            {a.bonding && <div><strong>Mother-Baby Bonding:</strong> {a.bonding}</div>}
                                                        </div>

                                                        {/* Danger Signs */}
                                                        {(a.fever || a.excessive_bleeding || a.foul_discharge || a.breast_engorgement || a.mastitis || a.urinary_issues) && (
                                                            <div style={{ marginTop: '12px', padding: '8px', background: '#fee2e2', borderRadius: '4px' }}>
                                                                <strong style={{ color: '#991b1b' }}>⚠️ Danger Signs:</strong>
                                                                <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                                                    {a.fever && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Fever</span>}
                                                                    {a.excessive_bleeding && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Bleeding</span>}
                                                                    {a.foul_discharge && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Foul Discharge</span>}
                                                                    {a.breast_engorgement && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Breast Engorgement</span>}
                                                                    {a.mastitis && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Mastitis</span>}
                                                                    {a.urinary_issues && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Urinary Issues</span>}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {a.notes && (
                                                            <div style={{ marginTop: '12px' }}>
                                                                <strong>Clinical Notes:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.notes}</p>
                                                            </div>
                                                        )}
                                                        {a.recommendations && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Recommendations:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.recommendations}</p>
                                                            </div>
                                                        )}
                                                        {a.nutrition_advice && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Nutrition Advice:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.nutrition_advice}</p>
                                                            </div>
                                                        )}
                                                        {a.medications && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Medications:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.medications}</p>
                                                            </div>
                                                        )}
                                                        {a.next_visit_date && (
                                                            <div style={{ marginTop: '8px', padding: '8px', background: '#dbeafe', borderRadius: '4px' }}>
                                                                <strong style={{ color: '#1e40af' }}>📅 Next Visit:</strong> {a.next_visit_date}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
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
            </div>

            {/* Child List */}
            <div className="patient-list">
                {children.length === 0 ? (
                    <div className="empty-state">
                        <Baby size={48} />
                        <p>No children registered yet</p>
                        <span>Children will appear after being added during delivery completion</span>
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
                    <div className="panel-header">
                        <div className="panel-title">
                            <h4>{selectedChild.name}'s Health Checks</h4>
                            <span>{selectedChild.gender === 'male' ? 'Boy' : 'Girl'} · Born {selectedChild.birth_date}</span>
                        </div>
                        <button
                            className="btn-primary"
                            onClick={() => setShowForm('child')}
                        >
                            <Plus size={16} /> New Health Check
                        </button>
                    </div>

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
                                            <option value="moist">Moist</option>
                                            <option value="infected">Signs of Infection</option>
                                            <option value="separated">Separated</option>
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
                                                <textarea value={childAssessment.recommendations || ''} onChange={e => setChildAssessment({ ...childAssessment, recommendations: e.target.value })} placeholder="Enter recommendations..." rows={2} />
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
                            <h5>📜 Health Check History</h5>
                            {assessments.length === 0 ? (
                                <p className="no-records">No health checks recorded yet</p>
                            ) : (
                                <div className="history-list">
                                    {assessments.map((a, i) => (
                                        <div
                                            key={i}
                                            className={`history-item ${expandedAssessment === i ? 'expanded' : ''}`}
                                            onClick={() => setExpandedAssessment(expandedAssessment === i ? null : i)}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <div className="history-date">
                                                <Calendar size={14} />
                                                {a.assessment_date}
                                            </div>
                                            <div className="history-details">
                                                <div className="flex gap-2 mb-1">
                                                    <span className={`px-2 py-0.5 text-xs rounded-full ${a.assessor_role === 'doctor' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                                                        {a.assessor_role === 'doctor' ? '👨‍⚕️ Doctor' : '👩‍⚕️ ASHA'}
                                                    </span>
                                                    {expandedAssessment !== i && <span className="text-xs text-gray-500">Click to view details</span>}
                                                </div>
                                                <span>Weight: {a.weight_kg || '?'} kg</span>

                                                {expandedAssessment === i && (
                                                    <div className="assessment-details-expanded" style={{ marginTop: '12px', padding: '12px', background: '#f9fafb', borderRadius: '8px', fontSize: '13px' }} onClick={(e) => e.stopPropagation()}>
                                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                                            {a.weight_kg && <div><strong>Weight:</strong> {a.weight_kg} kg</div>}
                                                            {a.length_cm && <div><strong>Length:</strong> {a.length_cm} cm</div>}
                                                            {a.head_circumference_cm && <div><strong>Head Circumference:</strong> {a.head_circumference_cm} cm</div>}
                                                            {a.temperature && <div><strong>Temperature:</strong> {a.temperature}°C</div>}
                                                            {a.heart_rate && <div><strong>Heart Rate:</strong> {a.heart_rate} bpm</div>}
                                                            {a.respiratory_rate && <div><strong>Respiratory Rate:</strong> {a.respiratory_rate}/min</div>}
                                                            {a.feeding_type && <div><strong>Feeding Type:</strong> {a.feeding_type}</div>}
                                                            {a.feeding_frequency && <div><strong>Feeding Frequency:</strong> {a.feeding_frequency}</div>}
                                                            {a.skin_color && <div><strong>Skin Color:</strong> {a.skin_color}</div>}
                                                            {a.jaundice_level && <div><strong>Jaundice:</strong> {a.jaundice_level}</div>}
                                                            {a.umbilical_cord && <div><strong>Umbilical Cord:</strong> {a.umbilical_cord}</div>}
                                                        </div>

                                                        {/* IMNCI Danger Signs */}
                                                        {(a.not_feeding_well || a.convulsions || a.fast_breathing || a.chest_indrawing || a.high_fever || a.hypothermia || a.jaundice_extending || a.umbilical_infection) && (
                                                            <div style={{ marginTop: '12px', padding: '8px', background: '#fee2e2', borderRadius: '4px' }}>
                                                                <strong style={{ color: '#991b1b' }}>⚠️ IMNCI Danger Signs:</strong>
                                                                <div style={{ marginTop: '4px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                                                                    {a.not_feeding_well && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Not Feeding</span>}
                                                                    {a.convulsions && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Convulsions</span>}
                                                                    {a.fast_breathing && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Fast Breathing</span>}
                                                                    {a.chest_indrawing && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Chest Indrawing</span>}
                                                                    {a.high_fever && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>High Fever</span>}
                                                                    {a.hypothermia && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Hypothermia</span>}
                                                                    {a.jaundice_extending && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Severe Jaundice</span>}
                                                                    {a.umbilical_infection && <span style={{ padding: '2px 8px', background: '#fca5a5', borderRadius: '4px', fontSize: '11px' }}>Umbilical Infection</span>}
                                                                </div>
                                                            </div>
                                                        )}

                                                        {a.notes && (
                                                            <div style={{ marginTop: '12px' }}>
                                                                <strong>Clinical Notes:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.notes}</p>
                                                            </div>
                                                        )}
                                                        {a.recommendations && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Recommendations:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.recommendations}</p>
                                                            </div>
                                                        )}
                                                        {a.nutrition_advice && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Nutrition Advice:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.nutrition_advice}</p>
                                                            </div>
                                                        )}
                                                        {a.medications && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <strong>Medications:</strong>
                                                                <p style={{ marginTop: '4px', color: '#4b5563' }}>{a.medications}</p>
                                                            </div>
                                                        )}
                                                        {a.next_visit_date && (
                                                            <div style={{ marginTop: '8px', padding: '8px', background: '#dbeafe', borderRadius: '4px' }}>
                                                                <strong style={{ color: '#1e40af' }}>📅 Next Visit:</strong> {a.next_visit_date}
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
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
