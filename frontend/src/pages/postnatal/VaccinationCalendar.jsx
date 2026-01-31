import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import { Calendar, Check, AlertCircle, Clock, Syringe, ChevronRight, Info, Loader } from 'lucide-react';
import './PostnatalPages.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// IAP 2023 Vaccination Schedule
const IAP_SCHEDULE = [
    { vaccine: 'BCG', due_age_days: 0, description: 'Tuberculosis prevention' },
    { vaccine: 'OPV-0', due_age_days: 0, description: 'Oral Polio Vaccine (birth dose)' },
    { vaccine: 'Hepatitis B-1', due_age_days: 0, description: 'Hepatitis B birth dose' },
    { vaccine: 'OPV-1 + IPV-1', due_age_days: 42, description: '6 weeks - Polio vaccines' },
    { vaccine: 'Pentavalent-1', due_age_days: 42, description: '6 weeks - DPT + Hep B + Hib' },
    { vaccine: 'Rotavirus-1', due_age_days: 42, description: '6 weeks - Rotavirus' },
    { vaccine: 'PCV-1', due_age_days: 42, description: '6 weeks - Pneumococcal' },
    { vaccine: 'OPV-2 + IPV-2', due_age_days: 70, description: '10 weeks - Polio vaccines' },
    { vaccine: 'Pentavalent-2', due_age_days: 70, description: '10 weeks - DPT + Hep B + Hib' },
    { vaccine: 'Rotavirus-2', due_age_days: 70, description: '10 weeks - Rotavirus' },
    { vaccine: 'OPV-3 + IPV-3', due_age_days: 98, description: '14 weeks - Polio vaccines' },
    { vaccine: 'Pentavalent-3', due_age_days: 98, description: '14 weeks - DPT + Hep B + Hib' },
    { vaccine: 'Rotavirus-3', due_age_days: 98, description: '14 weeks - Rotavirus' },
    { vaccine: 'PCV-2', due_age_days: 98, description: '14 weeks - Pneumococcal booster' },
    { vaccine: 'Measles-1 (MR/MMR)', due_age_days: 270, description: '9 months - Measles/Rubella' },
    { vaccine: 'Vitamin A-1', due_age_days: 270, description: '9 months - Vitamin A supplement' },
    { vaccine: 'PCV Booster', due_age_days: 365, description: '12 months - Pneumococcal' },
    { vaccine: 'Measles-2 (MMR)', due_age_days: 450, description: '15 months - MMR booster' },
    { vaccine: 'DPT Booster-1', due_age_days: 540, description: '18 months - DPT booster' },
];

