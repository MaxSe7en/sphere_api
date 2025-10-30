from fastapi import FastAPI
# from app.api.v1.endpoints import users
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import bills, users, states, ai, watchlist#, posts, auth
from app.db.session import SessionLocal
from app.api.v1.endpoints import ai


app = FastAPI(title="BillTracker API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# app = FastAPI(docs_url=None, redoc_url=None)  # disable docs in production
API_PREFIX = "/api/v1"
# Health check (no prefix, always accessible)

@app.get("/health", tags=["health"])
def health_check():
    try:
        # check db connectivity
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # lightweight query
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


# Users
app.include_router(users.router, prefix=f"{API_PREFIX}/users", tags=["Users"])

app.include_router(watchlist.router, prefix=f"{API_PREFIX}/users/me", tags=["Watchlist"])

# Bills
app.include_router(bills.router, prefix=f"{API_PREFIX}/bills", tags=["Bills"])

# States
app.include_router(states.router, prefix=f"{API_PREFIX}/states_overview_count", tags=["States"])

# AI summary
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])


@app.get("/")
async def root():
    return {"message": "BillTracker API is running!"}
    