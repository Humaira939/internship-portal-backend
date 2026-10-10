import getpass
import re

from pwdlib import PasswordHash

from src.admin.model import AdminModel
from src.utils.db import get_db

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"


def main():
    print("=== Create a SmartIntern admin account ===")
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (at least 8 characters): ")
    confirm = getpass.getpass("Confirm password: ")

    if len(name) < 2:
        print("Error: name must be at least 2 characters.")
        return
    if not re.match(EMAIL_PATTERN, email):
        print("Error: email is not valid.")
        return
    if len(password) < 8:
        print("Error: password must be at least 8 characters.")
        return
    if password != confirm:
        print("Error: passwords do not match.")
        return

    # get_db() is the same function FastAPI uses to open a database session
    source = get_db()
    db = next(source) if hasattr(source, "__next__") else source

    try:
        if db.query(AdminModel).filter(AdminModel.email == email).first():
            print("An admin with this email already exists. Nothing was changed.")
            return

        admin = AdminModel(
            name=name,
            email=email,
            password_hash=PasswordHash.recommended().hash(password),
        )
        db.add(admin)
        db.commit()
        print(f"Done. Admin account created for {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()