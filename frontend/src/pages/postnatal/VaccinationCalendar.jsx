import React, { useState, useEffect } from 'react';
import { postnatalAPI } from '../../services/api'; // Use centralized API
import { Calendar, Check, AlertCircle, Clock, Syringe, ChevronRight, Info, Loader } from 'lucide-react';
import { showToast } from '../../utils/FixedPatterns';
import './PostnatalPages.css';

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

export const VaccinationCalendar = ({ ashaWorkerId, doctorId }) => {
    const [children, setChildren] = useState([]);
    const [vaccinations, setVaccinations] = useState([]); // Currently loaded vaccinations (for selected child)
    const [loading, setLoading] = useState(true);
    const [loadingVaccines, setLoadingVaccines] = useState(false);
    const [selectedChild, setSelectedChild] = useState(null);
    const [filter, setFilter] = useState('all'); // 'all', 'due', 'overdue', 'completed'
    const [savingVaccine, setSavingVaccine] = useState(null); // Track which vaccine is being saved

    useEffect(() => {
        loadChildren();
    }, [ashaWorkerId, doctorId]);

    useEffect(() => {
        if (selectedChild) {
            loadChildVaccinations(selectedChild);
        } else {
            setVaccinations([]);
        }
    }, [selectedChild]);

    const loadChildren = async () => {
        try {
            setLoading(true);
            const response = await postnatalAPI.getChildren(null, ashaWorkerId, doctorId);
            setChildren(response.children || []);
        } catch (err) {
            console.error('Error loading children:', err);
        } finally {
            setLoading(false);
        }
    };

    const loadChildVaccinations = async (childId) => {
        try {
            setLoadingVaccines(true);
            const response = await postnatalAPI.getVaccinations(childId);
            setVaccinations(response.vaccinations || []);
        } catch (err) {
            console.error('Error loading vaccinations:', err);
        } finally {
            setLoadingVaccines(false);
        }
    };

    const getVaccineStatus = (vaccineName) => {
        const record = vaccinations.find(v => v.vaccine_name === vaccineName);
        if (!record) return 'pending';
        return record.status;
    };

    const markVaccineDone = async (vaccineName) => {
        if (!selectedChild) return;
        setSavingVaccine(`${selectedChild}-${vaccineName}`);

        try {
            // Calculate today as default given date
            const today = new Date().toISOString().split('T')[0];

            await postnatalAPI.recordVaccination({
                child_id: selectedChild,
                vaccine_name: vaccineName,
                given_date: today,
                notes: 'Marked manually'
            });

            // Refresh data
            await loadChildVaccinations(selectedChild);

        } catch (err) {
            console.error('Error marking vaccine done:', err);
            showToast('Failed to update vaccination status', 'error');
        } finally {
            setSavingVaccine(null);
        }
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

    // Filter displayed vaccinations based on tab
    const filteredSchedule = IAP_SCHEDULE.filter(vax => {
        const status = getVaccineStatus(vax.vaccine);
        if (filter === 'all') return true;
        if (filter === 'completed') return status === 'completed';
        if (filter === 'due') return status === 'due' || status === 'pending'; // Showing pending as due for now in calendar view
        if (filter === 'overdue') return status === 'overdue';
        return true;
    });

    return (
        <div className="postnatal-page">
            <div className="page-header">
                <h2><Syringe className="icon" /> Vaccination Calendar</h2>
                <p>IAP 2023 Immunization Schedule Tracker</p>
            </div>

            {loading ? (
                <div className="loading-state">Loading registered children...</div>
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
                            <div
                                className="child-header"
                                onClick={() => setSelectedChild(selectedChild === child.id ? null : child.id)}
                            >
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
                                    {loadingVaccines ? (
                                        <div className="p-4 text-center">Loading vaccinations...</div>
                                    ) : (
                                        <>
                                            {/* Filter Tabs within Child Card */}
                                            <div className="filter-tabs small">
                                                <button className={filter === 'all' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); setFilter('all'); }}>All</button>
                                                <button className={filter === 'due' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); setFilter('due'); }}>Due</button>
                                                <button className={filter === 'completed' ? 'active' : ''} onClick={(e) => { e.stopPropagation(); setFilter('completed'); }}>Completed</button>
                                            </div>

                                            <div className="vaccine-timeline">
                                                {filteredSchedule.map((vax, idx) => {
                                                    const status = getVaccineStatus(vax.vaccine);
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
                                                                            markVaccineDone(vax.vaccine);
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
                                                {filteredSchedule.length === 0 && (
                                                    <div className="text-center p-3 text-slate-400">No vaccines found for this filter</div>
                                                )}
                                            </div>
                                        </>
                                    )}
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
