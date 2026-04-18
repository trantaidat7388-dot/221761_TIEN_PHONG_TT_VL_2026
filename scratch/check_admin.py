from backend.app.database import SessionLocal
from backend.app import models

def check_admin():
    db = SessionLocal()
    try:
        admins = db.query(models.User).filter(models.User.role == "admin").all()
        print(f"Number of admins found: {len(admins)}")
        for admin in admins:
            print(f"ID: {admin.id}, Username: {admin.username}, Email: {admin.email}, Plan: {admin.plan_type}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin()
