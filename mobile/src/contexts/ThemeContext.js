// Theme Context — Light/Dark mode toggle
import React, { createContext, useContext, useState } from 'react';
import { colors } from '../theme';

const ThemeContext = createContext({});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
    const [isDark, setIsDark] = useState(false);
    const theme = isDark ? colors.dark : colors.light;

    return (
        <ThemeContext.Provider value={{ theme, isDark, toggleTheme: () => setIsDark((p) => !p) }}>
            {children}
        </ThemeContext.Provider>
    );
};
