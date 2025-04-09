import os
import sys
from app import app, db
from models import User

def make_admin(email_or_username):
    """Make a user an admin by email or username"""
    # Try to find by email
    user = User.query.filter_by(email=email_or_username).first()
    
    # If not found by email, try username
    if not user:
        user = User.query.filter_by(username=email_or_username).first()
    
    # If user found, make them admin
    if user:
        if user.is_admin:
            print(f"User {user.username} ({user.email}) is already an admin.")
        else:
            user.is_admin = True
            db.session.commit()
            print(f"User {user.username} ({user.email}) is now an admin.")
    else:
        print(f"User with email or username '{email_or_username}' not found.")

def list_admins():
    """List all admin users"""
    admins = User.query.filter_by(is_admin=True).all()
    if admins:
        print("Admin users:")
        for admin in admins:
            print(f"- {admin.username} ({admin.email})")
    else:
        print("No admin users found.")

def main():
    with app.app_context():
        if len(sys.argv) < 2:
            print("Usage: python make_admins.py [email_or_username]")
            print("To list all admins: python make_admins.py --list")
            return
        
        if sys.argv[1] == "--list":
            list_admins()
            return
        
        # Make the specified users admins
        for email_or_username in sys.argv[1:]:
            make_admin(email_or_username)

if __name__ == "__main__":
    main()