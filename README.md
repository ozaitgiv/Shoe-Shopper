# Shoe-Shopper

A full-stack web application that helps users find the perfect shoe fit by analyzing foot measurements from uploaded images.

## 🏗️ Project Structure

```
Shoe-Shopper/
├── docs/                      # Project documentation
│   └── CLAUDE.md             # Comprehensive project guide
├── backend/                   # Django REST API
│   ├── core/                 # Main Django app
│   ├── scripts/              # Utility scripts
│   ├── dev-tools/            # Development and analysis tools  
│   ├── docs/                 # Backend documentation
│   ├── data/                 # Backup and sample data
│   └── media/                # User uploads (gitignored)
├── frontend/                  # Next.js client application
├── cv/                       # Computer vision utilities
└── docker-compose.yml        # Local development setup
```

## 🚀 Quick Start

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python scripts/load_shoes.py
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📚 Documentation

- **Main Guide**: [`docs/CLAUDE.md`](docs/CLAUDE.md) - Comprehensive project documentation
- **Testing**: [`backend/docs/README_TESTING.md`](backend/docs/README_TESTING.md) - Testing guide
- **API Docs**: [`backend/docs/`](backend/docs/) - Backend documentation

## 🛠️ Development Tools

- **Algorithm Analysis**: `backend/dev-tools/analyze_algorithm.py`
- **Test Runner**: `backend/scripts/run_all_tests.py`
- **Data Loading**: `backend/scripts/load_shoes.py`

## 🔧 Key Features

- **Computer Vision**: Foot measurement from uploaded images
- **4D Scoring Algorithm**: Length, width, area, perimeter analysis
- **Guest Support**: UUID-based guest sessions
- **Dynamic Categories**: Database-driven filters
- **Mobile Responsive**: Full mobile support

## 📱 Technology Stack

- **Backend**: Django 5.2.4 + Django REST Framework
- **Frontend**: Next.js 15.3.4 + React 19 + TypeScript
- **Computer Vision**: OpenCV + Roboflow
- **Database**: PostgreSQL (production) / SQLite3 (development)
- **Deployment**: Railway/Render

## 📄 License

This project is part of a shoe fitting solution development effort.