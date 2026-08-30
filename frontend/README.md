# Frontend (Phase 6)

React 18 + Vite + Tailwind. Nykaa listing chrome (`#FC2779` italic-caps **NYKAA**). Groq keys never belong here — talk to FastAPI only.

```bash
cd frontend
npm install
npm run dev
```

Dev server: [http://127.0.0.1:5173](http://127.0.0.1:5173) (proxies `/api` → `http://127.0.0.1:8000`).

Production: set `VITE_API_BASE_URL` to the Render origin (see `frontend/.env.example` and [docs/phase6.md](../docs/phase6.md)).
