// Aanchal AI — Mobile App Entry Point
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from './src/contexts/AuthContext';
import { ThemeProvider } from './src/contexts/ThemeContext';
import { ViewProvider } from './src/contexts/ViewContext';
import AppNavigator from './src/navigation/AppNavigator';
import './src/i18n';

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <AuthProvider>
          <ViewProvider>
            <AppNavigator />
          </ViewProvider>
        </AuthProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
