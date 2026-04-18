from backend.app.database import SessionLocal
from backend.app import models, auth
import os

def check_admin_password():
    # Load env variables manually just in case
    admin_email = "admin@word2latex.local"
    admin_password = "Admin@123456"
    
    db = SessionLocal()
    try:
        admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin:
            print("Admin user not found in database.")
            return

        is_correct = auth.xac_minh_mat_khau(admin_password, admin.hashed_password)
        print(f"Password '{admin_password}' is {'CORRECT' if is_correct else 'INCORRECT'} for user {admin_email}")
        
        if not is_correct:
            print("Resetting admin password to 'Admin@123456'...")
            admin.hashed_password = auth.bam_mat_khau(admin_password)
            db.commit()
            print("Admin password reset successfully.")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_password()
