import os

# We have to import the engine before importing models to ensure they bind
from core_backend.database import engine
from core_backend import models

def reset_database():
    print("Dropping all existing database tables (Wiping MVP Data)...")
    models.Base.metadata.drop_all(bind=engine)
    
    print("Creating new SQLAlchemy tables for Phase 1 Enterprise Schema...")
    models.Base.metadata.create_all(bind=engine)
    
    print("Database reset completed successfully.")

if __name__ == "__main__":
    reset_database()
