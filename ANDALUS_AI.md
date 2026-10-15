# Andalus AI Engine
## Implemented
- Natural-language tool selection with Gemini Flash.
- FastAPI service: `GET /health`, `GET /tools`, `POST /chat`.
- Allow-listed Supabase REST adapter for student lookup, attendance, grades, guardian details and absentees.
- Persistent task queue adapter and SQL migration.
- Confirmation gate for mutating tools.
- WhatsApp explicitly reports not-connected until a real provider adapter is implemented; it never claims delivery.

## Setup
1. Python 3.11+; run `pip install -r requirements.txt`.
2. Set server environment variables (never commit secrets): `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. Optional: `ANDALUS_AI_ADMIN_TOKEN`.
3. Apply `migrations/001_andalus_ai_tasks.sql` to the academy Supabase project.
4. Start: `uvicorn andalus_ai.api:app --host 0.0.0.0 --port 8000`.
5. Open `/docs` for interactive API testing.

## Security and deployment
- Personal-data endpoints must be restricted to authenticated, authorized academy staff.
- Never put the service-role key in a website, Android app, or public repository.
- Task persistence is implemented; a production worker/scheduler and WhatsApp provider still need deployment/configuration before scheduled actions run.
- Production confirmations must be bound to the authenticated admin/session, not just a client-supplied boolean.
