// Auth Context for React Native — Self-contained, separate from web app
import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { Platform } from 'react-native';
import authService, { cacheUser, getCachedUser, updateActivity, supabase } from '../services/auth';

const AuthContext = createContext({});

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const userRef = useRef(null);

    // Initialize: load cached user, then verify with Supabase
    useEffect(() => {
        let mounted = true;

        (async () => {
            // 1. Quick load from cache
            const cached = await getCachedUser();
            if (cached && mounted) {
                setUser(cached);
                userRef.current = cached;
                setLoading(false);
            }

            // 2. On web, check for OAuth redirect hash in URL
            if (Platform.OS === 'web' && supabase) {
                try {
                    // Supabase will automatically detect the hash fragment
                    // and exchange it for a session if detectSessionInUrl is true
                    const { data: { session: hashSession }, error } = await supabase.auth.getSession();
                    if (hashSession && mounted) {
                        setSession(hashSession);
                        const freshUser = await authService.getCurrentUser();
                        if (freshUser && mounted) {
                            setUser(freshUser);
                            userRef.current = freshUser;
                            await cacheUser(freshUser);
                            await updateActivity();
                        }
                        // Clean up the URL hash so it looks clean
                        if (window.location.hash) {
                            window.history.replaceState(null, '', window.location.pathname);
                        }
                        setLoading(false);
                        return; // Skip the normal session check
                    }
                } catch (e) {
                    console.warn('OAuth hash check:', e);
                }
            }

            // 3. Verify with server
            try {
                const currentSession = await authService.getSession();
                if (mounted) setSession(currentSession);
                if (currentSession?.user) {
                    const freshUser = await authService.getCurrentUser();
                    if (freshUser && mounted) {
                        setUser(freshUser);
                        userRef.current = freshUser;
                        await cacheUser(freshUser);
                        await updateActivity();
                    }
                } else if (!cached && mounted) {
                    setUser(null);
                }
            } catch (e) {
                if (e.name !== 'AbortError') {
                    console.error('Auth init error:', e);
                }
            } finally {
                if (mounted) setLoading(false);
            }
        })();

        // Listen for auth state changes (sign in, sign out, token refresh)
        const subscription = authService.onAuthStateChange((event, newSession, newUser) => {
            if (!mounted) return;

            console.log(`[Mobile Auth] Event: ${event}`);

            if (event === 'SIGNED_OUT') {
                setSession(null);
                setUser(null);
                userRef.current = null;
                cacheUser(null);
                return;
            }
            if (event === 'TOKEN_REFRESHED') {
                setSession(newSession);
                return;
            }
            if (event === 'SIGNED_IN' && newSession && newUser) {
                setSession(newSession);
                setUser(newUser);
                userRef.current = newUser;
                cacheUser(newUser);
                updateActivity();
                setLoading(false);
            }
        });

        return () => {
            mounted = false;
            subscription?.unsubscribe?.();
        };
    }, []);

    const signUp = async (userData) => {
        try {
            setLoading(true);
            return await authService.signUp(userData);
        } finally {
            setLoading(false);
        }
    };

    const signIn = async (email, password) => {
        try {
            setLoading(true);
            const result = await authService.signIn(email, password);
            // Set user immediately — AppNavigator will switch to MainTabs
            setUser(result.user);
            setSession(result.session);
            await cacheUser(result.user);
            await updateActivity();
            return result;
        } finally {
            setLoading(false);
        }
    };

    const signInWithGoogle = async () => {
        try {
            setLoading(true);
            return await authService.signInWithGoogle();
            // After Google OAuth redirect, the onAuthStateChange handler
            // will fire SIGNED_IN event and set the user
        } catch (e) {
            setLoading(false);
            throw e;
        }
    };

    const signOut = async () => {
        setUser(null);
        setSession(null);
        userRef.current = null;
        await authService.signOut();
    };

    const updateProfile = async (updates) => {
        const result = await authService.updateProfile(updates);
        const updatedUser = await authService.getCurrentUser();
        setUser(updatedUser);
        await cacheUser(updatedUser);
        return result;
    };

    const hasRole = (allowedRoles) => authService.hasRole(user, allowedRoles);
    const isAdmin = () => hasRole(['ADMIN']);
    const isDoctor = () => hasRole(['DOCTOR', 'ADMIN']);
    const isAshaWorker = () => hasRole(['ASHA_WORKER', 'DOCTOR', 'ADMIN']);

    return (
        <AuthContext.Provider
            value={{
                user, session, loading,
                signUp, signIn, signInWithGoogle, signOut,
                updateProfile,
                hasRole, isAdmin, isDoctor, isAshaWorker,
                isAuthenticated: !!user,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
