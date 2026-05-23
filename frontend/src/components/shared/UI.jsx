/**
 * Shared UI primitives.
 * Import from here to keep visual consistency across all pages.
 */

export function Card({ children, className = '', ...props }) {
  return (
    <div
      className={`bg-surface-700 border border-surface-600 rounded-2xl p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function Button({
  children, variant = 'primary', size = 'md',
  className = '', disabled, ...props
}) {
  const base = 'inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-sans'
  const variants = {
    primary:  'bg-brand-gradient text-white hover:opacity-90 active:scale-[.98]',
    secondary:'bg-surface-600 text-text-primary hover:bg-surface-700',
    ghost:    'bg-transparent text-text-secondary hover:text-text-primary hover:bg-surface-700',
    danger:   'bg-red-500/10 text-red-400 hover:bg-red-500/20',
  }
  const sizes = {
    sm: 'text-xs px-3 py-2',
    md: 'text-sm px-4 py-2.5',
    lg: 'text-base px-6 py-3',
  }
  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}

export function Input({ label, error, className = '', ...props }) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-text-secondary text-xs font-medium mb-1.5">{label}</label>
      )}
      <input
        className={`w-full px-3.5 py-2.5 bg-surface-800 border border-surface-600 rounded-xl
          text-text-primary text-sm placeholder:text-text-muted
          focus:outline-none focus:border-brand-green/60 transition-colors ${className}`}
        {...props}
      />
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  )
}

export function Select({ label, error, className = '', children, ...props }) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-text-secondary text-xs font-medium mb-1.5">{label}</label>
      )}
      <select
        className={`w-full px-3.5 py-2.5 bg-surface-800 border border-surface-600 rounded-xl
          text-text-primary text-sm cursor-pointer
          focus:outline-none focus:border-brand-green/60 transition-colors ${className}`}
        {...props}
      >
        {children}
      </select>
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  )
}

export function Badge({ children, color = 'green' }) {
  const colors = {
    green:  'bg-brand-green/15 text-brand-green',
    red:    'bg-red-500/15 text-red-400',
    yellow: 'bg-yellow-500/15 text-yellow-400',
    blue:   'bg-blue-500/15 text-blue-400',
    purple: 'bg-purple-500/15 text-purple-400',
    gray:   'bg-gray-500/15 text-gray-400',
  }
  return (
    <span className={`inline-flex items-center text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${colors[color]}`}>
      {children}
    </span>
  )
}

export function Spinner({ size = 6 }) {
  return (
    <div className={`w-${size} h-${size} border-2 border-brand-green border-t-transparent rounded-full animate-spin`} />
  )
}

export function EmptyState({ icon = '📭', title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="font-display font-semibold text-lg text-text-primary mb-2">{title}</h3>
      {description && <p className="text-text-secondary text-sm max-w-xs mb-6">{description}</p>}
      {action}
    </div>
  )
}

export function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-7 gap-4">
      <div>
        <h2 className="font-display font-bold text-[22px] text-text-primary tracking-tight">{title}</h2>
        {subtitle && <p className="text-text-secondary text-sm mt-1">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}
