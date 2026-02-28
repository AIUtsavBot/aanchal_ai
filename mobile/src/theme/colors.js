// Color system matching the web frontend
// Web uses: purple-600 primary, indigo-600 accent, pink-50/purple-50 gradients
export const colors = {
    light: {
        // Core palette — matches website
        primary: '#7C3AED',       // purple-600 (website primary)
        primaryDark: '#6D28D9',   // purple-700
        primaryLight: '#EDE9FE',  // purple-50
        accent: '#4F46E5',        // indigo-600 (website accent)
        accentLight: '#EEF2FF',   // indigo-50

        // Backgrounds — matches website gradient
        background: '#FAFAFA',
        backgroundGradientFrom: '#FDF2F8', // pink-50
        backgroundGradientTo: '#FAF5FF',   // purple-50
        surface: '#FFFFFF',
        surfaceElevated: '#F9FAFB',

        // Text hierarchy
        text: '#111827',          // gray-900
        textSecondary: '#4B5563', // gray-600
        textTertiary: '#9CA3AF',  // gray-400
        placeholder: '#6B7280',   // gray-500

        // Semantic
        success: '#10B981',
        successLight: '#D1FAE5',
        warning: '#F59E0B',
        warningLight: '#FEF3C7',
        error: '#EF4444',
        errorLight: '#FEE2E2',
        info: '#3B82F6',
        infoLight: '#DBEAFE',

        // Borders
        border: '#E5E7EB',       // gray-200
        divider: '#F3F4F6',      // gray-100

        // Navigation
        tabBar: '#FFFFFF',
        tabBarBorder: '#E5E7EB',
        cardShadow: '#000',
        statusBar: 'dark',
    },
    dark: {
        primary: '#A78BFA',
        primaryDark: '#7C3AED',
        primaryLight: '#2D1B69',
        accent: '#818CF8',
        accentLight: '#1E1B4B',

        background: '#0F172A',
        backgroundGradientFrom: '#0F172A',
        backgroundGradientTo: '#1E1B4B',
        surface: '#1E293B',
        surfaceElevated: '#334155',

        text: '#F1F5F9',
        textSecondary: '#94A3B8',
        textTertiary: '#64748B',
        placeholder: '#64748B',

        success: '#34D399',
        successLight: '#064E3B',
        warning: '#FBBF24',
        warningLight: '#78350F',
        error: '#F87171',
        errorLight: '#7F1D1D',
        info: '#60A5FA',
        infoLight: '#1E3A5F',

        border: '#334155',
        divider: '#1E293B',

        tabBar: '#1E293B',
        tabBarBorder: '#334155',
        cardShadow: '#000',
        statusBar: 'light',
    },
};
