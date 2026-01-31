import React, { useState, useEffect, useRef } from 'react';
import { supabase } from '../../services/auth.js';
import { Target, Check, Clock, AlertCircle, Baby, Brain, Hand, MessageCircle, Heart, Loader } from 'lucide-react';
import './PostnatalPages.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// RBSK 4Ds Developmental Milestones
const MILESTONES_BY_AGE = [
    {
        age_months: 0,
        age_label: 'Birth - 1 Month',
        milestones: [
            { category: 'Motor', icon: '💪', name: 'Moves arms and legs', description: 'Shows active limb movements' },
            { category: 'Sensory', icon: '👁️', name: 'Responds to sounds', description: 'Startles or blinks to loud sounds' },
            { category: 'Social', icon: '😊', name: 'Looks at faces', description: 'Focuses briefly on caregiver\'s face' },
        ]
    },
    {
        age_months: 2,
        age_label: '2 Months',
        milestones: [
            { category: 'Motor', icon: '💪', name: 'Lifts head briefly', description: 'When lying on tummy' },
            { category: 'Social', icon: '😊', name: 'Social smile', description: 'Smiles in response to caregiver' },
            { category: 'Sensory', icon: '👁️', name: 'Follows objects', description: 'Tracks moving objects with eyes' },
        ]
    },
    {
        age_months: 4,
        age_label: '4 Months',
        milestones: [
            { category: 'Motor', icon: '💪', name: 'Holds head steady', description: 'Good head control when supported' },
            { category: 'Motor', icon: '✋', name: 'Reaches for objects', description: 'Attempts to grasp toys' },
            { category: 'Language', icon: '🗣️', name: 'Coos and babbles', description: 'Makes vowel sounds' },
            { category: 'Social', icon: '😊', name: 'Laughs', description: 'Laughs out loud' },
        ]
    },
    {
        age_months: 6,
        age_label: '6 Months',
        milestones: [
            { category: 'Motor', icon: '💪', name: 'Sits with support', description: 'Sits when propped' },
            { category: 'Motor', icon: '✋', name: 'Transfers objects', description: 'Passes toy from hand to hand' },
            { category: 'Language', icon: '🗣️', name: 'Responds to name', description: 'Turns when name is called' },
            { category: 'Social', icon: '😊', name: 'Stranger anxiety', description: 'Shows preference for familiar faces' },
        ]
    },
    {
        age_months: 9,
        age_label: '9 Months',
        milestones: [
            { category: 'Motor', icon: '💪', name: 'Sits without support', description: 'Sits independently' },
            { category: 'Motor', icon: '🚶', name: 'Crawls', description: 'Moves on hands and knees' },
            { category: 'Motor', icon: '✋', name: 'Pincer grasp developing', description: 'Picks small objects with fingers' },
            { category: 'Language', icon: '🗣️', name: 'Says mama/dada', description: 'Non-specific babbling' },
        ]
    },
    {
        age_months: 12,
        age_label: '12 Months (1 Year)',
        milestones: [
            { category: 'Motor', icon: '🚶', name: 'Stands alone', description: 'Stands without support briefly' },
            { category: 'Motor', icon: '🚶', name: 'Walks with support', description: 'Cruises along furniture' },
            { category: 'Language', icon: '🗣️', name: '1-2 words', description: 'Says specific words like mama/dada' },
            { category: 'Cognitive', icon: '🧠', name: 'Object permanence', description: 'Looks for hidden objects' },
        ]
    },
    {
        age_months: 18,
        age_label: '18 Months',
        milestones: [
            { category: 'Motor', icon: '🚶', name: 'Walks independently', description: 'Walks without support' },
            { category: 'Motor', icon: '✋', name: 'Scribbles', description: 'Holds crayon and scribbles' },
            { category: 'Language', icon: '🗣️', name: '15-20 words', description: 'Vocabulary expanding' },
            { category: 'Social', icon: '😊', name: 'Parallel play', description: 'Plays alongside other children' },
        ]
    },
    {
        age_months: 24,
        age_label: '24 Months (2 Years)',
        milestones: [
            { category: 'Motor', icon: '🚶', name: 'Runs', description: 'Runs with coordination' },
            { category: 'Motor', icon: '⚽', name: 'Kicks ball', description: 'Kicks ball forward' },
            { category: 'Language', icon: '🗣️', name: '2-word sentences', description: 'Combines words' },
            { category: 'Cognitive', icon: '🧠', name: 'Follows 2-step commands', description: 'Understands instructions' },
        ]
    },
];

