# Crestal - Rise to Your Level

A remote work platform that connects African youth to global dollar-paying jobs through skill-based simulation testing, not CVs.

## 🎯 What is Crestal?

Crestal is a platform where:
- **Workers** prove their skills through AI-generated simulations
- **Rank** is earned through performance, not credentials
- **Teams** form fluidly based on verified ability
- **Payment** is in dollars, distributed fairly

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **AI**: Google Gemini API

### Project Structure
```
/mnt/okcomputer/output/
├── app/                    # React Frontend
│   ├── src/
│   │   ├── screens/        # Main screens (Auth, Skills, Simulation, Results)
│   │   ├── components/     # Reusable components
│   │   ├── lib/            # API client
│   │   ├── App.tsx         # Main app with routing
│   │   └── index.css       # Design system
│   └── package.json
│
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── auth.py         # JWT & password utils
│   │   ├── database.py     # DB connection
│   │   ├── config.py       # Settings
│   │   └── routers/        # API endpoints
│   │       ├── auth.py     # Auth endpoints
│   │       ├── skills.py   # Skill headers & types
│   │       └── simulations.py  # Simulation engine
│   ├── database/
│   │   └── schema.sql      # PostgreSQL schema
│   └── requirements.txt
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 1. Database Setup

```bash
# Create database
createdb crestal

# Run schema
psql crestal < backend/database/schema.sql
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`
API docs at `http://localhost:8000/api/docs`

### 3. Frontend Setup

```bash
cd app

# Install dependencies
npm install

# Run dev server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 📋 Features Implemented

### Phase 1: Foundation ✅
- [x] PostgreSQL database schema
- [x] User authentication (register, login, OTP)
- [x] JWT token management
- [x] Skill headers & job types API
- [x] User skill selection

### Phase 2: Simulation Engine ✅
- [x] AI question generation with Gemini
- [x] Dynamic question pools (never repeats)
- [x] Session management with heartbeat
- [x] Answer submission & scoring
- [x] Mini-task submission
- [x] Results calculation

### Phase 3: Skill DNA ✅
- [x] Weakness tracking per concept
- [x] Visual skill strength chart
- [x] Retake weighting toward weak areas

### Phase 4: Anti-Cheating ✅
- [x] 30-minute session timeout
- [x] Cooldown enforcement (48h-7d)
- [x] Server-side only validation
- [x] Question regeneration on timeout

## 🎨 Design System

### Colors
- Background: `#0B0C10` (near-black)
- Card: `#15161A`
- Input: `#1E1F24`
- Primary: `#FF6B2B` (orange)
- Secondary: `#F5C842` (gold)
- Success: `#22C55E`
- Error: `#EF4444`

### Typography
- Font: Inter (headings), JetBrains Mono (numbers)
- H1: 32px, bold
- H2: 24px, semibold
- Body: 16px, regular

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/verify-otp` - Verify phone OTP
- `GET /api/auth/me` - Get current user

### Skills
- `GET /api/headers` - Get all skill headers with job types
- `POST /api/user/skills` - Add skills to user
- `GET /api/user/skills` - Get user's skills

### Simulations
- `POST /api/simulations/start` - Start simulation
- `POST /api/simulations/{id}/answer` - Submit answer
- `POST /api/simulations/{id}/mini-task` - Submit mini-task
- `GET /api/simulations/{id}/results` - Get results
- `POST /api/simulations/{id}/heartbeat` - Keep session alive

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest
```

### Test Question Generation
The AI generates unique questions every time. To test:
1. Start a simulation
2. Answer questions
3. Start another simulation
4. Questions will be different

## 📚 Concept Pools

The platform includes fully written concept pools for:

### Data & Operations
- Data Entry (8 concepts)
- Data Cleaning (12 concepts)
- Data Analysis (8 concepts)

### Business & Finance
- Market Research (7 concepts)
- Financial Analysis (7 concepts)
- Bookkeeping (7 concepts)
- Business Writing (7 concepts)

Each concept includes:
- Definition
- Question templates
- Nigerian contexts
- Common mistakes (for distractors)

## 🔒 Security

- Passwords hashed with bcrypt
- JWT tokens with expiration
- OTP verification for phone
- Session timeout protection
- Cooldown enforcement (server-side)
- SQL injection protection (SQLAlchemy)

## 🛣️ Roadmap

### Phase 5: Mini-Task Auto-Scoring
- [ ] Data cleaning CSV auto-scorer
- [ ] Data analysis visualization evaluator
- [ ] Business writing AI evaluator

### Phase 6: Job System
- [ ] Job posting (clients)
- [ ] Team formation
- [ ] Payment distribution

### Phase 7: Community
- [ ] Public pages (speculative work)
- [ ] Team channels
- [ ] Mentorship layer

## 🤝 Contributing

This is a proprietary platform. For development questions, contact the founding team.

## 📄 License

Copyright © 2024 Crestal. All rights reserved.

---

**Crestal** - Rise to your level. Your work is your only resume.
