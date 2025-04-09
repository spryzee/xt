import os
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    discord_id = db.Column(db.String(64), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_ip = db.Column(db.String(45), nullable=True)  # Store last IP for single IP login restriction
    is_admin = db.Column(db.Boolean, default=False)
    is_premium = db.Column(db.Boolean, default=False)
    premium_until = db.Column(db.DateTime, nullable=True)
    tokens = db.relationship('DiscordToken', backref='user', lazy=True, cascade="all, delete-orphan")
    custom_scripts = db.relationship('CustomScript', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_user_folder_path(self):
        base_path = os.path.join('users', self.username)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        return base_path

class DiscordToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="not verified")
    server_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CustomScript(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    size = db.Column(db.Integer, default=0)  # Size in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def get_script_path(self):
        """Get the path where this script should be saved"""
        user = User.query.get(self.user_id)
        if not user:
            return None
        user_folder = user.get_user_folder_path()
        script_filename = f"custom_{self.id}_{secure_filename(self.name)}.py"
        return os.path.join(user_folder, script_filename)
    
    def save_to_disk(self):
        """Save the script content to disk"""
        path = self.get_script_path()
        if not path:
            return False
        
        try:
            with open(path, 'w') as f:
                f.write(self.content)
            return True
        except Exception as e:
            print(f"Error saving script to disk: {str(e)}")
            return False

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    auto_reconnect = db.Column(db.Boolean, default=True)
    single_ip_login = db.Column(db.Boolean, default=True)
    enable_notifications = db.Column(db.Boolean, default=True)
    enable_2fa = db.Column(db.Boolean, default=False)
    proxy_url = db.Column(db.String(255), nullable=True)
    session_timeout = db.Column(db.Integer, default=1440)  # minutes
    ip_whitelist = db.Column(db.Text, nullable=True)  # Comma-separated IP addresses
    debug_mode = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(255), nullable=True)
    api_key = db.Column(db.String(64), nullable=True)
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(16), default='string')  # string, int, float, bool, json
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get(cls, key, default=None):
        """Get a system setting by key with type conversion"""
        setting = cls.query.filter_by(key=key).first()
        if not setting:
            return default
            
        # Convert value based on type
        if setting.value_type == 'int':
            return int(setting.value) if setting.value else default
        elif setting.value_type == 'float':
            return float(setting.value) if setting.value else default
        elif setting.value_type == 'bool':
            return setting.value.lower() == 'true' if setting.value else default
        elif setting.value_type == 'json':
            try:
                import json
                return json.loads(setting.value) if setting.value else default
            except:
                return default
        else:  # string or unknown type
            return setting.value if setting.value else default
    
    @classmethod
    def set(cls, key, value, value_type=None, description=None):
        """Set or update a system setting"""
        setting = cls.query.filter_by(key=key).first()
        
        # Determine value type if not provided
        if value_type is None:
            if isinstance(value, bool):
                value_type = 'bool'
            elif isinstance(value, int):
                value_type = 'int'
            elif isinstance(value, float):
                value_type = 'float'
            elif isinstance(value, (dict, list)):
                value_type = 'json'
                import json
                value = json.dumps(value)
            else:
                value_type = 'string'
        
        # Convert value to string for storage
        if value_type == 'bool':
            str_value = str(value).lower()
        else:
            str_value = str(value) if value is not None else None
            
        if setting:
            # Update existing setting
            setting.value = str_value
            setting.value_type = value_type
            if description:
                setting.description = description
        else:
            # Create new setting
            setting = cls(
                key=key,
                value=str_value,
                value_type=value_type,
                description=description
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    

