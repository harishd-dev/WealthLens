# 💰 WealthLens — Smart Expense Tracker & Money Manager

A production-quality, AI-assisted financial management web app. Upload bank statements, track expenses, get smart auto-categorization powered by a rule engine + merchant learning, and receive personalized AI insights from Claude.

---

## ✨ Features

| Module | Details |
|---|---|
| 🔐 **Authentication** | Supabase Auth (signup, login, forgot password, session persistence) |
| 📊 **Dashboard** | Income, expenses, savings, monthly trend charts, recent transactions |
| 💳 **Transactions** | Add / edit / delete income & expenses with 9 categories |
| 📤 **Upload** | CSV & PDF bank statement parsing with two-step import flow |
| 🧠 **Smart Categorization** | Layer 1: 60+ built-in rules · Layer 2: merchant learning |
| 📈 **Analytics** | Monthly bar chart, category pie chart, breakdown with % bars |
| ✨ **AI Insights** | Claude-generated, data-driven spending insights |
| 🌙 **Dark Mode** | Dark-first design, light-mode ready via Tailwind `dark:` classes |
| 📱 **Responsive** | Mobile-first layout with collapsible sidebar |

---

## 🗂 Project Structure

```
smart-expense-tracker/
├── backend/
│   ├── main.py                        # FastAPI app entry
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── core/
│       │   ├── config.py              # pydantic-settings
│       │   └── security.py            # JWT + auth dependency
│       ├── db/
│       │   └── supabase.py            # Supabase client singleton
│       ├── schemas/
│       │   └── schemas.py             # All Pydantic models
│       ├── services/
│       │   ├── categorization.py      # Rule engine + merchant learning
│       │   ├── parser.py              # CSV + PDF parser
│       │   └── insights.py            # Claude AI insights
│       └── api/routes/
│           ├── auth.py
│           ├── transactions.py
│           ├── upload.py
│           ├── analytics.py
│           ├── insights.py
│           └── merchants.py
│
├── frontend/
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── App.jsx                    # Router + auth guard
│       ├── lib/
│       │   ├── supabase.js            # Supabase client
│       │   ├── api.js                 # Axios + auth interceptor
│       │   └── constants.js           # Categories, formatters, rules
│       ├── store/
│       │   └── index.js               # Zustand global store
│       ├── hooks/
│       │   ├── useAuth.js
│       │   └── useTransactions.js
│       ├── components/shared/
│       │   ├── Layout.jsx             # Sidebar + topbar
│       │   └── UI.jsx                 # Card, Button, Input, Badge…
│       └── pages/
│           ├── LoginPage.jsx
│           ├── AuthPages.jsx          # Signup + Forgot
│           └── DashboardAnalyticsInsights.jsx
│
└── docs/
    └── supabase_setup.sql             # Full schema + RLS policies
```

---

## 🚀 Quick Setup

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Supabase account | free tier is fine |
| Anthropic API key | console.anthropic.com |

---

### Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Note your **Project URL** and **API keys** from:
   `Project Settings → API`
3. Open **SQL Editor → New Query**
4. Paste and run `docs/supabase_setup.sql`
5. Verify tables `transactions` and `merchant_mappings` were created

---

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in SUPABASE_URL, SUPABASE_ANON_KEY,
#              SUPABASE_SERVICE_ROLE_KEY, ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

> API docs available at `http://localhost:8000/docs`

---

### Step 3 — Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local — fill in VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY

# Start dev server
npm run dev
```

> App available at `http://localhost:5173`

---

## 🔌 API Reference

All endpoints require `Authorization: Bearer <supabase_token>` except auth routes.

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Sign in |
| POST | `/api/v1/auth/forgot-password` | Send reset email |
| POST | `/api/v1/auth/logout` | Sign out |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/transactions` | List (paginated, filterable) |
| POST | `/api/v1/transactions` | Create |
| GET | `/api/v1/transactions/{id}` | Get single |
| PATCH | `/api/v1/transactions/{id}` | Update |
| DELETE | `/api/v1/transactions/{id}` | Delete |

**Query params:** `page`, `size`, `category`, `type`, `search`, `sort_by`, `order`

### Upload
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/upload/preview` | Parse file → preview + categorize |
| POST | `/api/v1/upload/confirm` | Save transactions + merchant mappings |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/analytics/summary` | Full aggregated summary |
| GET | `/api/v1/analytics/history` | Daily expense history |

### Insights & Merchants
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/insights` | Generate Claude AI insights |
| GET | `/api/v1/merchants` | List learned mappings |
| POST | `/api/v1/merchants` | Add mapping |
| DELETE | `/api/v1/merchants/{id}` | Remove mapping |

---

## 📥 CSV Upload Format

```csv
Date,Description,Amount,Type
2026-05-15,Swiggy Order,380,debit
2026-05-10,Salary Credit,85000,credit
2026-05-08,Amazon Purchase,2499,debit
```

**Supported date formats:** `YYYY-MM-DD`, `DD-MM-YYYY`, `DD/MM/YYYY`, `DD Mon YYYY`

---

## 🧠 Categorization Logic

```
Upload / Add Transaction
        │
        ▼
Layer 2: User merchant mappings
  (e.g. "pizza corner" → Food learned from last upload)
        │ no match
        ▼
Layer 1: Built-in rules (60+ keywords)
  swiggy→Food · uber→Travel · amazon→Shopping
  netflix→Entertainment · airtel→Bills · groww→Investment …
        │ no match
        ▼
→ Flag as needs_review → ask user → save to merchant_mappings
  (auto-applied on all future uploads)
```

---

## 🔒 Security

- **RLS**: Every Supabase table has Row Level Security — users can only access their own data
- **Service role key**: Only used server-side (never exposed to browser)
- **JWT validation**: Every protected route validates the Supabase JWT
- **File limits**: 10 MB max upload size, CSV/PDF only
- **CORS**: Configured to your frontend origin only

---

## 🚢 Production Deployment

### Backend (Render / Railway / Fly.io)
```bash
# Set env vars in your provider's dashboard
# Start command:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel / Netlify)
```bash
npm run build
# dist/ folder → deploy to Vercel/Netlify
# Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in dashboard
# Set VITE_API_BASE_URL to your deployed backend URL
```

---

## 🛣 Roadmap

- [ ] Voice assistant integration (API is already structured for it)
- [ ] Budget goals & alerts
- [ ] Multi-currency support
- [ ] WhatsApp / Telegram bot
- [ ] Export to Excel / PDF reports
- [ ] Recurring transaction detection
- [ ] UPI / bank API integration

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 · Vite · TailwindCSS · Recharts · Zustand |
| Backend | Python 3.11 · FastAPI · Pydantic v2 · Uvicorn |
| Database | Supabase PostgreSQL |
| Auth | Supabase Auth |
| AI | Anthropic Claude (claude-sonnet-4) |
| File Parsing | pandas · pdfplumber |
| HTTP Client | Axios (frontend) · httpx (backend) |

---

## 📄 License

MIT — free to use, modify and deploy.
