import React, { useState, useEffect } from 'react';
import { supabase } from '../../services/auth.js';
import { ChildrenList } from './ChildrenList.jsx';
import { VaccinationCalendar } from './VaccinationCalendar.jsx';
import { GrowthCharts } from './GrowthCharts.jsx';
import { MilestonesTracker } from './MilestonesTracker.jsx';
import { PostnatalAssessments } from './PostnatalAssessments.jsx';
import {
    Home,
    Baby,
    Activity,
    Syringe,
    ClipboardList,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    ArrowLeft,
    ClipboardCheck,
    Target,
    Calendar,
    Users,
    MessageCircle,
    AlertCircle
} from 'lucide-react';
import { useView } from '../../contexts/ViewContext';
import './PostnatalDashboard.css';
import './PostnatalAssessments.css';


export const PostnatalDashboard = ({ ashaWorkerId, doctorId, userRole }) => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [stats, setStats] = useState({
        deliveredMothers: 0,
        childrenRegistered: 0,
        vaccinesDue: 0,
        growthAlerts: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        const fetchStats = async () => {
            try {
                setLoading(true);

                // Get children count
                const { data: children } = await supabase
                    .from('children')
                    .select('id, mothers:mother_id(asha_worker_id)')
                    .order('created_at', { ascending: false });

                // Get delivered mothers count
                const { data: mothers } = await supabase
                    .from('mothers')
                    .select('id, delivery_status, asha_worker_id')
                    .eq('delivery_status', 'delivered');

                // Get due vaccines
                const { data: vaccines } = await supabase
                    .from('vaccinations')
                    .select('id, status')
                    .in('status', ['due', 'overdue']);

                // Get growth alerts - use correct column name weight_for_age_z_score
                let growthAlerts = 0;
                try {
                    const { data: growth } = await supabase
                        .from('growth_records')
                        .select('id, weight_for_age_z_score')
                        .or('weight_for_age_z_score.lt.-2,weight_for_age_z_score.gt.2');
                    growthAlerts = (growth || []).length;
                } catch (err) {
                    if (isMounted) {
                        console.log('Growth records query error (column may not exist):', err);
                    }
                }

                if (isMounted) {
                    const filteredChildren = ashaWorkerId
                        ? (children || []).filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                        : (children || []);

                    const filteredMothers = ashaWorkerId
                        ? (mothers || []).filter(m => m.asha_worker_id === ashaWorkerId)
                        : (mothers || []);

                    setStats({
                        deliveredMothers: filteredMothers.length,
                        childrenRegistered: filteredChildren.length,
                        vaccinesDue: (vaccines || []).length,
                        growthAlerts: growthAlerts
                    });
                    setLoading(false);
                }
            } catch (err) {
                if (isMounted) {
                    console.error('Error loading stats:', err);
                    setLoading(false);
                }
            }
        };

        fetchStats();

        return () => {
            isMounted = false;
        };
    }, [ashaWorkerId]);

    const loadStats = async () => {
        try {
            setLoading(true);

            // Get children count
            const { data: children } = await supabase
                .from('children')
                .select('id, mothers:mother_id(asha_worker_id)')
                .order('created_at', { ascending: false });

            // Get delivered mothers count
            const { data: mothers } = await supabase
                .from('mothers')
                .select('id, delivery_status, asha_worker_id')
                .eq('delivery_status', 'delivered');

            // Get due vaccines
            const { data: vaccines } = await supabase
                .from('vaccinations')
                .select('id, status')
                .in('status', ['due', 'overdue']);

            // Get growth alerts - use correct column name weight_for_age_z_score
            let growthAlerts = 0;
            try {
                const { data: growth } = await supabase
                    .from('growth_records')
                    .select('id, weight_for_age_z_score')
                    .or('weight_for_age_z_score.lt.-2,weight_for_age_z_score.gt.2');
                growthAlerts = (growth || []).length;
            } catch (err) {
                console.log('Growth records query error (column may not exist):', err);
            }

            const filteredChildren = ashaWorkerId
                ? (children || []).filter(c => c.mothers?.asha_worker_id === ashaWorkerId)
                : (children || []);

            const filteredMothers = ashaWorkerId
                ? (mothers || []).filter(m => m.asha_worker_id === ashaWorkerId)
                : (mothers || []);

            setStats({
                deliveredMothers: filteredMothers.length,
                childrenRegistered: filteredChildren.length,
                vaccinesDue: (vaccines || []).length,
                growthAlerts: growthAlerts
            });
        } catch (err) {
            console.error('Error loading stats:', err);
        } finally {
            setLoading(false);
        }
    };

    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: Home },
        { id: 'assessments', label: 'Assessments', icon: ClipboardCheck },
        { id: 'children', label: 'Children', icon: Baby },
        { id: 'vaccines', label: 'Vaccines', icon: Syringe },
        { id: 'growth', label: 'Growth', icon: TrendingUp },
        { id: 'milestones', label: 'Milestones', icon: Target },
    ];

    const renderContent = () => {
        switch (activeTab) {
            case 'assessments':
                return <PostnatalAssessments
                    ashaWorkerId={ashaWorkerId}
                    doctorId={doctorId}
                    userRole={userRole}
                    onUpdate={loadStats}
                />;
            case 'children':
                return <ChildrenList ashaWorkerId={ashaWorkerId} />;
            case 'vaccines':
                return <VaccinationCalendar ashaWorkerId={ashaWorkerId} />;
            case 'growth':
                return <GrowthCharts ashaWorkerId={ashaWorkerId} />;
            case 'milestones':
                return <MilestonesTracker ashaWorkerId={ashaWorkerId} />;
            default:
                return renderDashboard();
        }
    };

    const renderDashboard = () => (
        <div className="dashboard-content">
            <div className="dashboard-header">
                <h2>🍼 Postnatal & Child Care Dashboard</h2>
                <p className="subtitle">SantanRaksha - Monitor mothers and children after delivery</p>
            </div>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card" onClick={() => setActiveTab('children')}>
                    <div className="stat-icon mothers">👩‍👧</div>
                    <div className="stat-content">
                        <h3>DELIVERED MOTHERS</h3>
                        <p className="stat-number">{stats.deliveredMothers}</p>
                        <p className="stat-label">Under postnatal care</p>
                    </div>
                </div>

                <div className="stat-card" onClick={() => setActiveTab('children')}>
                    <div className="stat-icon children">👶</div>
                    <div className="stat-content">
                        <h3>CHILDREN REGISTERED</h3>
                        <p className="stat-number">{stats.childrenRegistered}</p>
                        <p className="stat-label">Active profiles</p>
                    </div>
                </div>

                <div className="stat-card vaccines" onClick={() => setActiveTab('vaccines')}>
                    <div className="stat-icon vaccines">💉</div>
                    <div className="stat-content">
                        <h3>VACCINES DUE</h3>
                        <p className="stat-number">{stats.vaccinesDue}</p>
                        <p className="stat-label">This month</p>
                    </div>
                </div>

                <div className="stat-card growth" onClick={() => setActiveTab('growth')}>
                    <div className="stat-icon growth">📊</div>
                    <div className="stat-content">
                        <h3>GROWTH ALERTS</h3>
                        <p className="stat-number">{stats.growthAlerts}</p>
                        <p className="stat-label">Needs attention</p>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions-section">
                <h3>Quick Actions</h3>
                <div className="quick-actions-grid">
                    <button className="action-btn" onClick={() => setActiveTab('children')}>
                        <Baby size={24} />
                        <span>View Children</span>
                    </button>
                    <button className="action-btn" onClick={() => setActiveTab('vaccines')}>
                        <Syringe size={24} />
                        <span>Vaccination Calendar</span>
                    </button>
                    <button className="action-btn" onClick={() => setActiveTab('growth')}>
                        <TrendingUp size={24} />
                        <span>Growth Charts</span>
                    </button>
                    <button className="action-btn" onClick={() => setActiveTab('milestones')}>
                        <Target size={24} />
                        <span>Milestones</span>
                    </button>
                    <button className="action-btn" onClick={() => setActiveTab('assessments')}>
                        <Calendar size={24} />
                        <span>Postnatal Checkups</span>
                    </button>
                    <button className="action-btn">
                        <MessageCircle size={24} />
                        <span>AI Assistant</span>
                    </button>
                </div>
            </div>

            {/* Clinical Standards */}
            <div className="standards-section">
                <h4>📋 Clinical Standards</h4>
                <div className="standards-badges">
                    <span className="badge">NHM SUMAN</span>
                    <span className="badge">WHO Growth Standards</span>
                    <span className="badge">IAP 2023</span>
                    <span className="badge">IMNCI</span>
                    <span className="badge">RBSK</span>
                    <span className="badge">WHO IYCF</span>
                </div>
            </div>

            {/* Info Card */}
            <div className="info-card">
                <h3>🎉 Welcome to SantanRaksha!</h3>
                <p>
                    This is your postnatal and child health monitoring dashboard. Here you can:
                </p>
                <ul>
                    <li>Track mothers' postnatal recovery (0-6 weeks)</li>
                    <li>Monitor children's growth and development (0-5 years)</li>
                    <li>Manage vaccination schedules (IAP 2023)</li>
                    <li>Track developmental milestones (RBSK 4Ds)</li>
                    <li>Get AI-powered health guidance</li>
                </ul>
            </div>
        </div>
    );

    return (
        <div className="postnatal-dashboard-wrapper">
            {/* Tab Navigation */}
            <div className="postnatal-tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <tab.icon size={18} />
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="postnatal-content">
                {loading && activeTab === 'dashboard' ? (
                    <div className="loading-state">Loading dashboard...</div>
                ) : (
                    renderContent()
                )}
            </div>
        </div>
    );
};
