import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import { TrendingUp, Weight, Ruler, Activity, AlertTriangle, CheckCircle, Plus, Loader } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './PostnatalPages.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// WHO Z-score thresholds
const Z_SCORE_CLASSIFICATIONS = {
    3: { label: 'Obese', color: '#ef4444', severity: 'high' },
    2: { label: 'Overweight', color: '#f59e0b', severity: 'moderate' },
    1: { label: 'Risk of Overweight', color: '#fbbf24', severity: 'low' },
    0: { label: 'Normal', color: '#10b981', severity: 'normal' },
    '-1': { label: 'Normal', color: '#10b981', severity: 'normal' },
    '-2': { label: 'Wasted/Underweight', color: '#f59e0b', severity: 'moderate' },
    '-3': { label: 'Severely Wasted', color: '#ef4444', severity: 'high' },
};

export const GrowthCharts = ({ ashaWorkerId }) => {
    const [children, setChildren] = useState([]);
    const [growthRecords, setGrowthRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedChild, setSelectedChild] = useState(null);
    const [showAddForm, setShowAddForm] = useState(false);
    const [saving, setSaving] = useState(false);
    const [lastResult, setLastResult] = useState(null);
    const [newRecord, setNewRecord] = useState({
        weight_kg: '',
        height_cm: '',
        head_circumference_cm: '',
        notes: ''
    });

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                setLoading(true);

                const { data: childrenData } = await supabase
                    .from('children')
                    .select('*, mothers:mother_id(name, asha_worker_id)')
                    .order('birth_date', { ascending: false });

                const { data: growthData } = await supabase
                    .from('growth_records')
                    .select('*')
                    .order('measurement_date', { ascending: false });

                if (isMounted) {
                    if (childrenData) {
                        const filtered = ashaWorkerId
                            ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                            : childrenData;
                        setChildren(filtered);
                    }
                    if (growthData) setGrowthRecords(growthData);
                    setLoading(false);
                }
            } catch (err) {
                if (isMounted) {
                    console.error('Error loading data:', err);
                    setLoading(false);
                }
            }
        };

        fetchData();

        return () => {
            isMounted = false;
        };
    }, [ashaWorkerId]);

    const loadData = async () => {
        try {
            setLoading(true);

            const { data: childrenData } = await supabase
                .from('children')
                .select('*, mothers:mother_id(name, asha_worker_id)')
                .order('birth_date', { ascending: false });

            const { data: growthData } = await supabase
                .from('growth_records')
                .select('*')
                .order('measurement_date', { ascending: false });

            if (childrenData) {
                const filtered = ashaWorkerId
                    ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                    : childrenData;
                setChildren(filtered);
            }
            if (growthData) setGrowthRecords(growthData);
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getChildGrowthRecords = (childId) => {
        return growthRecords.filter(r => r.child_id === childId)
            .sort((a, b) => new Date(b.measurement_date) - new Date(a.measurement_date));
    };

    const getLatestGrowth = (childId) => {
        const records = getChildGrowthRecords(childId);
        return records[0] || null;
    };

    const getGrowthStatus = (zScore) => {
        if (zScore >= 3) return Z_SCORE_CLASSIFICATIONS['3'];
        if (zScore >= 2) return Z_SCORE_CLASSIFICATIONS['2'];
        if (zScore >= 1) return Z_SCORE_CLASSIFICATIONS['1'];
        if (zScore >= -1) return Z_SCORE_CLASSIFICATIONS['0'];
        if (zScore >= -2) return Z_SCORE_CLASSIFICATIONS['-1'];
        if (zScore >= -3) return Z_SCORE_CLASSIFICATIONS['-2'];
        return Z_SCORE_CLASSIFICATIONS['-3'];
    };

    const handleAddRecord = async () => {
        if (!selectedChild || !newRecord.weight_kg) return;

        setSaving(true);
        setLastResult(null);

        try {
            // Use the new API endpoint which calculates z-scores
            const response = await fetch(`${API_URL}/api/santanraksha/growth/record`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    child_id: selectedChild,
                    weight_kg: parseFloat(newRecord.weight_kg),
                    height_cm: newRecord.height_cm ? parseFloat(newRecord.height_cm) : null,
                    head_circumference_cm: newRecord.head_circumference_cm ? parseFloat(newRecord.head_circumference_cm) : null,
                    notes: newRecord.notes,
                    measured_by: 'ASHA Worker',
                    measurement_date: new Date().toISOString().split('T')[0]
                })
            });

            if (response.ok) {
                const result = await response.json();
                setLastResult(result);

                // Show result for a moment then close and refresh
                setTimeout(async () => {
                    setShowAddForm(false);
                    setNewRecord({ weight_kg: '', height_cm: '', head_circumference_cm: '', notes: '' });
                    setLastResult(null);
                    // Force refresh data immediately
                    await loadData();
                }, 2000);
            } else {
                console.warn('Backend API failed, using client-side fallback:', errorData);
                // Trigger fallback
                throw new Error('API_FALLBACK');
            }
        } catch (err) {
            console.log('Attempting offline fallback save...');

            // Fallback to direct Supabase insert
            try {
                const childData = children.find(c => c.id === selectedChild);
                let age_months = 0;
                let age_days = 0;

                if (childData?.birth_date) {
                    const birth = new Date(childData.birth_date);
                    const now = new Date();
                    const diffTime = Math.abs(now - birth);
                    age_days = Math.floor(diffTime / (1000 * 60 * 60 * 24));
                    age_months = Math.floor(age_days / 30.44);
                }

                const { data, error } = await supabase
                    .from('growth_records')
                    .insert({
                        child_id: selectedChild,
                        measurement_date: new Date().toISOString().split('T')[0],
                        age_months: age_months,
                        age_days: age_days,
                        weight_kg: parseFloat(newRecord.weight_kg),
                        height_cm: newRecord.height_cm ? parseFloat(newRecord.height_cm) : null,
                        head_circumference_cm: newRecord.head_circumference_cm ? parseFloat(newRecord.head_circumference_cm) : null,
                        notes: `${newRecord.notes || ''} | Offline Record`
                    })
                    .select();

                if (error) throw error;

                // Success
                setShowAddForm(false);
                setNewRecord({ weight_kg: '', height_cm: '', head_circumference_cm: '', notes: '' });
                alert('Record saved successfully (Offline Mode)');
                await loadData();

            } catch (fallbackError) {
                console.error('Fallback save failed:', fallbackError);
                alert('Failed to save record: ' + (fallbackError.message || 'Unknown error'));
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="postnatal-page">
            <div className="page-header">
                <h2><TrendingUp className="icon" /> Growth Monitoring</h2>
                <p>WHO Growth Standards - Track weight, height, and development</p>
            </div>

            {/* Stats Overview */}
            <div className="growth-stats">
                <div className="growth-stat normal">
                    <CheckCircle size={24} />
                    <div>
                        <span className="number">
                            {children.filter(c => {
                                const latest = getLatestGrowth(c.id);
                                return latest && latest.weight_for_age_z >= -2 && latest.weight_for_age_z <= 2;
                            }).length}
                        </span>
                        <span className="label">Normal Growth</span>
                    </div>
                </div>
                <div className="growth-stat warning">
                    <AlertTriangle size={24} />
                    <div>
                        <span className="number">
                            {children.filter(c => {
                                const latest = getLatestGrowth(c.id);
                                return latest && (latest.weight_for_age_z < -2 || latest.weight_for_age_z > 2);
                            }).length}
                        </span>
                        <span className="label">Needs Attention</span>
                    </div>
                </div>
                <div className="growth-stat pending">
                    <Activity size={24} />
                    <div>
                        <span className="number">
                            {children.filter(c => !getLatestGrowth(c.id)).length}
                        </span>
                        <span className="label">No Records</span>
                    </div>
                </div>
            </div>

            {loading ? (
                <div className="loading-state">Loading growth data...</div>
            ) : children.length === 0 ? (
                <div className="empty-state">
                    <TrendingUp size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>Register children to track their growth and development.</p>
                </div>
            ) : (
                <div className="growth-grid">
                    {children.map(child => {
                        const latestGrowth = getLatestGrowth(child.id);
                        const records = getChildGrowthRecords(child.id);

                        return (
                            <div key={child.id} className="growth-card">
                                <div className="growth-card-header">
                                    <div className="child-info">
                                        <span className="avatar">{child.gender === 'female' ? '👧' : '👦'}</span>
                                        <div>
                                            <h4>{child.name}</h4>
                                            <p>DOB: {new Date(child.birth_date).toLocaleDateString()}</p>
                                        </div>
                                    </div>
                                    <button
                                        className="btn-add-record"
                                        onClick={() => { setSelectedChild(child.id); setShowAddForm(true); }}
                                    >
                                        <Plus size={16} /> Record
                                    </button>
                                </div>

                                {latestGrowth ? (
                                    <div className="growth-latest">
                                        <div className="measurement">
                                            <Weight size={18} />
                                            <span>{latestGrowth.weight_kg} kg</span>
                                        </div>
                                        <div className="measurement">
                                            <Ruler size={18} />
                                            <span>{latestGrowth.height_cm || '-'} cm</span>
                                        </div>
                                        {latestGrowth.weight_for_age_z !== null && (
                                            <div className={`z-score ${getGrowthStatus(latestGrowth.weight_for_age_z).severity}`}>
                                                Z: {latestGrowth.weight_for_age_z?.toFixed(1)}
                                                <span className="status-label">
                                                    {getGrowthStatus(latestGrowth.weight_for_age_z).label}
                                                </span>
                                            </div>
                                        )}
                                        <p className="last-measured">
                                            Last: {new Date(latestGrowth.measurement_date).toLocaleDateString()}
                                        </p>
                                    </div>
                                ) : (
                                    <div className="no-records">
                                        <p>No growth records yet</p>
                                        <button
                                            className="btn-primary sm"
                                            onClick={() => { setSelectedChild(child.id); setShowAddForm(true); }}
                                        >
                                            Add First Record
                                        </button>
                                    </div>
                                )}

                                {records.length > 1 && (
                                    <div className="growth-history">
                                        <h5>Recent Measurements</h5>
                                        {records.slice(0, 3).map((record, idx) => (
                                            <div key={idx} className="history-item">
                                                <span>{new Date(record.measurement_date).toLocaleDateString()}</span>
                                                <span>{record.weight_kg} kg</span>
                                                <span>{record.height_cm || '-'} cm</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {records.length > 0 && (
                                    <div className="growth-chart-section" style={{ marginTop: '1rem', height: '200px' }}>
                                        <ResponsiveContainer width="100%" height="100%">
                                            <LineChart data={records.map(r => ({
                                                date: new Date(r.measurement_date).toLocaleDateString(),
                                                weight: r.weight_kg,
                                                height: r.height_cm
                                            })).reverse()}>
                                                <CartesianGrid strokeDasharray="3 3" />
                                                <XAxis dataKey="date" fontSize={10} />
                                                <YAxis yAxisId="left" orientation="left" stroke="#8884d8" fontSize={10} domain={['auto', 'auto']} />
                                                <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" fontSize={10} domain={['auto', 'auto']} />
                                                <Tooltip />
                                                <Line yAxisId="left" type="monotone" dataKey="weight" stroke="#8884d8" dot={{ r: 3 }} activeDot={{ r: 5 }} name="Weight (kg)" />
                                                <Line yAxisId="right" type="monotone" dataKey="height" stroke="#82ca9d" dot={{ r: 3 }} name="Height (cm)" />
                                            </LineChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Add Record Modal */}
            {
                showAddForm && (
                    <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
                        <div className="modal-content" onClick={e => e.stopPropagation()}>
                            <div className="modal-header">
                                <h2>📏 Add Growth Record</h2>
                                <button onClick={() => setShowAddForm(false)}>×</button>
                            </div>
                            <div className="modal-body">
                                {lastResult ? (
                                    <div className={`growth-result ${lastResult.alert ? 'alert' : 'success'}`}>
                                        <div className="result-icon">
                                            {lastResult.alert ? (
                                                <AlertTriangle size={48} color="#f59e0b" />
                                            ) : (
                                                <CheckCircle size={48} color="#10b981" />
                                            )}
                                        </div>
                                        <h3>{lastResult.status_label}</h3>
                                        <div className="z-score-display">
                                            <span>Weight-for-Age Z-Score:</span>
                                            <strong>{lastResult.z_scores?.weight_for_age_z?.toFixed(1) || 'N/A'}</strong>
                                        </div>
                                        {lastResult.recommendations?.length > 0 && (
                                            <div className="recommendations">
                                                <h4>Recommendations:</h4>
                                                <ul>
                                                    {lastResult.recommendations.map((rec, idx) => (
                                                        <li key={idx}>{rec}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        <p className="closing-message">Closing in 3 seconds...</p>
                                    </div>
                                ) : (
                                    <>
                                        <div className="form-group">
                                            <label>Weight (kg) *</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={newRecord.weight_kg}
                                                onChange={e => setNewRecord({ ...newRecord, weight_kg: e.target.value })}
                                                placeholder="e.g., 5.5"
                                                disabled={saving}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Height/Length (cm)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={newRecord.height_cm}
                                                onChange={e => setNewRecord({ ...newRecord, height_cm: e.target.value })}
                                                placeholder="e.g., 55"
                                                disabled={saving}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Head Circumference (cm)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={newRecord.head_circumference_cm}
                                                onChange={e => setNewRecord({ ...newRecord, head_circumference_cm: e.target.value })}
                                                placeholder="e.g., 35"
                                                disabled={saving}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Notes</label>
                                            <textarea
                                                value={newRecord.notes}
                                                onChange={e => setNewRecord({ ...newRecord, notes: e.target.value })}
                                                placeholder="Any observations..."
                                                disabled={saving}
                                            />
                                        </div>
                                        <button
                                            className="btn-primary full"
                                            onClick={handleAddRecord}
                                            disabled={saving || !newRecord.weight_kg}
                                        >
                                            {saving ? (
                                                <><Loader size={16} className="animate-spin" /> Calculating Z-Score...</>
                                            ) : (
                                                'Save & Evaluate Growth'
                                            )}
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
};
