import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

/**
 * Top-level ErrorBoundary — catches any crash and shows a
 * readable error instead of a blank white page.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error) {
    return { error }
  }
  componentDidCatch(error, info) {
    console.error('[WealthLens] Uncaught error:', error, info)
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh', background: '#060A12', color: '#E8EDF5',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          fontFamily: 'DM Sans, sans-serif', padding: 24,
        }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>
            Something went wrong
          </h1>
          <div style={{
            background: '#111827', border: '1px solid #1E2D45',
            borderRadius: 12, padding: '16px 20px',
            maxWidth: 560, width: '100%', marginBottom: 20,
          }}>
            <code style={{ color: '#EF4444', fontSize: 13, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {this.state.error.message}
            </code>
          </div>
          <p style={{ color: '#7B92B2', fontSize: 14, marginBottom: 8 }}>
            Common fixes:
          </p>
          <ul style={{ color: '#7B92B2', fontSize: 13, lineHeight: 2, listStyle: 'disc', paddingLeft: 20 }}>
            <li>Copy <code style={{color:'#10B981'}}>frontend/.env.example</code> → <code style={{color:'#10B981'}}>frontend/.env.local</code></li>
            <li>Set <code style={{color:'#10B981'}}>VITE_SUPABASE_URL</code> and <code style={{color:'#10B981'}}>VITE_SUPABASE_ANON_KEY</code></li>
            <li>Restart the dev server: <code style={{color:'#10B981'}}>npm run dev</code></li>
          </ul>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: 20, padding: '10px 24px',
              background: 'linear-gradient(135deg,#10B981,#06B6D4)',
              border: 'none', borderRadius: 10, color: 'white',
              cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
)