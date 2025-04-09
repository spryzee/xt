import os
from app import app, db
from sqlalchemy import text

def apply_migration():
    print("Starting database migration...")
    with app.app_context():
        try:
            conn = db.engine.connect()
            
            # Check for columns in user table
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'is_admin';
            """))
            is_admin_exists = result.scalar() is not None
            
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'is_premium';
            """))
            is_premium_exists = result.scalar() is not None
            
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'premium_until';
            """))
            premium_until_exists = result.scalar() is not None
            
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'last_ip';
            """))
            last_ip_exists = result.scalar() is not None
            
            # Check for server_count in discord_token table
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'discord_token' AND column_name = 'server_count';
            """))
            server_count_exists = result.scalar() is not None
            
            # Check if tables exist
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'custom_script';
            """))
            custom_script_exists = result.scalar() is not None
            
            result = conn.execute(text("""
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'user_settings';
            """))
            user_settings_exists = result.scalar() is not None
            
            # Check for size column in custom_script
            size_column_exists = False
            if custom_script_exists:
                result = conn.execute(text("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'custom_script' AND column_name = 'size';
                """))
                size_column_exists = result.scalar() is not None
            
            # Add is_admin column if needed
            if not is_admin_exists:
                print("Adding is_admin column to user table...")
                conn.execute(text("""
                    ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
                """))
                conn.commit()
            
            # Add is_premium column if needed
            if not is_premium_exists:
                print("Adding is_premium column to user table...")
                conn.execute(text("""
                    ALTER TABLE "user" ADD COLUMN is_premium BOOLEAN DEFAULT FALSE;
                """))
                conn.commit()
            
            # Add premium_until column if needed
            if not premium_until_exists:
                print("Adding premium_until column to user table...")
                conn.execute(text("""
                    ALTER TABLE "user" ADD COLUMN premium_until TIMESTAMP;
                """))
                conn.commit()
            
            # Add last_ip column if needed
            if not last_ip_exists:
                print("Adding last_ip column to user table...")
                conn.execute(text("""
                    ALTER TABLE "user" ADD COLUMN last_ip VARCHAR(45);
                """))
                conn.commit()
                
            # Add server_count column to discord_token if needed
            if not server_count_exists:
                print("Adding server_count column to discord_token table...")
                conn.execute(text("""
                    ALTER TABLE discord_token ADD COLUMN server_count INTEGER DEFAULT 0;
                """))
                conn.commit()
            
            # Create custom_script table if needed
            if not custom_script_exists:
                print("Creating custom_script table...")
                conn.execute(text("""
                    CREATE TABLE custom_script (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        content TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT FALSE,
                        size INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
                    );
                """))
                conn.commit()
            elif not size_column_exists:
                print("Adding size column to custom_script table...")
                conn.execute(text("""
                    ALTER TABLE custom_script ADD COLUMN size INTEGER DEFAULT 0;
                """))
                conn.commit()
            
            # Create user_settings table if needed
            if not user_settings_exists:
                print("Creating user_settings table...")
                conn.execute(text("""
                    CREATE TABLE user_settings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        auto_reconnect BOOLEAN DEFAULT TRUE,
                        single_ip_login BOOLEAN DEFAULT TRUE,
                        enable_notifications BOOLEAN DEFAULT TRUE,
                        enable_2fa BOOLEAN DEFAULT FALSE,
                        proxy_url VARCHAR(255),
                        session_timeout INTEGER DEFAULT 1440,
                        ip_whitelist TEXT,
                        debug_mode BOOLEAN DEFAULT FALSE,
                        webhook_url VARCHAR(255),
                        api_key VARCHAR(64),
                        FOREIGN KEY (user_id) REFERENCES "user" (id) ON DELETE CASCADE
                    );
                """))
                conn.commit()
            
            conn.close()
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    apply_migration()