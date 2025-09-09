from fastapi import FastAPI
# from app.api.v1.endpoints import users
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import bills, users#, states, posts, auth

app = FastAPI(title="BillTracker API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# app = FastAPI(docs_url=None, redoc_url=None)#for production
pref = "/api/v1"
# Include routers
app.include_router(users.router, prefix=pref)
# app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(bills.router, prefix=f"{pref}/bills", tags=["bills"])
# app.include_router(states.router, prefix="/states", tags=["states"])
# app.include_router(posts.router, prefix="/posts", tags=["posts"])
app.include_router(users.router, prefix=f"{pref}/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "BillTracker API is running!"}