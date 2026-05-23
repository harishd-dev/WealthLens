/**
 * Global Zustand store.
 * Slices: auth, transactions, ui.
 * Keep business logic in hooks — store is for shared state only.
 */
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { supabase } from '@/lib/supabase'
import api from '@/lib/api'

export const useStore = create(
  persist(
    (set, get) => ({
      // ── Auth ─────────────────────────────────────────────────────────────
      user:    null,
      session: null,
      setUser:    (user)    => set({ user }),
      setSession: (session) => set({ session }),
      logout: async () => {
        await supabase.auth.signOut()
        set({ user: null, session: null, transactions: [], analytics: null })
      },

      // ── Transactions ──────────────────────────────────────────────────────
      transactions: [],
      txLoading:    false,
      txError:      null,

      fetchTransactions: async (params = {}) => {
        set({ txLoading: true, txError: null })
        try {
          const { data } = await api.get('/api/v1/transactions', { params })
          set({ transactions: data.data, txLoading: false })
          return data
        } catch (e) {
          set({ txError: e.message, txLoading: false })
        }
      },

      addTransaction: async (payload) => {
        const { data } = await api.post('/api/v1/transactions', payload)
        set((s) => ({ transactions: [data, ...s.transactions] }))
        return data
      },

      updateTransaction: async (id, payload) => {
        const { data } = await api.patch(`/api/v1/transactions/${id}`, payload)
        set((s) => ({
          transactions: s.transactions.map((t) => (t.id === id ? data : t)),
        }))
        return data
      },

      deleteTransaction: async (id) => {
        await api.delete(`/api/v1/transactions/${id}`)
        set((s) => ({
          transactions: s.transactions.filter((t) => t.id !== id),
        }))
      },

      // ── Analytics ─────────────────────────────────────────────────────────
      analytics:        null,
      analyticsLoading: false,

      fetchAnalytics: async (params = {}) => {
        set({ analyticsLoading: true })
        try {
          const { data } = await api.get('/api/v1/analytics/summary', { params })
          set({ analytics: data, analyticsLoading: false })
        } catch {
          set({ analyticsLoading: false })
        }
      },

      // ── UI ────────────────────────────────────────────────────────────────
      theme:    'dark',
      sideOpen: false,
      toggleTheme:  () => set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
      toggleSide:   () => set((s) => ({ sideOpen: !s.sideOpen })),
      closeSide:    () => set({ sideOpen: false }),
    }),
    {
      name: 'wealthlens-store',
      partialize: (s) => ({ user: s.user, theme: s.theme }),
    }
  )
)
