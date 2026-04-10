from app.db.session import SessionLocal
from app.model import StaffUser

def drop_admins():
    session = SessionLocal()
    try:
        num_deleted = session.query(StaffUser).delete()
        session.commit()
        print(f"deleted")
    except Exception as e:
        session.rollback()
        print(f"error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    drop_admins()
