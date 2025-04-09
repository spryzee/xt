from app import app, db
from models import User, DiscordToken
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

with app.app_context():
    # Check if there are any users
    user_count = User.query.count()
    if user_count == 0:
        # Create a sample user
        user = User(
            username="demo",
            email="demo@example.com",
            password_hash=generate_password_hash("demo123"),
            is_admin=True,
            is_premium=True,
            premium_until=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(user)
        db.session.commit()
        print(f"Created demo user with ID: {user.id}")
    else:
        user = User.query.first()
        print(f"Using existing user with ID: {user.id}")
    
    # Add sample tokens
    token_count = DiscordToken.query.count()
    if token_count == 0:
        # Create a few sample tokens
        token1 = DiscordToken(
            token="sample_token_1234567890",
            label="Gaming Server",
            is_active=True,
            status="verified",
            server_count=3,
            user_id=user.id
        )
        
        token2 = DiscordToken(
            token="sample_token_0987654321",
            label="Community Server",
            is_active=True,
            status="verified",
            server_count=5,
            user_id=user.id
        )
        
        token3 = DiscordToken(
            token="sample_token_inactive",
            label="Test Server",
            is_active=False,
            status="not verified",
            server_count=2,
            user_id=user.id
        )
        
        db.session.add_all([token1, token2, token3])
        db.session.commit()
        print(f"Added {3} sample tokens.")
    else:
        print(f"Already have {token_count} tokens in the database.")