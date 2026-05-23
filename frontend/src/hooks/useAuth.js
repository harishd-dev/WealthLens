/**
 * useAuth — wraps Supabase auth lifecycle.
 * Listens to onAuthStateChange so session persists across tabs/refreshes.
 */
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useStore }  from '@/store'

export function useAuth() {
  const { user, setUser, setSession, logout } = useStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Hydrate on mount
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setSession(data.session)
        setUser(data.session.user)
      }
      setLoading(false)
    })

    // Subscribe to auth changes (login, logout, token refresh)
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => listener.subscription.unsubscribe()
  }, [])

  const signUp = async ({ email, password, name }) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name } },
    })
    if (error) throw error
    return data
  }

  const signIn = async ({ email, password }) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    return data
  }

  const resetPassword = async (email) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    if (error) throw error
  }

  return { user, loading, signUp, signIn, resetPassword, logout }
}