export const MilestonesTracker = ({ ashaWorkerId }) => {
    const [children, setChildren] = useState([]);
    const [milestoneRecords, setMilestoneRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedChild, setSelectedChild] = useState(null);
    const [expandedAge, setExpandedAge] = useState(null);
    const [togglingMilestone, setTogglingMilestone] = useState(null);

    // Ref to track pending operations synchronously (prevents race conditions from rapid clicks)
    const pendingToggles = useRef(new Set());

    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                setLoading(true);

                const { data: childrenData } = await supabase
                    .from('children')
                    .select('*, mothers:mother_id(name, asha_worker_id)')
                    .order('birth_date', { ascending: false });

                const { data: milestonesData } = await supabase
                    .from('milestones')
                    .select('*')
                    .eq('is_achieved', true)
                    .order('achieved_date', { ascending: false });

                if (isMounted) {
                    if (childrenData) {
                        const filtered = ashaWorkerId
                            ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                            : childrenData;
                        setChildren(filtered);
                    }
                    if (milestonesData) setMilestoneRecords(milestonesData);
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

            const { data: milestonesData } = await supabase
                .from('milestones')
                .select('*')
                .eq('is_achieved', true)
                .order('achieved_date', { ascending: false });

            if (childrenData) {
                const filtered = ashaWorkerId
                    ? childrenData.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                    : childrenData;
                setChildren(filtered);
            }
            if (milestonesData) setMilestoneRecords(milestonesData);
        } catch (err) {
            console.error('Error loading data:', err);
        } finally {
            setLoading(false);
        }
    };

    const getChildAgeMonths = (birthDate) => {
        const birth = new Date(birthDate);
        const now = new Date();
        return Math.floor((now - birth) / (1000 * 60 * 60 * 24 * 30));
    };

    const isMilestoneAchieved = (childId, milestoneName) => {
        return milestoneRecords.some(m =>
            m.child_id === childId &&
            m.milestone_name === milestoneName &&
            m.is_achieved === true
        );
    };

    const toggleMilestone = async (childId, milestone) => {
        const key = `${childId}-${milestone.name}`;

        // Check ref synchronously to prevent race conditions from rapid clicks
        if (pendingToggles.current.has(key)) {
            return;
        }

        // Add to pending set immediately (synchronous)
        pendingToggles.current.add(key);
        setTogglingMilestone(key);

        try {
            // Use the new API endpoint
            const response = await fetch(`${API_URL}/api/santanraksha/milestone/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    child_id: childId,
                    milestone_name: milestone.name,
                    milestone_category: milestone.category,
                    notes: ''
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Milestone toggled:', result);
                // Force refresh data immediately
                await loadData();
            } else {
                const errorData = await response.json();
                console.error('API error:', errorData);
                // Fallback to direct Supabase operation with correct column names
                await fallbackToggleMilestone(childId, milestone);
            }
        } catch (err) {
            console.error('Error toggling milestone:', err);
            // Fallback to direct Supabase
            await fallbackToggleMilestone(childId, milestone);
        } finally {
            pendingToggles.current.delete(key);
            setTogglingMilestone(null);
        }
    };

    const fallbackToggleMilestone = async (childId, milestone) => {
        const isAchieved = isMilestoneAchieved(childId, milestone.name);

        // Get child age for the record
        const childData = children.find(c => c.id === childId);
        let age_months = 0;
        let age_days = 0;
        if (childData?.birth_date) {
            const birth = new Date(childData.birth_date);
            const now = new Date();
            age_days = Math.floor((now - birth) / (1000 * 60 * 60 * 24));
            age_months = Math.floor(age_days / 30);
        }

        // Map category to DB enum
        const categoryMap = {
            'Motor': 'gross_motor',
            'Fine Motor': 'fine_motor',
            'Language': 'language',
            'Cognitive': 'cognitive',
            'Social': 'social_emotional',
            'Sensory': 'cognitive',
            'Self Care': 'self_care'
        };
        const dbCategory = categoryMap[milestone.category] || 'gross_motor';

        if (isAchieved) {
            // Find and update the record to is_achieved: false
            const record = milestoneRecords.find(m =>
                m.child_id === childId &&
                m.milestone_name === milestone.name
            );
            if (record) {
                await supabase
                    .from('milestones')
                    .update({
                        is_achieved: false,
                        achieved_date: null,
                        achieved_age_months: null,
                        achieved_age_days: null
                    })
                    .eq('id', record.id);
            }
        } else {
            // Insert new milestone with correct columns
            await supabase.from('milestones').insert({
                child_id: childId,
                milestone_name: milestone.name,
                category: dbCategory,
                expected_age_months: age_months,
                is_achieved: true,
                achieved_date: new Date().toISOString().split('T')[0],
                achieved_age_months: age_months,
                achieved_age_days: age_days,
                observation_method: 'parent_report',
                notes: ''
            });
        }
        // Force refresh data
        await loadData();
    };

    const getProgressPercent = (childId, ageMonths) => {
        const ageGroup = MILESTONES_BY_AGE.find(g => g.age_months === ageMonths);
        if (!ageGroup) return 0;

        const achieved = ageGroup.milestones.filter(m => isMilestoneAchieved(childId, m.name)).length;
        return Math.round((achieved / ageGroup.milestones.length) * 100);
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'Motor': return <Hand size={16} />;
            case 'Language': return <MessageCircle size={16} />;
            case 'Cognitive': return <Brain size={16} />;
            case 'Social': return <Heart size={16} />;
            default: return <Target size={16} />;
        }
    };

    return (
        <div className="postnatal-page">
            <div className="page-header">
                <h2><Target className="icon" /> Developmental Milestones</h2>
                <p>RBSK 4Ds Screening - Track child development progress</p>
            </div>

            {/* Categories Legend */}
            <div className="categories-legend">
                <div className="category-item"><Hand size={16} /> Motor</div>
                <div className="category-item"><MessageCircle size={16} /> Language</div>
                <div className="category-item"><Brain size={16} /> Cognitive</div>
                <div className="category-item"><Heart size={16} /> Social-Emotional</div>
            </div>

            {loading ? (
                <div className="loading-state">Loading milestones...</div>
            ) : children.length === 0 ? (
                <div className="empty-state">
                    <Target size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>Register children to track their developmental milestones.</p>
                </div>
            ) : (
                <div className="milestones-container">
                    {/* Child Selector */}
                    <div className="child-selector">
                        {children.map(child => (
                            <button
                                key={child.id}
                                className={`child-btn ${selectedChild === child.id ? 'active' : ''}`}
                                onClick={() => setSelectedChild(child.id)}
                            >
                                <span className="avatar">{child.gender === 'female' ? '👧' : '👦'}</span>
                                <span>{child.name}</span>
                                <span className="age">{getChildAgeMonths(child.birth_date)}m</span>
                            </button>
                        ))}
                    </div>

                    {selectedChild ? (
                        <div className="milestones-timeline">
                            {MILESTONES_BY_AGE.map((ageGroup, idx) => {
                                const progress = getProgressPercent(selectedChild, ageGroup.age_months);
                                const childAge = getChildAgeMonths(children.find(c => c.id === selectedChild)?.birth_date || new Date());
                                const isCurrentAge = ageGroup.age_months <= childAge && (idx === MILESTONES_BY_AGE.length - 1 || MILESTONES_BY_AGE[idx + 1].age_months > childAge);

                                return (
                                    <div key={idx} className={`age-group ${isCurrentAge ? 'current' : ''}`}>
                                        <div
                                            className="age-header"
                                            onClick={() => setExpandedAge(expandedAge === ageGroup.age_months ? null : ageGroup.age_months)}
                                        >
                                            <div className="age-info">
                                                <span className="age-label">{ageGroup.age_label}</span>
                                                {isCurrentAge && <span className="current-badge">Current</span>}
                                            </div>
                                            <div className="progress-indicator">
                                                <div className="progress-bar">
                                                    <div className="progress-fill" style={{ width: `${progress}%` }}></div>
                                                </div>
                                                <span className="progress-text">{progress}%</span>
                                            </div>
                                        </div>

                                        {(expandedAge === ageGroup.age_months || isCurrentAge) && (
                                            <div className="milestones-list">
                                                {ageGroup.milestones.map((milestone, mIdx) => {
                                                    const achieved = isMilestoneAchieved(selectedChild, milestone.name);
                                                    return (
                                                        <div
                                                            key={mIdx}
                                                            className={`milestone-item ${achieved ? 'achieved' : ''} ${togglingMilestone === `${selectedChild}-${milestone.name}` ? 'toggling' : ''}`}
                                                            onClick={() => !togglingMilestone && toggleMilestone(selectedChild, milestone)}
                                                        >
                                                            <div className="milestone-check">
                                                                {togglingMilestone === `${selectedChild}-${milestone.name}` ? (
                                                                    <Loader size={18} className="animate-spin" />
                                                                ) : achieved ? (
                                                                    <Check size={18} />
                                                                ) : (
                                                                    <Clock size={18} />
                                                                )}
                                                            </div>
                                                            <div className="milestone-icon">{milestone.icon}</div>
                                                            <div className="milestone-details">
                                                                <span className="milestone-name">{milestone.name}</span>
                                                                <span className="milestone-desc">{milestone.description}</span>
                                                            </div>
                                                            <div className="milestone-category">
                                                                {getCategoryIcon(milestone.category)}
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="select-child-prompt">
                            <Baby size={48} />
                            <p>Select a child to view and track their milestones</p>
                        </div>
                    )}
                </div>
            )}

            {/* Alert for delays */}
            <div className="delay-alert">
                <AlertCircle size={18} />
                <p>
                    <strong>Note:</strong> If a child has not achieved milestones for their age group,
                    please refer for developmental assessment. Early intervention is key!
                </p>
            </div>
        </div>
    );
};
