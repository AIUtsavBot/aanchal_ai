// =============================================================================
// CRITICAL FIX: Backend Freeze Issue
// =============================================================================
// This file contains the refactored async operations with proper error handling,
// loading states, and cleanup to prevent UI freezes.
// 
// Apply these patterns to PostnatalAssessments.jsx and other components.
// =============================================================================

import { useState, useEffect, useRef, useCallback } from 'react';
import { supabase } from '../../services/auth.js';

// =============================================================================
// UTILITY: Request Timeout Wrapper
// =============================================================================
export const withTimeout = (promise, ms = 30000) => {
    return Promise.race([
        promise,
        new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout - please check your connection')), ms)
        )
    ]);
};

// =============================================================================
// UTILITY: Toast Notification (Replace alert())
// =============================================================================
export const showToast = (message, type = 'info') => {
    // TODO: Implement actual toast UI component
    // For now, use non-blocking notification
    console.log(`[${type.toUpperCase()}]`, message);

    // Temporary: Create a simple toast div
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        background: ${type === 'error' ? '#ef4444' : '#10b981'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
};

// =============================================================================
// PATTERN: Proper Data Loading with Cleanup
// =============================================================================
export const useDataLoading = (loadFunction, dependencies = []) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const abortControllerRef = useRef(null);

    const load = useCallback(async () => {
        // Cancel previous request if still running
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        abortControllerRef.current = new AbortController();
        setLoading(true);
        setError(null);

        try {
            const result = await withTimeout(
                loadFunction(abortControllerRef.current.signal),
                30000
            );
            setData(result);
            return result;
        } catch (err) {
            if (err.name !== 'AbortError') {
                console.error('Data loading error:', err);
                setError(err.message || 'Failed to load data');
                showToast(err.message || 'Failed to load data', 'error');
            }
            return null;
        } finally {
            setLoading(false);
        }
    }, dependencies);

    useEffect(() => {
        load();

        // Cleanup: Abort any pending requests when unmounting
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, [load]);

    return { data, loading, error, reload: load };
};

// =============================================================================
// FIXED: loadData Pattern
// =============================================================================
export const createLoadDataFunction = (ashaWorkerId, doctorId) => {
    return async (signal) => {
        // Build query with filters
        let query = supabase
            .from('mothers')
            .select('*')
            .eq('status', 'postnatal')
            .abortSignal(signal);

        if (ashaWorkerId) query = query.eq('asha_worker_id', ashaWorkerId);
        if (doctorId) query = query.eq('doctor_id', doctorId);

        const { data: mothersData, error: mothersError } = await query;

        if (mothersError) throw mothersError;

        // Load children for these mothers
        let childrenData = [];
        if (mothersData && mothersData.length > 0) {
            const motherIds = mothersData.map(m => m.id);
            const { data, error } = await supabase
                .from('children')
                .select('*')
                .in('mother_id', motherIds)
                .abortSignal(signal);

            if (!error && data) {
                childrenData = data;
            }
        }

        return {
            mothers: mothersData || [],
            children: childrenData
        };
    };
};

// =============================================================================
// FIXED: loadAssessments Pattern
// =============================================================================
export const createLoadAssessmentsFunction = (motherId, childId) => {
    return async (signal) => {
        let query = supabase
            .from('postnatal_assessments')
            .select('*')
            .abortSignal(signal);

        if (motherId) query = query.eq('mother_id', motherId);
        if (childId) query = query.eq('child_id', childId);

        query = query.order('assessment_date', { ascending: false });

        const { data, error } = await query;

        if (error) throw error;

        return data || [];
    };
};

// =============================================================================
// FIXED: Submit Assessment Pattern
// =============================================================================
export const createSubmitAssessment = (setShowForm, loadAssessments, onUpdate) => {
    return async (assessmentData, selectedEntity, entityType = 'mother') => {
        try {
            const { error } = await withTimeout(
                supabase.from('postnatal_assessments').insert(assessmentData),
                15000 // 15 second timeout for writes
            );

            if (error) throw error;

            showToast(
                `${entityType === 'mother' ? 'Mother' : 'Child'} assessment saved successfully!`,
                'success'
            );

            setShowForm(null);

            // Reload assessments
            if (entityType === 'mother') {
                await loadAssessments(selectedEntity.id);
            } else {
                await loadAssessments(null, selectedEntity.id);
            }

            if (onUpdate) onUpdate();

            return true;
        } catch (err) {
            console.error('Error saving assessment:', err);
            showToast(
                `Failed to save assessment: ${err.message || 'Unknown error'}`,
                'error'
            );
            return false;
        }
    };
};

// =============================================================================
// ERROR BOUNDARY COMPONENT
// =============================================================================
import React from 'react';

export class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error boundary caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    padding: '2rem',
                    background: '#fee2e2',
                    border: '2px solid #ef4444',
                    borderRadius: '8px',
                    margin: '2rem'
                }}>
                    <h2 style={{ color: '#991b1b' }}>⚠️ Something went wrong</h2>
                    <p>{this.state.error?.message || 'Unknown error'}</p>
                    <button
                        onClick={() => {
                            this.setState({ hasError: false, error: null });
                            window.location.reload();
                        }}
                        style={{
                            padding: '8px 16px',
                            background: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            marginTop: '1rem'
                        }}
                    >
                        Reload Page
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

// =============================================================================
// USAGE EXAMPLE
// =============================================================================
/*
// In your component:
import { useDataLoading, createSubmitAssessment, showToast, ErrorBoundary } from './FixedPatterns';

export const PostnatalAssessments = ({ ashaWorkerId, doctorId, userRole, onUpdate }) => {
    const [selectedMother, setSelectedMother] = useState(null);
    const [showForm, setShowForm] = useState(null);
    const [assessments, setAssessments] = useState([]);

    // Use the hook for automatic loading with cleanup
    const { 
        data: entityData, 
        loading, 
        error, 
        reload 
    } = useDataLoading(
        createLoadDataFunction(ashaWorkerId, doctorId),
        [ashaWorkerId, doctorId]
    );

    const { mothers = [], children = [] } = entityData || {};

    // Create submit function
    const submitAssessment = createSubmitAssessment(setShowForm, loadAssessments, onUpdate);

    // Handle form submission
    const handleSubmit = async () => {
        const assessmentData = {
            mother_id: selectedMother.id,
            assessment_type: 'mother_postnatal',
            assessor_id: ashaWorkerId || doctorId,
            assessor_role: userRole,
            ...motherAssessment
        };

        await submitAssessment(assessmentData, selectedMother, 'mother');
    };

    return (
        <ErrorBoundary>
            {loading && <div>Loading...</div>}
            {error && <div>Error: {error}</div>}
            {/ * Your component JSX * /}
        </ErrorBoundary>
    );
};
*/
