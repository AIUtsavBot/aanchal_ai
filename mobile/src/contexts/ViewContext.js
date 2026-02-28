// View Context — MatruRaksha / SantanRaksha toggle
import React, { createContext, useContext, useState } from 'react';

const ViewContext = createContext({});

export const useView = () => useContext(ViewContext);

export const ViewProvider = ({ children }) => {
    const [currentView, setCurrentView] = useState('matruraksha'); // 'matruraksha' or 'santanraksha'

    return (
        <ViewContext.Provider value={{ currentView, setCurrentView }}>
            {children}
        </ViewContext.Provider>
    );
};
