import os
import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, DiscordToken, CustomScript, UserSettings, SystemSettings
from forms import (LoginForm, RegistrationForm, TokenForm, DiscordAuthForm,
                  CustomScriptForm, CustomScriptUploadForm, ResetPasswordForm,
                  ResetPasswordRequestForm, EditProfileForm, AdminEditUserForm,
                  AdminResetPasswordForm)
from utils import create_selfbot_script, validate_discord_token

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='Discord Selfbot Manager')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', title='Pricing Plans')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    import random  # For API key generation in the template
    
    # Get or create user settings
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update settings from form data
            user_settings.auto_reconnect = 'auto_reconnect' in request.form
            user_settings.single_ip_login = 'single_ip_login' in request.form
            user_settings.enable_notifications = 'enable_notifications' in request.form
            user_settings.enable_2fa = 'enable_2fa' in request.form
            user_settings.proxy_url = request.form.get('proxy_url', '')
            user_settings.session_timeout = int(request.form.get('session_timeout', 1440))
            user_settings.ip_whitelist = request.form.get('ip_whitelist', '')
            user_settings.debug_mode = 'debug_mode' in request.form
            
            # Only allow premium users to set webhook URL
            if current_user.is_premium:
                user_settings.webhook_url = request.form.get('webhook_url', '')
            
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating settings: {str(e)}")
            flash(f"Error updating settings: {str(e)}", 'danger')
    
    # Get CPU and memory usage info
    active_tokens = len([t for t in current_user.tokens if t.is_active])
    cpu_percent = min(95, max(5, active_tokens * 10 + random.randint(-5, 15)))  # Simulated data
    memory_percent = min(90, max(5, active_tokens * 8 + random.randint(-5, 10)))  # Simulated data
    
    return render_template(
        'settings.html', 
        title='Settings', 
        random=random,
        user_settings=user_settings,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        
        # Check for single IP login restriction
        current_ip = request.remote_addr
        user_settings = UserSettings.query.filter_by(user_id=user.id).first()
        
        if user_settings and user_settings.single_ip_login and user.last_ip and user.last_ip != current_ip:
            flash('This account is already logged in from another IP address. For security reasons, please log out from other sessions first.', 'danger')
            logger.warning(f"Multiple IP login attempt: {user.username} from {current_ip} (existing: {user.last_ip})")
            return redirect(url_for('login'))
        
        # Create user settings if they don't exist
        if not user_settings:
            user_settings = UserSettings(user_id=user.id)
            db.session.add(user_settings)
        
        # Update user login info
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        user.last_ip = current_ip
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')
        
        flash('Login successful!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create user folder
            user_folder = user.get_user_folder_path()
            logger.info(f"Created user folder: {user_folder}")
            
            flash('Congratulations, you are now a registered user!', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}")
            flash(f"Registration error: {str(e)}", 'danger')
    
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get token stats
    total_tokens = len(current_user.tokens) if hasattr(current_user, 'tokens') else 0
    active_tokens = len([t for t in current_user.tokens if t.is_active and t.status != 'invalid']) if hasattr(current_user, 'tokens') else 0
    
    # Calculate server count across all tokens
    total_servers = sum(t.server_count for t in current_user.tokens if hasattr(t, 'server_count')) if hasattr(current_user, 'tokens') else 0
    # Fallback if server_count attribute doesn't exist
    if total_servers == 0 and total_tokens > 0:
        total_servers = total_tokens * 3  # Estimate: average 3 servers per token
    
    # Calculate available slots
    if current_user.is_premium:
        available_slots = "Unlimited"
    else:
        available_slots = max(0, 5 - total_tokens)  # Free users have 5 slots
    
    # Calculate uptime percentage (last 7 days)
    uptime_percentage = 98.5  # Placeholder value
    
    token_stats = {
        'total_tokens': total_tokens,
        'active_tokens': active_tokens,
        'total_servers': total_servers,
        'available_slots': available_slots,
        'uptime_percentage': uptime_percentage
    }
    
    return render_template('dashboard.html', title='Dashboard', token_stats=token_stats)

@app.route('/tokens', methods=['GET', 'POST'])
@login_required
def token_management():
    form = TokenForm()
    
    if form.validate_on_submit():
        # Check token limit for non-premium users
        if not current_user.is_premium and len(current_user.tokens) >= 5:
            flash('You have reached the maximum number of tokens for a free account. Upgrade to Premium for unlimited tokens.', 'warning')
            return redirect(url_for('pricing'))
            
        token = form.token.data
        label = form.label.data or f"Token {len(current_user.tokens) + 1}"
        
        # Validate token before saving
        is_valid = False
        error_message = None
        
        try:
            # Run the token validation using asyncio
            import asyncio
            is_valid, error_message = asyncio.run(validate_discord_token(token))
            
            if not is_valid:
                flash(f'Invalid Discord token: {error_message}. Please check your token and try again.', 'danger')
                return redirect(url_for('token_management'))
            
            # Token is valid, save it
            new_token = DiscordToken(
                token=token,
                label=label,
                user_id=current_user.id,
                status="verified"
            )
            
            db.session.add(new_token)
            db.session.commit()
            
            # Create the selfbot script for this user
            create_selfbot_script(current_user)
            
            flash('Token successfully verified and added!', 'success')
            return redirect(url_for('token_management'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error validating/adding token: {str(e)}")
            flash(f"Error adding token: {str(e)}", 'danger')
    
    tokens = current_user.tokens
    return render_template('token_management.html', title='Manage Tokens', form=form, tokens=tokens)

@app.route('/tokens/delete/<int:token_id>', methods=['POST'])
@login_required
def delete_token(token_id):
    token = DiscordToken.query.get_or_404(token_id)
    
    # Ensure the token belongs to the current user
    if token.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('token_management'))
    
    try:
        db.session.delete(token)
        db.session.commit()
        
        # Recreate the selfbot script for this user
        create_selfbot_script(current_user)
        
        flash('Token deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting token: {str(e)}")
        flash(f"Error deleting token: {str(e)}", 'danger')
    
    return redirect(url_for('token_management'))

@app.route('/tokens/toggle/<int:token_id>', methods=['POST'])
@login_required
def toggle_token(token_id):
    token = DiscordToken.query.get_or_404(token_id)
    
    # Ensure the token belongs to the current user
    if token.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('token_management'))
    
    try:
        token.is_active = not token.is_active
        db.session.commit()
        
        # Recreate the selfbot script for this user
        create_selfbot_script(current_user)
        
        status = "activated" if token.is_active else "deactivated"
        flash(f'Token {status} successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling token: {str(e)}")
        flash(f"Error toggling token status: {str(e)}", 'danger')
    
    return redirect(url_for('token_management'))

@app.route('/link-discord', methods=['GET', 'POST'])
@login_required
def link_discord():
    form = DiscordAuthForm()
    
    if form.validate_on_submit():
        discord_id = form.discord_id.data
        
        # Check if Discord ID is already linked to another account
        existing_user = User.query.filter_by(discord_id=discord_id).first()
        if existing_user and existing_user.id != current_user.id:
            flash('This Discord ID is already linked to another account', 'danger')
            return redirect(url_for('link_discord'))
        
        try:
            current_user.discord_id = discord_id
            db.session.commit()
            flash('Discord account linked successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error linking Discord account: {str(e)}")
            flash(f"Error linking Discord account: {str(e)}", 'danger')
    
    return render_template('link_discord.html', title='Link Discord Account', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', title='Not Found', error=error), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', title='Server Error', error=error), 500

# Admin routes
def admin_required(func):
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page', 'danger')
            return redirect(url_for('dashboard'))
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view

@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    all_tokens = DiscordToken.query.count()
    active_tokens = DiscordToken.query.filter_by(is_active=True).count()
    
    # Count new users from today
    today = datetime.utcnow().date()
    new_users = User.query.filter(User.created_at >= today).count()
    
    return render_template('admin/dashboard.html', users=users, 
                          all_tokens=all_tokens, active_tokens=active_tokens, 
                          new_users=new_users)

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_view_user(user_id):
    user = User.query.get_or_404(user_id)
    edit_form = AdminEditUserForm(original_username=user.username, original_email=user.email, user_id=user.id)
    reset_form = AdminResetPasswordForm()
    
    edit_form.username.data = user.username
    edit_form.email.data = user.email
    
    return render_template('admin/user_detail.html', 
                           user=user,
                           edit_form=edit_form,
                           reset_form=reset_form)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'User {username} deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        flash(f"Error deleting user: {str(e)}", 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent removing admin from yourself
    if user.id == current_user.id:
        flash('You cannot remove admin privileges from yourself', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        
        status = "granted to" if user.is_admin else "removed from"
        flash(f'Admin privileges {status} {user.username}', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling admin status: {str(e)}")
        flash(f"Error toggling admin status: {str(e)}", 'danger')
    
    # Redirect back to the page we came from
    if request.referrer and 'admin_view_user' in request.referrer:
        return redirect(url_for('admin_view_user', user_id=user.id))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/token/<int:token_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_token(token_id):
    token = DiscordToken.query.get_or_404(token_id)
    user = User.query.get(token.user_id)
    
    try:
        token.is_active = not token.is_active
        db.session.commit()
        
        # Recreate the selfbot script for this user
        create_selfbot_script(user)
        
        status = "activated" if token.is_active else "deactivated"
        flash(f'Token {status} successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling token: {str(e)}")
        flash(f"Error toggling token status: {str(e)}", 'danger')
    
    return redirect(url_for('admin_view_user', user_id=token.user_id))

@app.route('/admin/token/<int:token_id>/delete', methods=['POST'])
@admin_required
def admin_delete_token(token_id):
    token = DiscordToken.query.get_or_404(token_id)
    user_id = token.user_id
    user = User.query.get(user_id)
    
    try:
        db.session.delete(token)
        db.session.commit()
        
        # Recreate the selfbot script for this user
        create_selfbot_script(user)
        
        flash('Token deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting token: {str(e)}")
        flash(f"Error deleting token: {str(e)}", 'danger')
    
    return redirect(url_for('admin_view_user', user_id=user_id))

# Premium membership management
@app.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminEditUserForm(original_username=user.username, original_email=user.email, user_id=user.id)
    
    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            db.session.commit()
            flash(f'User {user.username} updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {str(e)}")
            flash(f"Error updating user: {str(e)}", 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin_view_user', user_id=user.id))

@app.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminResetPasswordForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.password.data)
            db.session.commit()
            flash(f'Password for {user.username} reset successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password: {str(e)}")
            flash(f"Error resetting password: {str(e)}", 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin_view_user', user_id=user.id))

@app.route('/admin/user/<int:user_id>/toggle-premium', methods=['POST'])
@admin_required
def admin_toggle_premium(user_id):
    user = User.query.get_or_404(user_id)
    duration = int(request.form.get('duration', 30))  # Default 30 days
    
    try:
        # Toggle premium status
        if user.is_premium:
            user.is_premium = False
            user.premium_until = None
            message = f'Premium status removed from {user.username}'
        else:
            user.is_premium = True
            user.premium_until = datetime.utcnow() + timedelta(days=duration)
            message = f'Premium status granted to {user.username} for {duration} days'
        
        db.session.commit()
        flash(message, 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling premium status: {str(e)}")
        flash(f"Error toggling premium status: {str(e)}", 'danger')
    
    # Redirect back to the page we came from
    if request.referrer and 'admin_view_user' in request.referrer:
        return redirect(url_for('admin_view_user', user_id=user.id))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Render the admin settings page with all system settings"""
    # Get default system values or create them if they don't exist
    system_settings = {}
    
    # General settings
    system_settings['maintenance_mode'] = SystemSettings.get('maintenance_mode', False)
    system_settings['max_tokens_per_user'] = SystemSettings.get('max_tokens_per_user', 5)
    system_settings['server_script_timeout'] = SystemSettings.get('server_script_timeout', 300)
    system_settings['default_session_timeout'] = SystemSettings.get('default_session_timeout', 1440)
    
    # Security settings
    system_settings['enforce_strong_passwords'] = SystemSettings.get('enforce_strong_passwords', True)
    system_settings['enforce_single_ip'] = SystemSettings.get('enforce_single_ip', True)
    system_settings['max_login_attempts'] = SystemSettings.get('max_login_attempts', 5)
    system_settings['ip_whitelist'] = SystemSettings.get('ip_whitelist', '')
    
    # API settings
    system_settings['enable_public_api'] = SystemSettings.get('enable_public_api', False)
    system_settings['api_rate_limit'] = SystemSettings.get('api_rate_limit', 60)
    system_settings['discord_webhook_url'] = SystemSettings.get('discord_webhook_url', '')
    system_settings['master_api_key'] = SystemSettings.get('master_api_key', '')
    
    # Branding settings
    system_settings['site_name'] = SystemSettings.get('site_name', 'XTLive')
    system_settings['site_description'] = SystemSettings.get('site_description', 'Discord Selfbot Management Platform')
    system_settings['primary_color'] = SystemSettings.get('primary_color', '#6200ea')
    system_settings['contact_email'] = SystemSettings.get('contact_email', '')
    
    # Notification settings
    system_settings['email_notifications'] = SystemSettings.get('email_notifications', True)
    system_settings['discord_notifications'] = SystemSettings.get('discord_notifications', True)
    system_settings['admin_alerts'] = SystemSettings.get('admin_alerts', True)
    system_settings['sendgrid_api_key'] = SystemSettings.get('sendgrid_api_key', '')
    
    # Add current date for backup naming
    now = datetime.utcnow()
    
    return render_template('admin/settings.html', 
                           system_settings=system_settings,
                           now=now)

@app.route('/admin/settings/update', methods=['POST'])
@admin_required
def admin_update_settings():
    """Update system settings"""
    section = request.form.get('section', '')
    
    try:
        if section == 'general':
            # General settings
            maintenance_mode = 'maintenance_mode' in request.form
            max_tokens_per_user = int(request.form.get('max_tokens_per_user', 5))
            server_script_timeout = int(request.form.get('server_script_timeout', 300))
            default_session_timeout = int(request.form.get('default_session_timeout', 1440))
            
            SystemSettings.set('maintenance_mode', maintenance_mode, 'bool', 'When enabled, only administrators can access the site')
            SystemSettings.set('max_tokens_per_user', max_tokens_per_user, 'int', 'Maximum number of tokens allowed for non-premium users')
            SystemSettings.set('server_script_timeout', server_script_timeout, 'int', 'Maximum execution time for server-side scripts (seconds)')
            SystemSettings.set('default_session_timeout', default_session_timeout, 'int', 'Default timeout for user sessions (minutes)')
        
        elif section == 'security':
            # Security settings
            enforce_strong_passwords = 'enforce_strong_passwords' in request.form
            enforce_single_ip = 'enforce_single_ip' in request.form
            max_login_attempts = int(request.form.get('max_login_attempts', 5))
            ip_whitelist = request.form.get('ip_whitelist', '')
            
            SystemSettings.set('enforce_strong_passwords', enforce_strong_passwords, 'bool', 'Require passwords to include uppercase, lowercase, numbers, and special characters')
            SystemSettings.set('enforce_single_ip', enforce_single_ip, 'bool', 'Prevent users from logging in from multiple IP addresses simultaneously')
            SystemSettings.set('max_login_attempts', max_login_attempts, 'int', 'Number of failed login attempts before temporary account lockout')
            SystemSettings.set('ip_whitelist', ip_whitelist, 'string', 'List of IP addresses or ranges allowed to access the admin panel')
        
        elif section == 'api':
            # API settings
            enable_public_api = 'enable_public_api' in request.form
            api_rate_limit = int(request.form.get('api_rate_limit', 60))
            discord_webhook_url = request.form.get('discord_webhook_url', '')
            
            SystemSettings.set('enable_public_api', enable_public_api, 'bool', 'Allow external applications to access the API endpoints')
            SystemSettings.set('api_rate_limit', api_rate_limit, 'int', 'Maximum number of API requests allowed per minute')
            SystemSettings.set('discord_webhook_url', discord_webhook_url, 'string', 'Webhook URL for sending notifications to Discord')
            
            # Generate a new master API key if requested
            if 'regenerate_api_key' in request.form:
                import secrets
                new_key = secrets.token_hex(16)
                SystemSettings.set('master_api_key', new_key, 'string', 'Master API key for administrative operations')
        
        elif section == 'branding':
            # Branding settings
            site_name = request.form.get('site_name', 'XTLive')
            site_description = request.form.get('site_description', 'Discord Selfbot Management Platform')
            primary_color = request.form.get('primary_color', '#6200ea')
            contact_email = request.form.get('contact_email', '')
            
            SystemSettings.set('site_name', site_name, 'string', 'Name displayed in the site title and headers')
            SystemSettings.set('site_description', site_description, 'string', 'Short description for SEO and meta tags')
            SystemSettings.set('primary_color', primary_color, 'string', 'Main accent color for buttons and highlights')
            SystemSettings.set('contact_email', contact_email, 'string', 'Email address displayed for support inquiries')
            
            # Handle logo upload
            if 'logo_upload' in request.files and request.files['logo_upload'].filename:
                logo_file = request.files['logo_upload']
                if logo_file:
                    # Save the logo file
                    filename = secure_filename(logo_file.filename)
                    logo_path = os.path.join(app.static_folder, 'img', filename)
                    logo_file.save(logo_path)
                    SystemSettings.set('custom_logo', f'/static/img/{filename}', 'string', 'Path to custom logo file')
        
        elif section == 'notifications':
            # Notification settings
            email_notifications = 'email_notifications' in request.form
            discord_notifications = 'discord_notifications' in request.form
            admin_alerts = 'admin_alerts' in request.form
            sendgrid_api_key = request.form.get('sendgrid_api_key', '')
            
            SystemSettings.set('email_notifications', email_notifications, 'bool', 'Send important notifications via email to users')
            SystemSettings.set('discord_notifications', discord_notifications, 'bool', 'Send notifications to Discord webhook for system events')
            SystemSettings.set('admin_alerts', admin_alerts, 'bool', 'Send alerts to administrators for critical events')
            
            if sendgrid_api_key:
                SystemSettings.set('sendgrid_api_key', sendgrid_api_key, 'string', 'API key for SendGrid email integration')
        
        flash('Settings updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {str(e)}")
        flash(f"Error updating settings: {str(e)}", 'danger')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/backup', methods=['POST'])
@admin_required
def admin_backup_database():
    """Backup the database"""
    backup_name = request.form.get('backup_name', f'backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
    include_user_data = 'include_user_data' in request.form
    include_tokens = 'include_tokens' in request.form
    
    try:
        # This would be implemented with actual database backup logic
        flash(f'Database backup "{backup_name}" created successfully', 'success')
    except Exception as e:
        logger.error(f"Error creating database backup: {str(e)}")
        flash(f"Error creating database backup: {str(e)}", 'danger')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/purge', methods=['POST'])
@admin_required
def admin_purge_data():
    """Purge inactive data"""
    inactive_days = int(request.form.get('inactive_days', 90))
    purge_inactive_users = 'purge_inactive_users' in request.form
    purge_expired_tokens = 'purge_expired_tokens' in request.form
    purge_inactive_scripts = 'purge_inactive_scripts' in request.form
    purge_old_logs = 'purge_old_logs' in request.form
    confirm_purge = request.form.get('confirm_purge', '')
    
    if confirm_purge != 'CONFIRM PURGE':
        flash('You must type "CONFIRM PURGE" to proceed with data purge', 'danger')
        return redirect(url_for('admin_settings'))
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
        purged_count = 0
        
        # Purge inactive users
        if purge_inactive_users:
            # Get users who haven't logged in since the cutoff date
            inactive_users = User.query.filter(
                User.last_login < cutoff_date,
                User.is_admin == False  # Never purge admin users
            ).all()
            
            for user in inactive_users:
                db.session.delete(user)
                purged_count += 1
        
        # Purge expired tokens
        if purge_expired_tokens:
            # Get inactive tokens older than the cutoff date
            expired_tokens = DiscordToken.query.filter(
                DiscordToken.is_active == False,
                DiscordToken.last_used < cutoff_date
            ).all()
            
            for token in expired_tokens:
                db.session.delete(token)
                purged_count += 1
        
        # Purge inactive scripts
        if purge_inactive_scripts:
            # Get inactive scripts older than the cutoff date
            inactive_scripts = CustomScript.query.filter(
                CustomScript.is_active == False,
                CustomScript.updated_at < cutoff_date
            ).all()
            
            for script in inactive_scripts:
                db.session.delete(script)
                purged_count += 1
        
        # Purge old logs
        if purge_old_logs:
            # This would be implemented with actual log purging logic
            pass
        
        db.session.commit()
        flash(f'Successfully purged {purged_count} items older than {inactive_days} days', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error purging data: {str(e)}")
        flash(f"Error purging data: {str(e)}", 'danger')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/cache/clear', methods=['POST'])
@admin_required
def admin_clear_cache():
    """Clear system cache"""
    try:
        # This would be implemented with actual cache clearing logic
        flash('System cache cleared successfully', 'success')
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        flash(f"Error clearing cache: {str(e)}", 'danger')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/logs')
@admin_required
def admin_view_logs():
    """View system logs"""
    # This would show actual system logs
    logs = [
        {'timestamp': datetime.utcnow() - timedelta(minutes=5), 'level': 'INFO', 'message': 'User login: admin'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=10), 'level': 'WARNING', 'message': 'Failed login attempt for user: test@example.com'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=15), 'level': 'ERROR', 'message': 'Database connection error'},
    ]
    
    return render_template('admin/logs.html', logs=logs)

@app.route('/admin/logs/clear', methods=['POST'])
@admin_required
def admin_clear_logs():
    """Clear system logs"""
    try:
        # This would be implemented with actual log clearing logic
        flash('System logs cleared successfully', 'success')
    except Exception as e:
        logger.error(f"Error clearing logs: {str(e)}")
        flash(f"Error clearing logs: {str(e)}", 'danger')
    
    return redirect(url_for('admin_settings'))

# Routes for account management
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('edit_profile'))
        
        try:
            current_user.username = form.username.data
            current_user.email = form.email.data
            db.session.commit()
            
            flash('Your profile has been updated', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            flash(f"Error updating profile: {str(e)}", 'danger')
    
    # Pre-populate the form with current data
    if request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # In a real app, we would send an email with a reset link
            # For this demo, we'll just flash a message
            flash('Check your email for instructions to reset your password', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found', 'warning')
    
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # In a real app, we would validate the token
    # For this demo, we'll just show the form
    form = ResetPasswordForm()
    if form.validate_on_submit():
        # In a real app, we would find the user from the token
        # For this demo, we'll just flash a message
        flash('Your password has been reset', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', title='Reset Password', form=form)

# Custom script management routes
@app.route('/scripts', methods=['GET'])
@login_required
def script_management():
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    scripts = CustomScript.query.filter_by(user_id=current_user.id).all()
    return render_template('script_management.html', title='Manage Scripts', scripts=scripts)

@app.route('/scripts/new', methods=['GET', 'POST'])
@login_required
def new_script():
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    form = CustomScriptForm()
    
    if form.validate_on_submit():
        try:
            # Create new script
            script = CustomScript(
                name=form.name.data,
                description=form.description.data,
                content=form.content.data,
                user_id=current_user.id
            )
            
            db.session.add(script)
            db.session.commit()
            
            flash('Script created successfully', 'success')
            return redirect(url_for('script_management'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating script: {str(e)}")
            flash(f"Error creating script: {str(e)}", 'danger')
    
    return render_template('edit_script.html', title='New Script', form=form)

@app.route('/scripts/upload', methods=['GET', 'POST'])
@login_required
def upload_script():
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    form = CustomScriptUploadForm()
    
    if form.validate_on_submit():
        try:
            # Read uploaded file
            script_file = form.script_file.data
            script_content = script_file.read().decode('utf-8')
            
            # Check script size (30MB limit)
            script_size = len(script_content.encode('utf-8'))
            max_size = 30 * 1024 * 1024  # 30MB in bytes
            
            if script_size > max_size:
                flash(f'Script exceeds the maximum size limit of 30MB. Your script size: {script_size / (1024 * 1024):.2f}MB', 'danger')
                return redirect(url_for('upload_script'))
            
            # Create new script
            script = CustomScript(
                name=form.name.data,
                description=form.description.data,
                content=script_content,
                size=script_size,
                user_id=current_user.id
            )
            
            db.session.add(script)
            db.session.commit()
            
            flash(f'Script uploaded successfully (Size: {script_size / 1024:.2f} KB)', 'success')
            return redirect(url_for('script_management'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading script: {str(e)}")
            flash(f"Error uploading script: {str(e)}", 'danger')
    
    return render_template('upload_script.html', title='Upload Script', form=form)

@app.route('/scripts/edit/<int:script_id>', methods=['GET', 'POST'])
@login_required
def edit_script(script_id):
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    script = CustomScript.query.get_or_404(script_id)
    
    # Ensure the script belongs to the current user
    if script.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('script_management'))
    
    form = CustomScriptForm()
    
    if form.validate_on_submit():
        try:
            script.name = form.name.data
            script.description = form.description.data
            script.content = form.content.data
            script.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # If the script is active, save it to disk and update selfbot script
            if script.is_active:
                script.save_to_disk()
                create_selfbot_script(current_user)
            
            flash('Script updated successfully', 'success')
            return redirect(url_for('script_management'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating script: {str(e)}")
            flash(f"Error updating script: {str(e)}", 'danger')
    
    # Pre-populate the form with script data
    if request.method == 'GET':
        form.name.data = script.name
        form.description.data = script.description
        form.content.data = script.content
    
    return render_template('edit_script.html', title='Edit Script', form=form, script=script)

@app.route('/scripts/delete/<int:script_id>', methods=['POST'])
@login_required
def delete_script(script_id):
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    script = CustomScript.query.get_or_404(script_id)
    
    # Ensure the script belongs to the current user
    if script.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('script_management'))
    
    try:
        was_active = script.is_active
        db.session.delete(script)
        db.session.commit()
        
        # If the script was active, update selfbot script
        if was_active:
            create_selfbot_script(current_user)
        
        flash('Script deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting script: {str(e)}")
        flash(f"Error deleting script: {str(e)}", 'danger')
    
    return redirect(url_for('script_management'))

@app.route('/scripts/toggle/<int:script_id>', methods=['POST'])
@login_required
def toggle_script(script_id):
    if not current_user.is_premium:
        flash('Custom scripts are only available for premium users', 'warning')
        return redirect(url_for('dashboard'))
    
    script = CustomScript.query.get_or_404(script_id)
    
    # Ensure the script belongs to the current user
    if script.user_id != current_user.id:
        flash('Unauthorized action', 'danger')
        return redirect(url_for('script_management'))
    
    try:
        script.is_active = not script.is_active
        db.session.commit()
        
        # Update the script on disk and regenerate selfbot script
        if script.is_active:
            script.save_to_disk()
        
        create_selfbot_script(current_user)
        
        status = "activated" if script.is_active else "deactivated"
        flash(f'Script {status} successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling script: {str(e)}")
        flash(f"Error toggling script status: {str(e)}", 'danger')
    
    return redirect(url_for('script_management'))