export const VaccinationCalendar = ({ ashaWorkerId }) => {
    const [children, setChildren] = useState([]);
    const [vaccinations, setVaccinations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedChild, setSelectedChild] = useState(null);
    const [filter, setFilter] = useState('all'); // 'all', 'due', 'overdue', 'completed'
    const [savingVaccine, setSavingVaccine] = useState(null); // Track which vaccine is being saved

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                setLoading(true);

                // Load children
                const { data: childrenData } = await supabase
                    .from('children')
                    .select('*, mothers:mother_id(name, asha_worker_id)')
                    .order('birth_date', { ascending: false });

                // Load vaccinations
                const { data: vaccinationsData } = await supabase
                    .from('vaccinations')
                    .select('*')
                    .order('due_date', { ascending: true });

                if (isMounted) {
                    if (childrenData) {
                        const filtered = ashaWorkerId
                            ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                            : childrenData;
                        setChildren(filtered);
                    }
                    if (vaccinationsData) setVaccinations(vaccinationsData);
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

            // Load children
            const { data: childrenData } = await supabase
                .from('children')
                .select('*, mothers:mother_id(name, asha_worker_id)')
                .order('birth_date', { ascending: false });

            // Load vaccinations
            const { data: vaccinationsData } = await supabase
                .from('vaccinations')
                .select('*')
                .order('due_date', { ascending: true });

            if (childrenData) {
                const filtered = ashaWorkerId
                    ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                    : childrenData;
                setChildren(filtered);
            }
            if (vaccinationsData) setVaccinations(vaccinationsData);
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getVaccineStatus = (childId, vaccineName) => {
        const record = vaccinations.find(v => v.child_id === childId && v.vaccine_name === vaccineName);
        if (!record) return 'pending';
        return record.status;
    };

    const markVaccineDone = async (childId, vaccineName) => {
        setSavingVaccine(`${childId}-${vaccineName}`);
        try {
            const response = await fetch(`${API_URL}/api/santanraksha/vaccination/mark-done`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    child_id: childId,
                    vaccine_name: vaccineName,
                    given_date: new Date().toISOString().split('T')[0],
                    given_by: 'ASHA Worker'
                })
            });

            if (response.ok) {
                // Force refresh data to show updated status
                await loadData();
            } else {
                const errorData = await response.json();
                console.error('Failed to mark vaccine as done:', errorData);
                // Fallback to direct Supabase with correct columns
                await fallbackMarkVaccineDone(childId, vaccineName);
            }
        } catch (err) {
            console.error('Error marking vaccine done:', err);
            // Fallback to direct Supabase
            await fallbackMarkVaccineDone(childId, vaccineName);
        } finally {
            setSavingVaccine(null);
        }
    };

    const fallbackMarkVaccineDone = async (childId, vaccineName) => {
        const today = new Date().toISOString().split('T')[0];

        // Check if there's an existing record
        const { data: existing } = await supabase
            .from('vaccinations')
            .select('id')
            .eq('child_id', childId)
            .eq('vaccine_name', vaccineName)
            .neq('status', 'completed')
            .single();

        if (existing) {
            // Update existing record with correct column names
            await supabase
                .from('vaccinations')
                .update({
                    status: 'completed',
                    administered_date: today,
                    administered_by: 'ASHA Worker'
                })
                .eq('id', existing.id);
        } else {
            // Insert new record with correct column names
            await supabase
                .from('vaccinations')
                .insert({
                    child_id: childId,
                    vaccine_name: vaccineName,
                    vaccine_category: 'primary',
                    recommended_age_days: 0,
                    due_date: today,
                    administered_date: today,
                    administered_by: 'ASHA Worker',
                    status: 'completed'
                });
        }

        // Force refresh data
        await loadData();
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed': return 'status-completed';
            case 'overdue': return 'status-overdue';
            case 'due': return 'status-due';
            default: return 'status-pending';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed': return <Check size={16} />;
            case 'overdue': return <AlertCircle size={16} />;
            case 'due': return <Clock size={16} />;
            default: return <Syringe size={16} />;
        }
    };

    const upcomingVaccines = vaccinations.filter(v =>
        v.status === 'due' || v.status === 'overdue'
    ).slice(0, 10);

    return (
        <div className="postnatal-page">
            <div className="page-header">
                <h2><Syringe className="icon" /> Vaccination Calendar</h2>
                <p>IAP 2023 Immunization Schedule Tracker</p>
            </div>

            {/* Quick Stats */}
            <div className="vaccine-stats">
                <div className="vaccine-stat completed">
                    <Check size={24} />
                    <div>
                        <span className="number">{vaccinations.filter(v => v.status === 'completed').length}</span>
                        <span className="label">Completed</span>
                    </div>
                </div>
                <div className="vaccine-stat due">
                    <Clock size={24} />
                    <div>
                        <span className="number">{vaccinations.filter(v => v.status === 'due').length}</span>
                        <span className="label">Due This Month</span>
                    </div>
                </div>
                <div className="vaccine-stat overdue">
                    <AlertCircle size={24} />
                    <div>
                        <span className="number">{vaccinations.filter(v => v.status === 'overdue').length}</span>
                        <span className="label">Overdue</span>
                    </div>
                </div>
            </div>

            {/* Filter Tabs */}
            <div className="filter-tabs">
                <button className={filter === 'all' ? 'active' : ''} onClick={() => setFilter('all')}>All</button>
                <button className={filter === 'due' ? 'active' : ''} onClick={() => setFilter('due')}>Due</button>
                <button className={filter === 'overdue' ? 'active' : ''} onClick={() => setFilter('overdue')}>Overdue</button>
                <button className={filter === 'completed' ? 'active' : ''} onClick={() => setFilter('completed')}>Completed</button>
            </div>

            {loading ? (
                <div className="loading-state">Loading vaccination data...</div>
            ) : children.length === 0 ? (
                <div className="empty-state">
                    <Syringe size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>Register children to track their vaccination schedules.</p>
                </div>
            ) : (
                <div className="vaccination-list">
                    {children.map(child => (
                        <div key={child.id} className="child-vaccine-card">
                            <div className="child-header" onClick={() => setSelectedChild(selectedChild === child.id ? null : child.id)}>
                                <div className="child-info">
                                    <span className="avatar">{child.gender === 'female' ? '👧' : '👦'}</span>
                                    <div>
                                        <h4>{child.name}</h4>
                                        <p>Born: {new Date(child.birth_date).toLocaleDateString()}</p>
                                    </div>
                                </div>
                                <ChevronRight className={`arrow ${selectedChild === child.id ? 'rotated' : ''}`} />
                            </div>

                            {selectedChild === child.id && (
                                <div className="vaccine-schedule">
                                    <h5>📋 IAP 2023 Schedule</h5>
                                    <div className="vaccine-timeline">
                                        {IAP_SCHEDULE.map((vax, idx) => {
                                            const status = getVaccineStatus(child.id, vax.vaccine);
                                            return (
                                                <div key={idx} className={`vaccine-item ${getStatusColor(status)}`}>
                                                    <div className="vaccine-icon">{getStatusIcon(status)}</div>
                                                    <div className="vaccine-details">
                                                        <span className="vaccine-name">{vax.vaccine}</span>
                                                        <span className="vaccine-desc">{vax.description}</span>
                                                    </div>
                                                    <div className="vaccine-action">
                                                        {status !== 'completed' && (
                                                            <button
                                                                className="btn-mark"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    markVaccineDone(child.id, vax.vaccine);
                                                                }}
                                                                disabled={savingVaccine === `${child.id}-${vax.vaccine}`}
                                                            >
                                                                {savingVaccine === `${child.id}-${vax.vaccine}` ? (
                                                                    <><Loader size={14} className="animate-spin" /> Saving...</>
                                                                ) : (
                                                                    'Mark Done'
                                                                )}
                                                            </button>
                                                        )}
                                                        {status === 'completed' && (
                                                            <span className="completed-badge">✅ Done</span>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* IAP Schedule Reference */}
            <div className="schedule-reference">
                <h4><Info size={18} /> IAP 2023 Immunization Schedule Reference</h4>
                <div className="schedule-note">
                    <p>This schedule follows the Indian Academy of Pediatrics (IAP) 2023 guidelines.</p>
                    <p>Always consult with a healthcare provider for personalized recommendations.</p>
                </div>
            </div>
        </div>
    );
};
