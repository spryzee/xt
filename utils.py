import os
import logging
import shutil
import discord
import asyncio
from app import app

logger = logging.getLogger(__name__)

def create_selfbot_script(user):
    """Create a personalized selfbot script for the user with their tokens"""
    try:
        # Create user directory if it doesn't exist
        user_folder = user.get_user_folder_path()
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Get active tokens
        active_tokens = [token.token for token in user.tokens if token.is_active]
        
        # Copy template and replace tokens
        script_path = os.path.join(user_folder, f"{user.username}.py")
        
        # Get the template path
        template_path = os.path.join(app.root_path, 'user_template.py')
        if not os.path.exists(template_path):
            # If template is not in app folder, use the one in root folder
            template_path = 'user_template.py'
        
        # Read the template
        with open(template_path, 'r') as template_file:
            template_content = template_file.read()
        
        # Format tokens list
        tokens_str = ",\n    ".join([f'"{token}"' for token in active_tokens])
        tokens_list = f"[\n    {tokens_str}\n]" if active_tokens else "[]"
        
        # Replace placeholder with actual tokens
        script_content = template_content.replace("TOKENS = []", f"TOKENS = {tokens_list}")
        
        # Premium users can use custom scripts
        custom_script_imports = ""
        if user.is_premium:
            from models import CustomScript
            
            # Get active custom scripts
            active_scripts = CustomScript.query.filter_by(user_id=user.id, is_active=True).all()
            
            if active_scripts:
                # Save all active custom scripts to user folder
                for script in active_scripts:
                    script.save_to_disk()
                
                # Create imports for all active scripts
                imports = []
                functions = []
                for script in active_scripts:
                    script_name = f"custom_{script.id}_{os.path.splitext(os.path.basename(script.get_script_path()))[0]}"
                    imports.append(f"import {script_name}")
                    functions.append(f"    # Run custom script: {script.name}\n    {script_name}.run_script(client)")
                
                custom_script_imports = "\n".join(imports)
                custom_functions = "\n".join(functions)
                
                # Add the custom imports at the top of the file
                script_content = script_content.replace("import discord", f"import discord\n{custom_script_imports}")
                
                # Add custom function calls to the on_ready event
                script_content = script_content.replace("    print(f\"Logged in as {client.user}\")", 
                                                       f"    print(f\"Logged in as {{client.user}}\")\n{custom_functions}")
        
        # Write the personalized script
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)
        
        logger.info(f"Created selfbot script for user {user.username} with {len(active_tokens)} tokens and premium={user.is_premium}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating selfbot script: {str(e)}")
        return False

async def validate_discord_token(token):
    """Validate a Discord token by attempting to login"""
    try:
        # Basic format validation
        if not token or len(token) < 50:
            return False, "Token is too short or invalid format"
        
        # Check token format (rough check)
        token_parts = token.split('.')
        if len(token_parts) != 3:
            return False, "Token has invalid format (should have 3 parts separated by periods)"
        
        # Initialize Discord client
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        # Try to login with the token
        await client.login(token, bot=False)
        
        # If successful, close the client
        await client.close()
        return True, None
    
    except discord.errors.LoginFailure:
        return False, "Discord authentication failed - the token is invalid or has been revoked"
    except discord.errors.HTTPException as e:
        if e.status == 401:
            return False, "Unauthorized: Token is invalid or expired"
        elif e.status == 429:
            return False, "Rate limited: Too many requests to Discord API"
        else:
            return False, f"HTTP Error: {e.status} - {e.text}"
    except discord.errors.DiscordServerError:
        return False, "Discord server error - please try again later"
    except asyncio.TimeoutError:
        return False, "Connection to Discord timed out - please check your internet connection"
    except Exception as e:
        return False, f"Validation error: {str(e)}"
    finally:
        # Ensure client is closed
        if 'client' in locals():
            try:
                await client.close()
            except:
                pass
