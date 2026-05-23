/**
 * useTransactions — thin wrapper around the store for transaction CRUD.
 * Components import this instead of calling the store directly.
 */
import { useCallback } from 'react'
import { useStore } from '@/store'
import toast from 'react-hot-toast'

export function useTransactions() {
  const {
    transactions, txLoading, txError,
    fetchTransactions, addTransaction,
    updateTransaction, deleteTransaction,
  } = useStore()

  const add = useCallback(async (payload) => {
    try {
      const tx = await addTransaction(payload)
      toast.success('Transaction added!')
      return tx
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to add transaction.')
      throw e
    }
  }, [addTransaction])

  const update = useCallback(async (id, payload) => {
    try {
      const tx = await updateTransaction(id, payload)
      toast.success('Transaction updated!')
      return tx
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update transaction.')
      throw e
    }
  }, [updateTransaction])

  const remove = useCallback(async (id) => {
    try {
      await deleteTransaction(id)
      toast.success('Transaction deleted.')
    } catch (e) {
      toast.error('Failed to delete transaction.')
      throw e
    }
  }, [deleteTransaction])

  return {
    transactions, txLoading, txError,
    fetchTransactions, add, update, remove,
  }
}
