# GroceryPi 🛒

A smart grocery list tracker designed to run on your **Raspberry Pi** as a local home server.

## Architecture

```
grocerypi/
├── backend/   — Python FastAPI REST API (JWT auth, SQLite, CRUD)
└── frontend/  — React 18 + Vite + Tailwind CSS v3
```

---

## Backend Setup

### Requirements
- Python 3.11+

### Install & Run

```bash
cd backend

# Copy env file and set your secret key
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Start the development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive API docs (Swagger UI) are at `http://localhost:8000/docs`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | *(required)* | Random secret for JWT signing |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` (7 days) | Token lifetime |
| `DATABASE_URL` | `sqlite:///./grocerypi.db` | Database connection string |

---

## Frontend Setup

### Requirements
- Node.js 18+

### Install & Run

```bash
cd frontend

# Install dependencies
npm install

# Start the development server (proxies /auth and /lists to backend)
npm run dev
```

The app will be available at `http://localhost:5173`.

### Build for Production

```bash
npm run build
# Output is in frontend/dist/
```

---

## Running on Raspberry Pi

1. Clone the repo on your Pi:
   ```bash
   git clone <your-repo-url> grocerypi
   ```

2. Start the backend:
   ```bash
   cd grocerypi/backend
   cp .env.example .env
   # Edit .env with a strong SECRET_KEY
   pip install -r requirements.txt
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. Build and serve the frontend:
   ```bash
   cd grocerypi/frontend
   npm install && npm run build
   # Serve with any static file server, e.g.:
   npx serve dist -p 3000
   ```

4. Access GroceryPi from any device on your home network at `http://<pi-ip>:3000`.

---

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login → JWT token |
| GET | `/auth/me` | Get current user |
| GET | `/lists/` | Get all lists |
| POST | `/lists/` | Create a list |
| GET | `/lists/{id}` | Get list + items |
| PUT | `/lists/{id}` | Update list |
| DELETE | `/lists/{id}` | Delete list |
| GET | `/lists/{id}/items` | Get items |
| POST | `/lists/{id}/items` | Add item |
| PUT | `/lists/{id}/items/{item_id}` | Update item |
| DELETE | `/lists/{id}/items/{item_id}` | Delete item |

---

## License

See [LICENSE](LICENSE).