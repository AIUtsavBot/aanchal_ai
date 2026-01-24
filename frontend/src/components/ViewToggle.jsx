import React from 'react';
import './ViewToggle.css';

export const ViewToggle = ({ currentView, onViewChange }) => {
    return (
        <div className="view-toggle-compact">
            <button
                className={`toggle-btn-compact ${currentView === 'pregnancy' ? 'active' : ''}`}
                onClick={() => onViewChange('pregnancy')}
                title="Pregnancy Care (MatruRaksha)"
            >
                🤰 Pregnancy
            </button>
            <button
                className={`toggle-btn-compact ${currentView === 'postnatal' ? 'active' : ''}`}
                onClick={() => onViewChange('postnatal')}
                title="Postnatal & Child Care (SantanRaksha)"
            >
                🍼 Postnatal
            </button>
        </div>
    );
};
