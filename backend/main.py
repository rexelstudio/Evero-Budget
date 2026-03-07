import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes.auth_routes import router as auth_router
from routes.user_routes import router as user_router
from routes.transaction_routes import router as transaction_router
from routes.goal_routes import router as goal_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Evero Budget API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(transaction_router)
app.include_router(goal_router)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")


# SPA-style routing: serve HTML files
@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/{page}.html")
async def serve_page(page: str):
    file_path = os.path.join(frontend_dir, f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dir, "index.html"))


# Seed demo user on startup
@app.on_event("startup")
async def seed_demo_user():
    from database import SessionLocal
    from models import User
    from auth import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "demo@example.com").first()
        if not existing:
            demo = User(
                name="Demo User",
                email="demo@example.com",
                hashed_password=hash_password("demo1234"),
                monthly_goal=2000.0,
            )
            db.add(demo)
            db.commit()
            print("✅ Demo user created: demo@example.com / demo1234")
        else:
            print("✅ Demo user already exists")
    finally:
        db.close()
