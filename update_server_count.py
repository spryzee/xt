from app import app, db
from models import DiscordToken

with app.app_context():
    tokens = DiscordToken.query.all()
    updated_count = 0
    
    for token in tokens:
        if token.server_count == 0:
            # Assign a pseudorandom server count based on token length
            # This is just for demonstration purposes
            token.server_count = len(token.token) % 5 + 2
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        print(f'Updated {updated_count} tokens with server count data.')
    else:
        print('No tokens needed to be updated.')