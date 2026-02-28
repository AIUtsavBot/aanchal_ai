// Aanchal AI — Auth Service (React Native) — SELF-CONTAINED
// This auth service is completely separate from the web app.
// All login/session handling stays within the mobile app.
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform, Linking } from 'react-native';

const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

// Use a separate storage key prefix for mobile to avoid sharing with web app
const MOBILE_STORAGE_PREFIX = 'aanchal_mobile_';

// SecureStore adapter (native) / AsyncStorage fallback (web)
const MobileStorageAdapter = {
    getItem: async (key) => {
        const mobileKey = MOBILE_STORAGE_PREFIX + key;
        if (Platform.OS === 'web') {
            // On web, use localStorage with mobile-specific prefix
            try {
                return window.localStorage.getItem(mobileKey);
            } catch {
                return null;
            }
        }
        try {
            return await SecureStore.getItemAsync(mobileKey);
        } catch {
            return await AsyncStorage.getItem(mobileKey);
        }
    },
    setItem: async (key, value) => {
        const mobileKey = MOBILE_STORAGE_PREFIX + key;
        if (Platform.OS === 'web') {
            try {
                window.localStorage.setItem(mobileKey, value);
            } catch { }
            return;
        }
        try {
            await SecureStore.setItemAsync(mobileKey, value);
        } catch {
            await AsyncStorage.setItem(mobileKey, value);
        }
    },
    removeItem: async (key) => {
        const mobileKey = MOBILE_STORAGE_PREFIX + key;
        if (Platform.OS === 'web') {
            try {
                window.localStorage.removeItem(mobileKey);
            } catch { }
            return;
        }
        try {
            await SecureStore.deleteItemAsync(mobileKey);
        } catch {
            await AsyncStorage.removeItem(mobileKey);
        }
    },
};

let supabase;
if (SUPABASE_URL && SUPABASE_ANON_KEY) {
    supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
            storage: MobileStorageAdapter,
            autoRefreshToken: true,
            persistSession: true,
            detectSessionInUrl: Platform.OS === 'web', // detect hash fragment on web
            storageKey: 'aanchal-mobile-auth', // unique key to separate from website
        },
    });
} else {
    console.warn('⚠️ Missing Supabase credentials — auth will not work');
    supabase = null;
}

export { supabase };

// --- User Cache ---
const USER_CACHE_KEY = 'aanchal_mobile_user_cache';
const LAST_ACTIVITY_KEY = 'aanchal_mobile_last_activity';
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;

export async function cacheUser(user) {
    try {
        if (user) {
            await AsyncStorage.setItem(USER_CACHE_KEY, JSON.stringify({
                ...user,
                cachedAt: Date.now(),
            }));
        } else {
            await AsyncStorage.removeItem(USER_CACHE_KEY);
        }
    } catch (e) {
        console.error('Cache user error:', e);
    }
}

export async function getCachedUser() {
    try {
        const raw = await AsyncStorage.getItem(USER_CACHE_KEY);
        if (!raw) return null;
        const data = JSON.parse(raw);
        const lastActivity = await AsyncStorage.getItem(LAST_ACTIVITY_KEY);
        if (lastActivity && Date.now() - parseInt(lastActivity, 10) > IDLE_TIMEOUT_MS) {
            await AsyncStorage.removeItem(USER_CACHE_KEY);
            return null;
        }
        if (Date.now() - data.cachedAt > 24 * 60 * 60 * 1000) {
            await AsyncStorage.removeItem(USER_CACHE_KEY);
            return null;
        }
        return data;
    } catch {
        return null;
    }
}

export async function updateActivity() {
    await AsyncStorage.setItem(LAST_ACTIVITY_KEY, Date.now().toString());
}

