# HebreKraft SaaS Sprint 3.0

Sprint 3.0 is the production-MVP foundation for HebreKraft AI Marketing Operations Platform.
It moves the project from a local LinkedIn automation script into a commercial SaaS architecture.

## What is included

- FastAPI backend
- Streamlit admin frontend
- SQLAlchemy database models
- User registration and login with JWT
- Multi-tenant organization workspace
- Brand profile and content preferences
- Topics to focus and topics to avoid
- Gemini-first content generation
- ChatGPT review/refinement
- LangGraph workflow orchestration
- LangChain prompt structure
- CrewAI agent role structure
- Branded image generation using PIL
- LinkedIn OAuth connection structure
- LinkedIn publishing API structure
- Scheduling-ready post model
- Docker and Docker Compose setup

## Important architecture decision

Sprint 3.0 uses LinkedIn OAuth/API for the commercial SaaS path.
It does not use Selenium as the main publishing method because Selenium is not reliable or compliant enough for a multi-tenant SaaS product.

## Project structure

```text
hebrekraft_saas_sprint_3/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── ai_engine.py
│   │   ├── linkedin_service.py
│   │   ├── scheduler.py
│   │   ├── security.py
│   │   └── routes/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── streamlit_app.py
│   ├── requirements.txt
│   └── Dockerfile
├── scripts/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Local setup without Docker

### 1. Copy environment file

```bash
cp .env.example .env
```

For Windows PowerShell:

```powershell
copy .env.example .env
```

Edit `.env` and add:

```text
SECRET_KEY=your-long-secret
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/linkedin/callback
FERNET_KEY=your-fernet-key
```

Generate `FERNET_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Start backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend docs:

```text
http://localhost:8000/docs
```

### 3. Start frontend

Open another terminal:

```bash
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Windows:

```powershell
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Frontend:

```text
http://localhost:8501
```

## Docker deployment locally

### 1. Copy env

```bash
cp .env.example .env
```

### 2. For Docker Compose with PostgreSQL, change DATABASE_URL in `.env`

```text
DATABASE_URL=postgresql+psycopg2://hebrekraft:hebrekraft@db:5432/hebrekraft
BACKEND_BASE_URL=http://backend:8000
```

For local browser OAuth callback, keep:

```text
FRONTEND_BASE_URL=http://localhost:8501
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/linkedin/callback
```

### 3. Build and run

```bash
docker compose up --build
```

## LinkedIn setup

1. Go to LinkedIn Developer Portal.
2. Create or open your app.
3. Add the product: **Share on LinkedIn**.
4. In Auth settings, add redirect URL:

```text
http://localhost:8000/api/linkedin/callback
```

5. Copy Client ID and Client Secret into `.env`.
6. In the app UI, open the LinkedIn tab and click **Connect LinkedIn**.

For company page publishing, the customer account must have the correct page/admin permission and LinkedIn may require additional product approval depending on the publishing scenario.

## Production deployment steps

Recommended MVP hosting stack:

- Backend: Render, Railway, Azure App Service, AWS ECS, or Google Cloud Run
- Frontend: Streamlit Community Cloud, Render, or same VM/container platform
- Database: Managed PostgreSQL
- Redis: Managed Redis
- Storage: S3 or Azure Blob later

### Production checklist

1. Use PostgreSQL, not SQLite.
2. Set a strong `SECRET_KEY`.
3. Generate and set `FERNET_KEY`.
4. Use HTTPS URLs for frontend and backend.
5. Update LinkedIn OAuth redirect URI to production URL:

```text
https://api.yourdomain.com/api/linkedin/callback
```

6. Set CORS to your actual frontend domain before public launch.
7. Store API keys in the hosting provider's secret manager.
8. Use a dedicated worker for scheduled publishing.
9. Add monitoring/logging before onboarding paying users.
10. Keep free beta users for 60–90 days before activating payments.

## Suggested beta scope

- 10–20 companies
- 60–90 days free beta
- LinkedIn only
- One brand profile per organization
- Daily AI-generated post
- Manual approval first, auto-publish later

## Next Sprint 4.0

- Payment plans
- Analytics dashboard
- Multi-platform publishing
- RAG brand memory
- Content calendar view
- Admin panel
- Team invitation flow
