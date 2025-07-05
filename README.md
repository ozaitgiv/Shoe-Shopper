# Shoe Shopper 🥿📐
Upload a top-down photo of your insole on a sheet of paper and get shoe recommendations tailored to your exact foot shape.

---

## Tech stack

| Layer      | Main tools / libraries                                    |
|------------|-----------------------------------------------------------|
| Front-end  | **Next.js 15** (App Router) · React 18 · TypeScript · Tailwind CSS |
| Back-end   | **Django 5** · Django REST Framework · django-cors-headers |
| Database   | **PostgreSQL** |
| Tooling    | ESLint · Prettier · Node 20 · Python 3.11 |

---

## Prerequisites

* **Python ≥ 3.10** (`python --version`)
* **Node ≥ 20** (`node -v`) & npm ≥ 10 (*`.nvmrc` with `20` is in the repo*)
* Optional: `git config --global core.autocrlf input` if you’re on macOS/Linux

---

## Local setup

### Back-end

```bash
# from repo root
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env    # add your API keys, etc.
python backend/manage.py migrate
python backend/manage.py runserver 8000
```

### Front-end (in a new terminal)
```bash
cd frontend
npm install
cp .env.example .env.local  # set NEXT_PUBLIC_API_URL if needed
npm run dev # http://localhost:3000
```

### Database 
```bash
# from Root directory
cd backend
pip install Django djangorestframework django-cors-headers psycopg2-binary Pillow
# or run requirements.txt
python manage.py migrate
python manage.py createsuperuser #Optional, for Admin Process
python manage.py runserver
```