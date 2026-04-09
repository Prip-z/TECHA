from app.core.security import hash_password
from app.db.session import SessionLocal
from app.model import StaffRole, StaffUser


DEFAULT_LOGIN = "superadmin"
DEFAULT_PASSWORD = "superadmin123"
DEFAULT_NAME = "Super Admin"


def main() -> None:
    session = SessionLocal()
    try:
        existing_super_admin = (
            session.query(StaffUser)
            .filter(StaffUser.role == StaffRole.super_admin)
            .first()
        )
        if existing_super_admin is not None:
            print(
                f"Super admin already exists: "
                f"id={existing_super_admin.id}, login={existing_super_admin.login}"
            )
            return

        existing_login = (
            session.query(StaffUser)
            .filter(StaffUser.login == DEFAULT_LOGIN)
            .first()
        )
        if existing_login is not None:
            print(
                f"Cannot create default super admin because login "
                f"'{DEFAULT_LOGIN}' is already occupied by id={existing_login.id}"
            )
            return

        staff = StaffUser(
            login=DEFAULT_LOGIN,
            name=DEFAULT_NAME,
            password_hash=hash_password(DEFAULT_PASSWORD),
            role=StaffRole.super_admin,
            is_active=True,
        )
        session.add(staff)
        session.commit()
        session.refresh(staff)
        print(
            f"Created super admin: id={staff.id}, login={staff.login}, "
            f"password={DEFAULT_PASSWORD}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
