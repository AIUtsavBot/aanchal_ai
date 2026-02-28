// Color system — Clinical Teal Healthtech Palette
// Primary: Teal (#0d9488), Accent: Pink (#ec4899)
export const colors = {
    light: {
        // Core palette — Clinical Teal
        primary: '#0d9488',       // teal-600
        primaryDark: '#0f766e',   // teal-700
        primaryLight: '#f0fdfa',  // teal-50
        accent: '#ec4899',        // pink-500 (maternal accent)
        accentLight: '#fdf2f8',   // pink-50

        // Backgrounds
        background: '#f8fafa',
        backgroundGradientFrom: '#f0fdfa', // teal-50
        backgroundGradientTo: '#fdf2f8',   // pink-50
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
        info: '#0EA5E9',
        infoLight: '#F0F9FF',

        // Borders
        border: '#E5E7EB',       // gray-200
        divider: '#F3F4F6',      // gray-100

        // Navigation
        tabBar: '#FFFFFF',
        tabBarBorder: '#E5E7EB',
        cardShadow: '#0d9488',
        statusBar: 'dark',
    },
    dark: {
        primary: '#2dd4bf',       // teal-400
        primaryDark: '#0d9488',   // teal-600
        primaryLight: '#042f2e',  // teal-950
        accent: '#f472b6',        // pink-400
        accentLight: '#500724',   // pink-950

        background: '#0F172A',
        backgroundGradientFrom: '#0F172A',
        backgroundGradientTo: '#042f2e',
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
        info: '#38bdf8',
        infoLight: '#0c4a6e',

        border: '#334155',
        divider: '#1E293B',

        tabBar: '#1E293B',
        tabBarBorder: '#334155',
        cardShadow: '#000',
        statusBar: 'light',
    },
};
