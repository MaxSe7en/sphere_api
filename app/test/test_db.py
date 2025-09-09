from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("✅ Database connected successfully!")
        print(f"PostgreSQL version: {result.scalar()}")
except Exception as e:
    print(f"❌ Database connection failed: {e}")