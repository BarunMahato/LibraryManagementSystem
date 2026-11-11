# Library Management System

Library desk application with a Django REST Framework API and a React/Vite frontend.

## Backend

From `backend`, install `requirements.txt`, configure the PostgreSQL database in `config/settings.py`, then run:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

JWT routes are available at `/api/auth/login/`, `/api/auth/refresh/`, and `/api/auth/me/`. Create a librarian account through Django Admin or a management shell.

## Frontend

From `frontend`, install dependencies and run:

```powershell
npm install
npm run dev
```

The Vite development server uses `http://127.0.0.1:5173` and calls the API at `http://127.0.0.1:8000`.
