import React, { useState, useEffect } from 'react';
import { postnatalAPI } from '../../services/api';
import { TrendingUp, Weight, Ruler, Activity, AlertTriangle, CheckCircle, Plus, Loader } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { showToast } from '../../utils/FixedPatterns';
import './PostnatalPages.css';

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
    const [loadingRecords, setLoadingRecords] = useState(false);
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
        loadChildren();
    }, [ashaWorkerId]);

    useEffect(() => {
        if (selectedChild) {
            loadChildGrowth(selectedChild);
        } else {
            setGrowthRecords([]);
        }
    }, [selectedChild]);

    const loadChildren = async () => {
        try {
            setLoading(true);
            const response = await postnatalAPI.getChildren(null, ashaWorkerId);
            setChildren(response.children || []);
        } catch (err) {
            console.error('Error loading children:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadChildGrowth = async (childId) => {
        try {
            setLoadingRecords(true);
            const response = await postnatalAPI.getGrowthRecords(childId);
            setGrowthRecords(response.records || []);
        } catch (err) {
            console.error('Error loading growth records:', err);
        } finally {
            setLoadingRecords(false);
        }
    };

    const getLatestGrowth = () => {
        if (growthRecords.length === 0) return null;
        return growthRecords[0]; // Assuming API returns sorted desc
    };

    const getGrowthStatus = (zScore) => {
        if (!zScore && zScore !== 0) return { label: 'Unknown', color: '#9ca3af', severity: 'unknown' };
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
            const today = new Date().toISOString().split('T')[0];
            const response = await postnatalAPI.recordGrowth({
                child_id: selectedChild,
                measurement_date: today,
                weight_kg: parseFloat(newRecord.weight_kg),
                height_cm: newRecord.height_cm ? parseFloat(newRecord.height_cm) : null,
                head_circumference_cm: newRecord.head_circumference_cm ? parseFloat(newRecord.head_circumference_cm) : null,
                notes: newRecord.notes,
                measured_by: 'ASHA Worker'
            });

            if (response) {
                // Determine mock status for immediate feedback if backend doesn't return Z-scores yet
                const mockStatus = {
                    alert: false,
                    status_label: 'Use WHO Calculator',
                    z_scores: { weight_for_age_z: 0 } // Placeholder
                };

                setLastResult(mockStatus);

                setTimeout(async () => {
                    setShowAddForm(false);
                    setNewRecord({ weight_kg: '', height_cm: '', head_circumference_cm: '', notes: '' });
                    setLastResult(null);
                    await loadChildGrowth(selectedChild);
                }, 1500);
            }
        } catch (err) {
            console.error('Error saving record:', err);
            showToast('Failed to save record: ' + err.message, 'error');
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

            {loading ? (
                <div className="loading-state">Loading registered children...</div>
            ) : children.length === 0 ? (
                <div className="empty-state">
                    <TrendingUp size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>Register children to track their growth and development.</p>
                </div>
            ) : (
                <div className="growth-grid">
                    {children.map(child => {
                        // Only show expanded card if selected
                        const isSelected = selectedChild === child.id;
                        const latestGrowth = isSelected ? getLatestGrowth() : null;

                        return (
                            <div key={child.id} className={`growth-card ${isSelected ? 'expanded' : ''}`}>
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
                                        onClick={() => {
                                            setSelectedChild(child.id);
                                            // Only show form if already selected, otherwise just select
                                            if (isSelected) setShowAddForm(true);
                                        }}
                                    >
                                        <Plus size={16} /> {isSelected ? 'Record' : 'View'}
                                    </button>
                                </div>

                                {isSelected && (
                                    <div className="child-details-section">
                                        {loadingRecords ? (
                                            <div className="p-4 text-center">Loading growth records...</div>
                                        ) : (
                                            <>
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
                                                        <p className="last-measured">
                                                            Last: {new Date(latestGrowth.measurement_date).toLocaleDateString()}
                                                        </p>
                                                    </div>
                                                ) : (
                                                    <div className="no-records">
                                                        <p>No growth records yet</p>
                                                    </div>
                                                )}

                                                {growthRecords.length > 0 && (
                                                    <div className="growth-chart-section" style={{ marginTop: '1rem', height: '200px' }}>
                                                        <ResponsiveContainer width="100%" height="100%">
                                                            <LineChart data={[...growthRecords].reverse().map(r => ({
                                                                date: new Date(r.measurement_date).toLocaleDateString(),
                                                                weight: r.weight_kg,
                                                                height: r.height_cm
                                                            }))}>
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
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Add Record Modal */}
            {showAddForm && (
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
                                        <CheckCircle size={48} color="#10b981" />
                                    </div>
                                    <h3>Record Saved</h3>
                                    <p className="closing-message">Closing in a moment...</p>
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
                                            <><Loader size={16} className="animate-spin" /> Saving...</>
                                        ) : (
                                            'Save Record'
                                        )}
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
