from app.db.session import engine
from app.models.bills import Bill
from app.models.users import Base

# Create tables
def test_table_creation():
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Table creation failed: {e}")

if __name__ == "__main__":
    test_table_creation()