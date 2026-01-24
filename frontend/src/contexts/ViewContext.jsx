import React, { createContext, useContext, useState } from 'react';

const ViewContext = createContext();

export const useView = () => {
    const context = useContext(ViewContext);
    if (!context) {
        throw new Error('useView must be used within a ViewProvider');
    }
    return context;
};

export const ViewProvider = ({ children }) => {
    const [currentView, setCurrentView] = useState('pregnancy'); // 'pregnancy' or 'postnatal'

    return (
        <ViewContext.Provider value={{ currentView, setCurrentView }}>
            {children}
        </ViewContext.Provider>
    );
};