// --- Auth Service ---
class AuthService {
    _composeUser(base, profile) {
        if (!base) return null;
        return {
            id: base.id,
            email: base.email,
            fullName: profile?.full_name || base.user_metadata?.full_name || '',
            role: profile?.role || base.user_metadata?.role || null,
            phone: profile?.phone || base.user_metadata?.phone || '',
            assignedArea: profile?.assigned_area || '',
            status: profile?.status || 'active',
            avatarUrl: base.user_metadata?.avatar_url || '',
            provider: base.app_metadata?.provider || 'email',
        };
    }

    async signUp({ email, password, fullName, role, phone, assignedArea }) {
        if (!supabase) throw new Error('Supabase not configured');
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: { full_name: fullName, role, phone, assigned_area: assignedArea },
            },
        });
        if (error) throw error;
        return { user: this._composeUser(data.user, null), session: data.session };
    }

    async signIn(email, password) {
        if (!supabase) throw new Error('Supabase not configured');
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        const user = await this.getCurrentUser();
        return { user, session: data.session };
    }

    /**
     * Google OAuth — In-App Flow
     * On web mode: opens OAuth in the same window with redirect back to current origin
     * On native: opens the system browser with deep link redirect
     */
    async signInWithGoogle() {
        if (!supabase) throw new Error('Supabase not configured');

        // Get the current app URL for redirect (NOT the Vercel website)
        let redirectUrl;
        if (Platform.OS === 'web') {
            // Web mode: redirect back to the current page (localhost or wherever the app is running)
            redirectUrl = window.location.origin;
        } else {
            // Native: use the deep link scheme
            redirectUrl = 'aanchalai://auth/callback';
        }

        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: redirectUrl,
                skipBrowserRedirect: Platform.OS !== 'web', // On native, handle manually
            },
        });
        if (error) throw error;

        // On native, open the URL in the system browser
        if (Platform.OS !== 'web' && data?.url) {
            await Linking.openURL(data.url);
        }

        return data;
    }

    async signOut() {
        if (!supabase) return;
        await cacheUser(null);
        const { error } = await supabase.auth.signOut();
        if (error) console.error('Sign out error:', error);
    }

    async getCurrentUser() {
        if (!supabase) return null;
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return null;
        const profile = await this.getUserProfile(user.id);
        return this._composeUser(user, profile);
    }

    async getUserProfile(userId) {
        if (!supabase) return null;
        try {
            const { data } = await supabase
                .from('user_profiles')
                .select('*')
                .eq('id', userId)
                .single();
            return data;
        } catch {
            // Fallback: try profiles table
            try {
                const { data } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', userId)
                    .single();
                return data;
            } catch {
                return null;
            }
        }
    }

    async getSession() {
        if (!supabase) return null;
        const { data: { session } } = await supabase.auth.getSession();
        return session;
    }

    async getToken() {
        if (!supabase) return null;
        try {
            const { data: { session } } = await supabase.auth.getSession();
            return session?.access_token || null;
        } catch {
            return null;
        }
    }

    async updateProfile(updates) {
        if (!supabase) throw new Error('Supabase not configured');
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error('Not authenticated');
        const { data, error } = await supabase
            .from('user_profiles')
            .update(updates)
            .eq('id', user.id)
            .select()
            .single();
        if (error) throw error;
        return data;
    }

    async resetPassword(email) {
        if (!supabase) throw new Error('Supabase not configured');
        const { error } = await supabase.auth.resetPasswordForEmail(email);
        if (error) throw error;
    }

    async updatePassword(newPassword) {
        if (!supabase) throw new Error('Supabase not configured');
        const { error } = await supabase.auth.updateUser({ password: newPassword });
        if (error) throw error;
    }

    hasRole(user, allowedRoles) {
        if (!user?.role) return false;
        return allowedRoles.includes(user.role);
    }

    onAuthStateChange(callback) {
        if (!supabase) return { unsubscribe: () => { } };
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, session) => {
                let user = null;
                if (session?.user) {
                    try {
                        user = await this.getCurrentUser();
                    } catch {
                        user = this._composeUser(session.user, null);
                    }
                }
                callback(event, session, user);
            }
        );
        return subscription;
    }
}

const authService = new AuthService();
export default authService;
