import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import { Search, Plus, User, Calendar, Weight, Ruler, Activity, ChevronRight, Baby } from 'lucide-react';
import './PostnatalPages.css';

export const ChildrenList = ({ ashaWorkerId }) => {
    const [children, setChildren] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedChild, setSelectedChild] = useState(null);
    const [showAddForm, setShowAddForm] = useState(false);

    useEffect(() => {
        let isMounted = true;

        const fetchChildren = async () => {
            try {
                setLoading(true);
                // Get children through their mothers assigned to this ASHA worker
                const { data, error } = await supabase
                    .from('children')
                    .select(`
          *,
          mothers:mother_id (
            id, name, phone, location, asha_worker_id
          )
        `)
                    .order('birth_date', { ascending: false });

                if (isMounted) {
                    if (!error && data) {
                        // Filter by ASHA worker if needed
                        const filteredChildren = ashaWorkerId
                            ? data.filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                            : data;
                        setChildren(filteredChildren);
                    }
                    setLoading(false);
                }
            } catch (err) {
                if (isMounted) {
                    console.error('Error loading children:', err);
                    setLoading(false);
                }
            }
        };

        fetchChildren();

        return () => {
            isMounted = false;
        };
    }, [ashaWorkerId]);

    const calculateAge = (birthDate) => {
        const birth = new Date(birthDate);
        const now = new Date();
        const diffDays = Math.floor((now - birth) / (1000 * 60 * 60 * 24));

        if (diffDays < 30) return `${diffDays} days`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months`;
        return `${Math.floor(diffDays / 365)} years ${Math.floor((diffDays % 365) / 30)} months`;
    };

    const filteredChildren = children.filter(child =>
        child.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        child.mothers?.name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="postnatal-page">
            <div className="page-header">
                <h2><Baby className="icon" /> Children Registry</h2>
                <p>Manage and monitor all registered children (0-5 years)</p>
            </div>

            <div className="page-actions">
                <div className="search-box">
                    <Search className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search children or mothers..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <button className="btn-primary" onClick={() => setShowAddForm(true)}>
                    <Plus className="icon" /> Register Child
                </button>
            </div>

            {loading ? (
                <div className="loading-state">Loading children...</div>
            ) : filteredChildren.length === 0 ? (
                <div className="empty-state">
                    <Baby size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>When a delivery is completed and a child is registered, they will appear here.</p>
                    <button className="btn-primary" onClick={() => setShowAddForm(true)}>
                        <Plus className="icon" /> Register First Child
                    </button>
                </div>
            ) : (
                <div className="children-grid">
                    {filteredChildren.map(child => (
                        <div key={child.id} className="child-card" onClick={() => setSelectedChild(child)}>
                            <div className="child-avatar">
                                {child.gender === 'female' ? '👧' : '👦'}
                            </div>
                            <div className="child-info">
                                <h3>{child.name}</h3>
                                <p className="age">{calculateAge(child.birth_date)}</p>
                                <p className="mother">Mother: {child.mothers?.name || 'Unknown'}</p>
                            </div>
                            <div className="child-stats">
                                <div className="stat">
                                    <Weight size={16} />
                                    <span>{child.birth_weight_kg || '-'} kg</span>
                                </div>
                                <div className="stat">
                                    <Ruler size={16} />
                                    <span>{child.birth_length_cm || '-'} cm</span>
                                </div>
                            </div>
                            <ChevronRight className="arrow" />
                        </div>
                    ))}
                </div>
            )}

            {/* Child Detail Modal would go here */}
            {selectedChild && (
                <div className="modal-overlay" onClick={() => setSelectedChild(null)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>{selectedChild.gender === 'female' ? '👧' : '👦'} {selectedChild.name}</h2>
                            <button onClick={() => setSelectedChild(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="info-grid">
                                <div className="info-item">
                                    <label>Date of Birth</label>
                                    <span>{new Date(selectedChild.birth_date).toLocaleDateString()}</span>
                                </div>
                                <div className="info-item">
                                    <label>Age</label>
                                    <span>{calculateAge(selectedChild.birth_date)}</span>
                                </div>
                                <div className="info-item">
                                    <label>Gender</label>
                                    <span className="capitalize">{selectedChild.gender}</span>
                                </div>
                                <div className="info-item">
                                    <label>Birth Weight</label>
                                    <span>{selectedChild.birth_weight_kg || '-'} kg</span>
                                </div>
                                <div className="info-item">
                                    <label>Birth Length</label>
                                    <span>{selectedChild.birth_length_cm || '-'} cm</span>
                                </div>
                                <div className="info-item">
                                    <label>Mother</label>
                                    <span>{selectedChild.mothers?.name || 'Unknown'}</span>
                                </div>
                            </div>
                            <div className="quick-actions">
                                <button className="btn-secondary">📈 View Growth</button>
                                <button className="btn-secondary">💉 Vaccinations</button>
                                <button className="btn-secondary">🎯 Milestones</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
