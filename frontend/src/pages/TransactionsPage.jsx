/**
 * TransactionsPage — full CRUD with search/filter/sort.
 * Wired to the FastAPI /api/v1/transactions endpoints.
 */
import { useEffect, useState } from 'react'
import { useTransactions } from '@/hooks/useTransactions'
import { Card, SectionHeader, Button, Input, Select, Spinner, EmptyState } from '@/components/shared/UI'
import { CATEGORIES, CATEGORY_NAMES, formatCurrency, formatDate } from '@/lib/constants'
import toast from 'react-hot-toast'

const INIT_FORM = {
  description: '', amount: '', type: 'debit', category: 'Food',
  date: new Date().toISOString().split('T')[0], notes: '',
}

function TxModal({ initial, onSave, onClose }) {
  const [form, setForm] = useState(initial || INIT_FORM)
  const [loading, setLoading] = useState(false)
  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.description || !form.amount) { toast.error('Description and amount are required.'); return }
    setLoading(true)
    try {
      await onSave({ ...form, amount: parseFloat(form.amount) })
      onClose()
    } catch {}
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4">
      <div className="bg-surface-700 border border-surface-600 rounded-[20px] p-8 w-full max-w-md animate-fade-in">
        <h3 className="font-display font-bold text-lg text-text-primary mb-6">
          {initial ? 'Edit Transaction' : 'Add Transaction'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Select label="Type" value={form.type} onChange={set('type')}>
              <option value="debit">💸 Expense</option>
              <option value="credit">💰 Income</option>
            </Select>
            <Select label="Category" value={form.category} onChange={set('category')}>
              {CATEGORY_NAMES.map(c => <option key={c} value={c}>{CATEGORIES[c].icon} {c}</option>)}
            </Select>
          </div>
          <Input label="Description" value={form.description} onChange={set('description')} placeholder="e.g. Swiggy dinner" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Amount (₹)" type="number" value={form.amount} onChange={set('amount')} placeholder="0" />
            <Input label="Date" type="date" value={form.date} onChange={set('date')} />
          </div>
          <div>
            <label className="block text-text-secondary text-xs font-medium mb-1.5">Notes (optional)</label>
            <textarea value={form.notes} onChange={set('notes')} rows={2} placeholder="Any additional notes…"
              className="w-full px-3.5 py-2.5 bg-surface-800 border border-surface-600 rounded-xl text-text-primary text-sm resize-none focus:outline-none focus:border-brand-green/60" />
          </div>
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? 'Saving…' : initial ? 'Save Changes' : 'Add Transaction'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function TransactionsPage() {
  const { transactions, txLoading, fetchTransactions, add, update, remove } = useTransactions()
  const [modal,   setModal]   = useState(null)   // null | 'add' | tx object
  const [search,  setSearch]  = useState('')
  const [fCat,    setFCat]    = useState('')
  const [fType,   setFType]   = useState('')
  const [sortKey, setSortKey] = useState('date')

  useEffect(() => {
    fetchTransactions({ size: 200, sort_by: sortKey, order: 'desc' })
  }, [sortKey])

  const filtered = transactions.filter(tx => {
    if (search && !tx.description?.toLowerCase().includes(search.toLowerCase())) return false
    if (fCat  && tx.category !== fCat)  return false
    if (fType && tx.type     !== fType) return false
    return true
  })

  const net = filtered.reduce((s, t) => t.type === 'credit' ? s + t.amount : s - t.amount, 0)

  const handleSave = async (form) => {
    if (modal === 'add') await add(form)
    else                 await update(modal.id, form)
  }

  return (
    <div className="animate-fade-in">
      <SectionHeader
        title="Transactions"
        subtitle={`${filtered.length} transactions · Net: ${net >= 0 ? '+' : ''}${formatCurrency(Math.abs(net))}`}
        action={<Button onClick={() => setModal('add')}>＋ Add Transaction</Button>}
      />

      {/* Filters */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <div className="relative flex-1 min-w-[180px]">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-sm">🔍</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search…"
            className="w-full pl-9 pr-3.5 py-2.5 bg-surface-700 border border-surface-600 rounded-xl text-text-primary text-sm placeholder:text-text-muted focus:outline-none focus:border-brand-green/60" />
        </div>
        <select value={fCat}    onChange={e => setFCat(e.target.value)}
          className="px-3.5 py-2.5 bg-surface-700 border border-surface-600 rounded-xl text-sm text-text-primary focus:outline-none cursor-pointer">
          <option value="">All Categories</option>
          {CATEGORY_NAMES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={fType}   onChange={e => setFType(e.target.value)}
          className="px-3.5 py-2.5 bg-surface-700 border border-surface-600 rounded-xl text-sm text-text-primary focus:outline-none cursor-pointer">
          <option value="">All Types</option>
          <option value="debit">Expense</option>
          <option value="credit">Income</option>
        </select>
        <select value={sortKey} onChange={e => setSortKey(e.target.value)}
          className="px-3.5 py-2.5 bg-surface-700 border border-surface-600 rounded-xl text-sm text-text-primary focus:outline-none cursor-pointer">
          <option value="date">Sort: Date</option>
          <option value="amount">Sort: Amount</option>
        </select>
      </div>

      {/* Table */}
      <Card className="p-0 overflow-hidden">
        <div className="grid grid-cols-[110px_1fr_110px_110px_100px_80px] px-5 py-3 border-b border-surface-800">
          {['Date','Description','Category','Type','Amount',''].map(h => (
            <span key={h} className="text-text-secondary text-[10px] font-semibold uppercase tracking-wider">{h}</span>
          ))}
        </div>

        {txLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : filtered.length === 0 ? (
          <EmptyState icon="💳" title="No transactions found"
            description="Try adjusting your filters or add a new transaction."
            action={<Button onClick={() => setModal('add')}>＋ Add Transaction</Button>} />
        ) : (
          filtered.map(tx => {
            const cat = CATEGORIES[tx.category] || CATEGORIES.Other
            return (
              <div key={tx.id}
                className="grid grid-cols-[110px_1fr_110px_110px_100px_80px] px-5 py-3.5 items-center border-b border-surface-900 hover:bg-surface-800 transition-colors">
                <span className="text-text-secondary text-xs">{formatDate(tx.date)}</span>
                <span className="text-text-primary text-sm font-medium truncate pr-3">{tx.description}</span>
                <span>
                  <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full"
                    style={{ background: cat.bg, color: cat.color }}>{cat.icon} {tx.category}</span>
                </span>
                <span>
                  <span className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full ${
                    tx.type === 'credit' ? 'bg-brand-green/10 text-brand-green' : 'bg-red-500/10 text-red-400'}`}>
                    {tx.type === 'credit' ? 'Income' : 'Expense'}
                  </span>
                </span>
                <span className={`font-mono text-sm font-medium ${tx.type === 'credit' ? 'text-brand-green' : 'text-red-400'}`}>
                  {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
                </span>
                <div className="flex gap-1.5">
                  <button onClick={() => setModal(tx)}
                    className="bg-blue-500/15 text-blue-400 rounded-lg p-1.5 text-sm hover:bg-blue-500/25 transition-colors">✎</button>
                  <button onClick={() => remove(tx.id)}
                    className="bg-red-500/15 text-red-400 rounded-lg p-1.5 text-sm hover:bg-red-500/25 transition-colors">🗑</button>
                </div>
              </div>
            )
          })
        )}
      </Card>

      {modal && (
        <TxModal
          initial={modal !== 'add' ? modal : null}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}
