from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.routes import bookings, schedules, clients, chatbot
from db.supabase import get_db
from supabase import Client

app = FastAPI(
    title="Mirror Assistant Chatbot Backend",
    description="Backend for mental health professional schedule management",
    version="1.0.0"
)

# 1. CORS Configuration (Requirement for Frontend Team)
# This allows the frontend to communicate with your local/hosted API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

# 2. Register Routers
app.include_router(bookings.router, prefix=API_PREFIX)
app.include_router(schedules.router, prefix=API_PREFIX)
app.include_router(clients.router, prefix=API_PREFIX)
app.include_router(chatbot.router, prefix=API_PREFIX)

# 3. Health Check (Database Connection Test)
@app.get("/health", tags=["System"])
def health_check(db: Client = Depends(get_db)):
    """
    Checks if the backend and Supabase connection are healthy.
    """
    try:
        # Simple query to test Supabase connection
        db.table("clients").select("count", count="exact").limit(1).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "message": "Mirror Assistant Backend is fully operational"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "details": str(e)
        }

@app.get("/", tags=["System"])
def home():
    return {
        "message": "Welcome to Mirror Assistant API",
        "docs": "/docs",
        "version": "1.0.0"
    }