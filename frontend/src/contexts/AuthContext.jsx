import { createContext, useContext, useState, useEffect, useRef } from 'react'
import authService, { cacheUser, getCachedUser, updateActivity } from '../services/auth'

const AuthContext = createContext({})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  // Initialize with cached user for instant page load (no loading spinner)
  const cachedUser = getCachedUser()
  const [user, setUser] = useState(cachedUser)
  const [session, setSession] = useState(null)
  // If we have a cached user, don't show loading - page loads instantly
  const [loading, setLoading] = useState(!cachedUser)
  const userRef = useRef(cachedUser)

  // Keep ref in sync with state and cache user
  useEffect(() => {
    userRef.current = user
    cacheUser(user)  // Cache to localStorage for instant reload
  }, [user])

  // Track user activity for idle timeout
  useEffect(() => {
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart']
    const handleActivity = () => updateActivity()

    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity, { passive: true })
    })

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity)
      })
    }
  }, [])

  useEffect(() => {
    let mounted = true
    let timeoutId = null

    // Verify session - MUST complete before loading is set to false
    const verifySession = async () => {
      // Set a timeout - if session check takes too long, stop loading anyway
      timeoutId = setTimeout(() => {
        if (mounted) {
          console.log('⏱️ Session verification timeout - using cached user if available')
          // On timeout, trust the cached user but still set loading to false
          setLoading(false)
        }
      }, 8000) // 8 second timeout for slow Supabase cold starts

      try {
        // Wait for Supabase to restore session from localStorage
        const currentSession = await authService.getSession()
        console.log('🔐 Session verify:', currentSession ? 'Valid' : 'None')

        if (!mounted) return

        clearTimeout(timeoutId)
        setSession(currentSession)

        // If no valid session, clear everything and stop loading
        if (!currentSession?.user) {
          console.log('❌ No valid session')
          if (cachedUser) {
            console.log('⏰ Clearing expired cached user')
            setUser(null)
            cacheUser(null)
          }
          setLoading(false)
          return
        }

        // Session is valid - now refresh user data
        console.log('✅ Session valid, refreshing user data...')
        try {
          const freshUser = await authService.getCurrentUser()
          console.log('👤 User verified:', freshUser?.email, 'Role:', freshUser?.role)
          if (mounted && freshUser) {
            setUser(freshUser)
            cacheUser(freshUser) // Update cache with fresh data
            updateActivity()
          }
        } catch (userError) {
          console.error('Error fetching user:', userError)
          // Keep cached user if available
          if (cachedUser) {
            console.log('📦 Using cached user as fallback')
          }
        }
      } catch (error) {
        console.error('Auth verification error:', error)
        clearTimeout(timeoutId)
        // On error, keep cached data if available but stop loading
      } finally {
        if (mounted) {
          console.log('✅ Auth loading complete')
          setLoading(false)
        }
      }
    }

    verifySession()

    // Listen to auth state changes
    const subscription = authService.onAuthStateChange((event, newSession, newUser) => {
      console.log('🔄 Auth state changed:', event)

      if (!mounted) return

      // Handle sign out
      if (event === 'SIGNED_OUT') {
        console.log('👋 User signed out')
        setSession(null)
        setUser(null)
        cacheUser(null)
        userRef.current = null
        setLoading(false)
        return
      }

      // For TOKEN_REFRESHED, just update session but keep user
      if (event === 'TOKEN_REFRESHED') {
        console.log('↻ Token refreshed')
        setSession(newSession)
        updateActivity()
        return
      }

      // Handle sign in or initial session
      if (newSession && newUser) {
        console.log('✅ User authenticated:', newUser?.email)
        setSession(newSession)
        setUser(newUser)
        userRef.current = newUser
        updateActivity()
      }

      setLoading(false)
    })

    return () => {
      mounted = false
      if (timeoutId) clearTimeout(timeoutId)
      subscription?.unsubscribe()
    }
  }, [])

  const signUp = async (userData) => {
    try {
      setLoading(true)
      const result = await authService.signUp(userData)
      return result
    } catch (error) {
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signIn = async (email, password) => {
    try {
      setLoading(true)
      const result = await authService.signIn(email, password)
      setUser(result.user)
      setSession(result.session)
      updateActivity()
      return result
    } catch (error) {
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signInWithGoogle = async () => {
    try {
      setLoading(true)
      const result = await authService.signInWithGoogle()
      return result
    } catch (error) {
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    try {
      // Clear state immediately - don't set loading to avoid spinner during signout
      setUser(null)
      setSession(null)
      cacheUser(null)
      userRef.current = null

      // Call signOut in background - state is already cleared
      await authService.signOut()
    } catch (error) {
      console.error('Sign out error:', error)
      // State is already cleared, just log the error
    }
  }

  const updateProfile = async (updates) => {
    try {
      const result = await authService.updateProfile(updates)
      // Refresh user data
      const updatedUser = await authService.getCurrentUser()
      setUser(updatedUser)
      return result
    } catch (error) {
      throw error
    }
  }

  const resetPassword = async (email) => {
    return await authService.resetPassword(email)
  }

  const updatePassword = async (newPassword) => {
    return await authService.updatePassword(newPassword)
  }

  const hasRole = (allowedRoles) => {
    return authService.hasRole(user, allowedRoles)
  }

  const isAdmin = () => hasRole(['ADMIN'])
  const isDoctor = () => hasRole(['DOCTOR', 'ADMIN'])
  const isAshaWorker = () => hasRole(['ASHA_WORKER', 'DOCTOR', 'ADMIN'])

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signInWithGoogle,
    signOut,
    updateProfile,
    resetPassword,
    updatePassword,
    hasRole,
    isAdmin,
    isDoctor,
    isAshaWorker,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthContext
