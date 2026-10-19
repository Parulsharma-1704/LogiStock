"""
create_admin.py — CLI script to create an initial admin user for LogiStock.

Prompts interactively for username and password in the terminal.
Password input is masked using getpass and hashed using Werkzeug.
"""

import getpass
import sys
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash
from db import users

def main():
    print("=" * 50)
    print("  LogiStock — Create Initial Admin User")
    print("=" * 50)

    if len(sys.argv) >= 3:
        username = sys.argv[1].strip()
        password = sys.argv[2]
    else:
        try:
            username = input("Enter admin username: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)

        if not username:
            print("Error: Username cannot be empty.")
            sys.exit(1)

        def read_pass(prompt):
            try:
                return getpass.getpass(prompt)
            except Exception:
                return input(prompt)

        try:
            password = read_pass("Enter admin password: ")
            password_confirm = read_pass("Confirm admin password: ")
        except (KeyboardInterrupt, EOFError):
            print("\nAborted.")
            sys.exit(1)

        if not password:
            print("Error: Password cannot be empty.")
            sys.exit(1)

        if password != password_confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)

    password_hash = generate_password_hash(password)

    user_doc = {
        "username": username,
        "password_hash": password_hash,
        "role": "admin",
        "created_at": datetime.now(timezone.utc)
    }

    try:
        users.insert_one(user_doc)
        print(f"\n[OK] Admin user '{username}' created successfully!")
    except DuplicateKeyError:
        print(f"\n[Error] User with username '{username}' already exists.")
        sys.exit(1)

if __name__ == "__main__":
    main()
