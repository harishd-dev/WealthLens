/**
 * UploadPage — Two-step CSV/PDF import with merchant learning UI.
 * Step 1: POST /api/v1/upload/preview → show parsed transactions
 * Step 2: User assigns unknown categories → POST /api/v1/upload/confirm
 */
import { useState, useRef } from 'react'
import { Card, SectionHeader, Button, Spinner } from '@/components/shared/UI'
import { CATEGORIES, CATEGORY_NAMES, formatCurrency, formatDate } from '@/lib/constants'
import api from '@/lib/api'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const [step,    setStep]    = useState('idle')  // idle | parsing | review | done
  const [preview, setPreview] = useState(null)
  const [assign,  setAssign]  = useState({})
  const [drag,    setDrag]    = useState(false)
  const fileRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    setStep('parsing')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const { data } = await api.post('/api/v1/upload/preview', fd,
        { headers: { 'Content-Type': 'multipart/form-data' } })
      setPreview(data)
      setStep('review')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to parse file.')
      setStep('idle')
    }
  }

  const handleConfirm = async () => {
    const transactions = preview.transactions.map(tx => ({
      description: tx.description,
      amount:      tx.amount,
      type:        tx.type,
      category:    assign[tx.temp_id] || tx.category || 'Other',
      date:        tx.date,
    }))
    const saveMappings = Object.entries(assign).map(([_, cat]) => ({ category: cat }))
    try {
      const { data } = await api.post('/api/v1/upload/confirm', { transactions, save_mappings: saveMappings })
      toast.success(`✅ Imported ${data.imported} transactions!`)
      setStep('done')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Import failed.')
    }
  }

  return (
    <div className="animate-fade-in">
      <SectionHeader title="Upload Statement" subtitle="Import CSV or PDF bank statements with smart auto-categorization" />

      {step === 'idle' && (
        <>
          <div
            onDragOver={e => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={e => { e.preventDefault(); setDrag(false); handleFile(e.dataTransfer.files[0]) }}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-[20px] p-14 text-center cursor-pointer transition-all duration-200 ${
              drag ? 'border-brand-green bg-brand-green/5' : 'border-surface-600 bg-surface-700 hover:border-brand-green/50'
            }`}
          >
            <div className="text-5xl mb-4">☁️</div>
            <h3 className="font-display font-semibold text-lg text-text-primary mb-2">Drop your bank statement here</h3>
            <p className="text-text-secondary text-sm mb-5">or click to browse files</p>
            <div className="flex gap-2 justify-center">
              {['.CSV', '.PDF'].map(f => (
                <span key={f} className="bg-surface-600 text-text-secondary text-xs px-3 py-1 rounded-full font-medium">{f}</span>
              ))}
            </div>
            <input ref={fileRef} type="file" accept=".csv,.pdf" className="hidden"
              onChange={e => handleFile(e.target.files[0])} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5">
            <div className="bg-brand-green/5 border border-brand-green/20 rounded-2xl p-4">
              <div className="text-brand-green text-xs font-bold mb-1.5">🧠 Layer 1: Rule Engine</div>
              <div className="text-text-secondary text-xs leading-relaxed">Matches 60+ merchant keywords automatically — Swiggy→Food, Uber→Travel, Zerodha→Investment and more.</div>
            </div>
            <div className="bg-brand-cyan/5 border border-brand-cyan/20 rounded-2xl p-4" style={{borderColor:'rgba(6,182,212,.2)',background:'rgba(6,182,212,.05)'}}>
              <div className="text-[#06B6D4] text-xs font-bold mb-1.5">🎓 Layer 2: Learning</div>
              <div className="text-text-secondary text-xs leading-relaxed">Unknown merchants get classified by you, saved to the database, and auto-applied to all future uploads.</div>
            </div>
          </div>
        </>
      )}

      {step === 'parsing' && (
        <Card className="text-center py-14">
          <Spinner size={10} />
          <h3 className="font-display font-semibold text-lg text-text-primary mt-5 mb-2">Parsing statement…</h3>
          <p className="text-text-secondary text-sm">Extracting transactions and applying smart categorization</p>
        </Card>
      )}

      {step === 'review' && preview && (
        <>
          {/* Summary bar */}
          <div className="flex gap-3 mb-5 flex-wrap">
            {[
              { label: 'Total Found', val: preview.total, color: '#E8EDF5' },
              { label: 'Auto-Categorized', val: preview.auto_categorized, color: '#10B981' },
              { label: 'Need Review', val: preview.needs_review, color: '#F59E0B' },
            ].map(s => (
              <div key={s.label} className="bg-surface-700 border border-surface-600 rounded-xl px-5 py-3 flex-1 min-w-[120px]">
                <div className="font-mono text-xl font-medium" style={{color:s.color}}>{s.val}</div>
                <div className="text-text-secondary text-xs mt-0.5">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Unknown merchants */}
          {preview.needs_review > 0 && (
            <Card className="mb-5 border border-yellow-500/20 bg-yellow-500/5">
              <h4 className="font-display font-semibold text-sm text-text-primary mb-3">
                🏷 {preview.needs_review} merchant{preview.needs_review !== 1 ? 's' : ''} need categorization
              </h4>
              <p className="text-text-secondary text-xs mb-4">These will be saved and auto-applied to future uploads.</p>
              {preview.transactions.filter(tx => tx.needs_review).map(tx => (
                <div key={tx.temp_id} className="flex items-center gap-3 mb-3 bg-surface-800 rounded-xl p-3 flex-wrap">
                  <div className="flex-1 min-w-[160px]">
                    <div className="text-text-primary text-sm font-medium">{tx.description}</div>
                    <div className={`text-xs font-mono mt-0.5 ${tx.type === 'credit' ? 'text-brand-green' : 'text-red-400'}`}>
                      {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
                    </div>
                  </div>
                  <select value={assign[tx.temp_id] || ''} onChange={e => setAssign(a => ({...a,[tx.temp_id]:e.target.value}))}
                    className="px-3 py-2 bg-surface-700 border border-surface-600 rounded-lg text-xs text-text-primary focus:outline-none cursor-pointer">
                    <option value="">Select category…</option>
                    {CATEGORY_NAMES.map(c => <option key={c} value={c}>{CATEGORIES[c].icon} {c}</option>)}
                  </select>
                  {assign[tx.temp_id] && <span className="text-brand-green text-xs font-medium">📚 Saved!</span>}
                </div>
              ))}
            </Card>
          )}

          {/* Preview list */}
          <Card className="mb-5">
            <h4 className="font-display font-semibold text-sm text-text-primary mb-4">
              ✅ {preview.total} transactions ready to import
            </h4>
            {preview.transactions.slice(0, 8).map(tx => {
              const cat = CATEGORIES[assign[tx.temp_id] || tx.category || 'Other'] || CATEGORIES.Other
              return (
                <div key={tx.temp_id} className="flex items-center gap-3 py-2.5 border-b border-surface-800 last:border-0">
                  <span className="text-lg shrink-0">{cat.icon}</span>
                  <div className="flex-1 min-w-0 text-text-primary text-sm truncate">{tx.description}</div>
                  <span className="text-[11px] px-2 py-0.5 rounded-full shrink-0"
                    style={{background:cat.bg,color:cat.color}}>{assign[tx.temp_id] || tx.category || 'Other'}</span>
                  <span className={`font-mono text-xs font-medium shrink-0 ${tx.type==='credit'?'text-brand-green':'text-red-400'}`}>
                    {tx.type==='credit'?'+':'-'}{formatCurrency(tx.amount)}
                  </span>
                </div>
              )
            })}
            {preview.total > 8 && <p className="text-text-secondary text-xs mt-3">+{preview.total - 8} more transactions…</p>}
          </Card>

          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => { setStep('idle'); setPreview(null) }}>Cancel</Button>
            <Button onClick={handleConfirm}>Import {preview.total} Transactions →</Button>
          </div>
        </>
      )}

      {step === 'done' && (
        <Card className="text-center py-14 border border-brand-green/30 bg-brand-green/5">
          <div className="text-5xl mb-4">✅</div>
          <h3 className="font-display font-bold text-xl text-text-primary mb-2">Import complete!</h3>
          <p className="text-text-secondary text-sm mb-6">Transactions imported and merchant mappings saved.</p>
          <Button onClick={() => { setStep('idle'); setPreview(null); setAssign({}) }}>Upload Another</Button>
        </Card>
      )}
    </div>
  )
}
