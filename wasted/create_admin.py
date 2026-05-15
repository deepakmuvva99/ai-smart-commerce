import os
import sys

# Add the project root to the path so we can import the backend package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_backend.database import SessionLocal, engine
from core_backend import models, auth

def create_initial_admin():
    print("Initializing Database...")
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        admin_email = "admin@smartcommerce.com"
        existing_admin = db.query(models.User).filter(models.User.email == admin_email).first()
        
        hashed_password = auth.get_password_hash("admin123")
        
        if existing_admin:
            existing_admin.role = "admin"
            existing_admin.password_hash = hashed_password
            existing_admin.is_verified = True
            db.commit()
            print(f"Updated existing user {admin_email} to admin role with new password and verified status.")
        else:
            print(f"Creating new admin user: {admin_email}")
            db_admin = models.User(email=admin_email, password_hash=hashed_password, role="admin", is_verified=True)
            db.add(db_admin)
            db.commit()
        db.commit()
        print("Successfully created admin user!")
        print(f"Login: {admin_email}")
        print("Password: admin123")
        
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()
