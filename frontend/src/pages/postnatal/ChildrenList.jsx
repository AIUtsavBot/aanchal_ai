import React, { useState, useEffect } from 'react';
import { postnatalAPI } from '../../services/api';
import { Search, Plus, User, Calendar, Weight, Ruler, Activity, ChevronRight, Baby, UserPlus, X } from 'lucide-react';
import { showToast } from '../../utils/FixedPatterns';
import './PostnatalPages.css';

export const ChildrenList = ({ ashaWorkerId, doctorId }) => {
    const [children, setChildren] = useState([]);
    const [mothers, setMothers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedChild, setSelectedChild] = useState(null);
    const [showAddForm, setShowAddForm] = useState(false);

    // New Child State
    const [newChild, setNewChild] = useState({
        name: '',
        birth_date: new Date().toISOString().split('T')[0],
        gender: 'male',
        birth_weight_kg: '',
        mother_id: ''
    });

    useEffect(() => {
        loadChildren();
        loadMothers();
    }, [ashaWorkerId, doctorId]);

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

    const loadMothers = async () => {
        try {
            const response = await postnatalAPI.getMothers(ashaWorkerId, doctorId);
            setMothers(response.mothers || []);
        } catch (err) {
            console.error('Error loading mothers:', err);
        }
    };

    const handleRegisterChild = async () => {
        if (!newChild.name || !newChild.mother_id || !newChild.birth_date) {
            showToast('Please fill in all required fields', 'error');
            return;
        }

        try {
            const response = await postnatalAPI.registerChild(newChild);
            if (response) {
                showToast('Child registered successfully!', 'success');
                setShowAddForm(false);
                setNewChild({
                    name: '',
                    birth_date: new Date().toISOString().split('T')[0],
                    gender: 'male',
                    birth_weight_kg: '',
                    mother_id: ''
                });
                loadChildren(); // Reload list
            }
        } catch (err) {
            console.error('Error registering child:', err);
            showToast('Failed to register child. Please try again.', 'error');
        }
    };

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
                    <UserPlus className="icon" size={16} /> Register Child
                </button>
            </div>

            {loading ? (
                <div className="loading-state">Loading children...</div>
            ) : filteredChildren.length === 0 ? (
                <div className="empty-state">
                    <Baby size={64} className="empty-icon" />
                    <h3>No Children Registered</h3>
                    <p>When a delivery is completed and a child is registered, they will appear here.</p>
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

            {/* Child Details Modal */}
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
                                {/* Actions will navigate to respective tabs in future update */}
                                <button className="btn-secondary" disabled>📈 View Growth (Use Tabs)</button>
                                <button className="btn-secondary" disabled>💉 Vaccinations (Use Tabs)</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Register Child Modal */}
            {showAddForm && (
                <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
                    <div className="modal-content assessment-panel" onClick={e => e.stopPropagation()}>
                        <div className="panel-header">
                            <h4>👶 Register New Child</h4>
                            <button className="btn-secondary" onClick={() => setShowAddForm(false)}>
                                <X size={16} />
                            </button>
                        </div>
                        <div className="assessment-form">
                            <div className="form-section">
                                <h6>Child Details</h6>
                                <div className="form-row">
                                    <div className="form-field full">
                                        <label>Select Mother *</label>
                                        <select
                                            value={newChild.mother_id}
                                            onChange={e => setNewChild({ ...newChild, mother_id: e.target.value })}
                                        >
                                            <option value="">-- Select Mother --</option>
                                            {mothers.map(m => (
                                                <option key={m.id} value={m.id}>{m.name} (ID: {m.id.substring(0, 6)}...)</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-row">
                                    <div className="form-field">
                                        <label>Child Name *</label>
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
                                    <button className="btn-secondary" onClick={() => setShowAddForm(false)}>Cancel</button>
                                    <button className="btn-primary" onClick={handleRegisterChild}>Register Child</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
