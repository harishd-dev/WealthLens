/**
 * Page components wired to the real FastAPI backend.
 * Each page calls the relevant API endpoint on mount.
 */

import { useEffect, useState } from 'react'
import { useStore }      from '@/store'
import { Card, SectionHeader, Spinner, EmptyState, Button, Select } from '@/components/shared/UI'
import { CATEGORIES, CHART_COLORS, formatCurrency, formatDate, formatCompact } from '@/lib/constants'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

// ── Recharts tooltip skin ─────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-700 border border-surface-600 rounded-xl px-4 py-2.5 text-xs font-sans">
      <p className="text-text-secondary mb-1.5">{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color }} className="font-medium">
          {p.name}: {formatCurrency(p.value)}
        </p>
      ))}
    </div>
  )
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ title, value, icon, iconColor, sub, trend, trendVal }) {
  return (
    <Card className="flex-1 min-w-[160px]">
      <div className="flex justify-between items-start mb-4">
        <span className="text-text-secondary text-sm font-medium">{title}</span>
        <div className="w-9 h-9 rounded-[10px] flex items-center justify-center text-lg"
          style={{ background: iconColor + '22' }}>{icon}</div>
      </div>
      <div className="font-mono text-[22px] font-medium text-text-primary tracking-tight">{value}</div>
      {sub && <div className="text-text-secondary text-xs mt-1.5">{sub}</div>}
      {trendVal && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${trend === 'up' ? 'text-brand-green' : 'text-red-400'}`}>
          {trend === 'up' ? '↑' : '↓'} {trendVal}
          <span className="text-text-muted font-normal ml-1">vs last month</span>
        </div>
      )}
    </Card>
  )
}

// ════════════════════════════════════════════════════════════
// DASHBOARD PAGE
// ════════════════════════════════════════════════════════════
export function DashboardPage() {
  const { analytics, fetchAnalytics, analyticsLoading, transactions, fetchTransactions, txLoading } = useStore()

  useEffect(() => {
    fetchAnalytics()
    fetchTransactions({ size: 10, sort_by: 'date', order: 'desc' })
  }, [])

  const income  = analytics?.total_income  ?? 0
  const expense = analytics?.total_expense ?? 0
  const savings = analytics?.net_savings   ?? 0
  const recent  = transactions.slice(0, 8)

  return (
    <div className="animate-fade-in">
      <SectionHeader title="Dashboard" subtitle="Your financial overview at a glance" />

      {/* Stats */}
      <div className="flex gap-4 mb-6 flex-wrap">
        <StatCard title="Total Income"   value={formatCurrency(income)}  icon="📈" iconColor="#10B981" trend="up" trendVal="Live" />
        <StatCard title="Total Expenses" value={formatCurrency(expense)} icon="📉" iconColor="#EF4444" />
        <StatCard title="Net Savings"    value={formatCurrency(savings)} icon="🐷" iconColor="#06B6D4"
          sub={income > 0 ? `${((savings / income) * 100).toFixed(1)}% savings rate` : ''} />
        <StatCard title="Transactions"   value={analytics ? transactions.length : '—'} icon="💳" iconColor="#A855F7" sub="Total recorded" />
      </div>

      {/* Charts row */}
      <div className="flex gap-4 mb-6 flex-wrap">
        <Card className="flex-[2] min-w-[280px]">
          <h3 className="font-display font-semibold text-base text-text-primary mb-5">Monthly Overview</h3>
          {analyticsLoading ? <div className="flex justify-center py-16"><Spinner /></div> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={analytics?.monthly ?? []}>
                <defs>
                  <linearGradient id="gI" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#10B981" stopOpacity={.3} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gE" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#EF4444" stopOpacity={.3} />
                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2D45" />
                <XAxis dataKey="month" tick={{ fill: '#7B92B2', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#7B92B2', fontSize: 11 }} axisLine={false} tickLine={false}
                  tickFormatter={v => '₹' + (v / 1000).toFixed(0) + 'k'} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="income"  stroke="#10B981" strokeWidth={2} fill="url(#gI)" name="Income" />
                <Area type="monotone" dataKey="expense" stroke="#EF4444" strokeWidth={2} fill="url(#gE)" name="Expense" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card className="flex-1 min-w-[220px]">
          <h3 className="font-display font-semibold text-base text-text-primary mb-4">By Category</h3>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={analytics?.by_category?.slice(0, 7) ?? []}
                cx="50%" cy="50%" innerRadius={38} outerRadius={62}
                dataKey="total" paddingAngle={2}>
                {(analytics?.by_category ?? []).slice(0, 7).map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={v => formatCurrency(v)}
                contentStyle={{ background: '#111827', border: '1px solid #1E2D45', borderRadius: 10 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-2">
            {(analytics?.by_category ?? []).slice(0, 5).map((c, i) => (
              <div key={c.category} className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-sm" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-text-secondary text-xs">{c.category}</span>
                </div>
                <span className="text-text-primary text-xs font-mono">{formatCurrency(c.total)}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent transactions */}
      <Card>
        <h3 className="font-display font-semibold text-base text-text-primary mb-5">Recent Transactions</h3>
        {txLoading ? <div className="flex justify-center py-8"><Spinner /></div> :
         recent.length === 0 ? <EmptyState icon="💳" title="No transactions yet" description="Add your first transaction or upload a bank statement." /> :
         recent.map(tx => {
           const cat = CATEGORIES[tx.category] || CATEGORIES.Other
           return (
             <div key={tx.id} className="flex items-center gap-3.5 py-3 border-b border-surface-800 last:border-0">
               <div className="w-9 h-9 rounded-[10px] flex items-center justify-center text-lg shrink-0"
                 style={{ background: cat.bg }}>{cat.icon}</div>
               <div className="flex-1 min-w-0">
                 <div className="text-text-primary text-sm font-medium truncate">{tx.description}</div>
                 <div className="text-text-secondary text-xs mt-0.5">{formatDate(tx.date)} · {tx.category}</div>
               </div>
               <div className={`font-mono text-sm font-medium shrink-0 ${tx.type === 'credit' ? 'text-brand-green' : 'text-red-400'}`}>
                 {tx.type === 'credit' ? '+' : '-'}{formatCurrency(tx.amount)}
               </div>
             </div>
           )
         })
        }
      </Card>
    </div>
  )
}

// ════════════════════════════════════════════════════════════
// ANALYTICS PAGE
// ════════════════════════════════════════════════════════════
export function AnalyticsPage() {
  const { analytics, fetchAnalytics, analyticsLoading } = useStore()

  useEffect(() => { fetchAnalytics() }, [])

  const expense    = analytics?.total_expense ?? 0
  const income     = analytics?.total_income  ?? 0
  const catData    = analytics?.by_category ?? []
  const monthlyData = analytics?.monthly ?? []

  return (
    <div className="animate-fade-in">
      <SectionHeader title="Analytics" subtitle="Deep insights into your spending behavior" />

      <Card className="mb-5">
        <h3 className="font-display font-semibold text-base text-text-primary mb-5">Monthly Income vs Expenses</h3>
        {analyticsLoading ? <div className="flex justify-center py-12"><Spinner /></div> : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={monthlyData} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2D45" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: '#7B92B2', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#7B92B2', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={v => '₹' + (v / 1000).toFixed(0) + 'k'} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ color: '#7B92B2', fontSize: 12 }} />
              <Bar dataKey="income"  fill="#10B981" name="Income"  radius={[4, 4, 0, 0]} />
              <Bar dataKey="expense" fill="#EF4444" name="Expense" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      <div className="flex gap-4 flex-wrap">
        <Card className="flex-1 min-w-[260px]">
          <h3 className="font-display font-semibold text-base text-text-primary mb-5">Category Breakdown</h3>
          {catData.map((c, i) => (
            <div key={c.category} className="mb-4">
              <div className="flex justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-base">{(CATEGORIES[c.category] || CATEGORIES.Other).icon}</span>
                  <span className="text-text-primary text-sm font-medium">{c.category}</span>
                </div>
                <div className="text-right">
                  <span className="text-text-primary text-sm font-mono">{formatCurrency(c.total)}</span>
                  <span className="text-text-muted text-xs ml-2">({c.percentage}%)</span>
                </div>
              </div>
              <div className="h-1.5 bg-surface-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${c.percentage}%`, background: CHART_COLORS[i % CHART_COLORS.length] }} />
              </div>
            </div>
          ))}
        </Card>

        <Card className="flex-1 min-w-[220px]">
          <h3 className="font-display font-semibold text-base text-text-primary mb-5">Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={catData} cx="50%" cy="50%" outerRadius={82} dataKey="total" paddingAngle={2}>
                {catData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={v => formatCurrency(v)}
                contentStyle={{ background: '#111827', border: '1px solid #1E2D45', borderRadius: 10 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-x-3 gap-y-2 mt-3">
            {catData.slice(0, 6).map((c, i) => (
              <div key={c.category} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm shrink-0" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                <span className="text-text-secondary text-xs">{c.category}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

// ════════════════════════════════════════════════════════════
// INSIGHTS PAGE
// ════════════════════════════════════════════════════════════
const TYPE_STYLE = {
  positive: { color: '#10B981', border: 'rgba(16,185,129,.2)',  badge: 'Great' },
  warning:  { color: '#F59E0B', border: 'rgba(245,158,11,.2)',  badge: 'Watch out' },
  tip:      { color: '#3B82F6', border: 'rgba(59,130,246,.2)',  badge: 'Tip' },
  alert:    { color: '#EF4444', border: 'rgba(239,68,68,.2)',   badge: 'Alert' },
}

export function InsightsPage() {
  const [insights, setInsights] = useState([])
  const [loading,  setLoading]  = useState(false)

  const generate = async () => {
    setLoading(true)
    try {
      const { data } = await api.post('/api/v1/insights')
      setInsights(data.insights)
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate insights.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in">
      <SectionHeader title="AI Insights ✨" subtitle="Powered by Claude — personalized financial intelligence" />

      {insights.length === 0 && !loading && (
        <>
          <Card className="text-center py-14 mb-5"
            style={{ backgroundImage: 'radial-gradient(ellipse at 50% 0%, rgba(16,185,129,.07) 0%, transparent 70%)' }}>
            <div className="text-6xl mb-5">🧠</div>
            <h3 className="font-display font-bold text-2xl text-text-primary tracking-tight mb-3">Smart Financial Analysis</h3>
            <p className="text-text-secondary text-sm max-w-md mx-auto mb-7 leading-relaxed">
              Claude analyzes your transactions to surface spending patterns, flag unusual activity,
              identify savings opportunities, and provide personalized recommendations.
            </p>
            <Button onClick={generate} size="lg">✨ Generate My Insights</Button>
          </Card>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
            {[
              ['🔍', 'Spending Patterns', 'Where your money goes each month'],
              ['📊', 'Trend Analysis',    'Compares spending across periods'],
              ['💡', 'Smart Suggestions', 'Actionable money-saving advice'],
              ['⚠️', 'Anomaly Detection', 'Spots unusual transactions'],
            ].map(([e, t, d]) => (
              <div key={t} className="bg-surface-800 border border-surface-600 rounded-2xl p-4">
                <div className="text-3xl mb-3">{e}</div>
                <div className="text-text-primary text-sm font-semibold mb-1.5">{t}</div>
                <div className="text-text-secondary text-xs leading-relaxed">{d}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {loading && (
        <Card className="text-center py-14">
          <div className="text-5xl mb-4 animate-pulse">✨</div>
          <h3 className="font-display font-semibold text-xl text-text-primary mb-2">Claude is analyzing your finances…</h3>
          <p className="text-text-secondary text-sm">Processing all your transactions across every category</p>
        </Card>
      )}

      {insights.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
            {insights.map((ins, i) => {
              const s = TYPE_STYLE[ins.type] || TYPE_STYLE.tip
              return (
                <div key={i} className="rounded-2xl p-5 border animate-slide-in"
                  style={{ background: s.color + '0d', borderColor: s.border, animationDelay: `${i * 0.08}s` }}>
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
                      style={{ background: s.color + '22' }}>{ins.emoji}</div>
                    <div>
                      <span className="inline-block text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wide mb-1.5"
                        style={{ background: s.color + '22', color: s.color }}>{s.badge}</span>
                      <h4 className="font-display font-semibold text-sm text-text-primary leading-snug">{ins.title}</h4>
                    </div>
                  </div>
                  <p className="text-[13px] text-text-secondary leading-relaxed">{ins.body}</p>
                </div>
              )
            })}
          </div>
          <Button variant="secondary" onClick={generate} disabled={loading}>↺ Regenerate</Button>
        </>
      )}
    </div>
  )
}
