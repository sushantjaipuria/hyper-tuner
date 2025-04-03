"""Configuration management for the application"""
import os
import json
import logging
import glob
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Application root directory
ROOT_DIR = Path(__file__).parent

# Kite API configuration
DEFAULT_KITE_USER = "satyam"  # Default user
# Template as string for proper formatting
KITE_CONFIG_FILE_TEMPLATE = "kite_config_{user_id}.json"
LEGACY_KITE_CONFIG_FILE = ROOT_DIR / "kite_config.json"  # For backward compatibility
DEFAULT_KITE_CONFIG = {
    "api_key": "",
    "api_secret": "",
    "access_token": "",
    "token_timestamp": ""
}

def get_kite_config_path(user_id=DEFAULT_KITE_USER):
    """Get the path to the Kite configuration file for a specific user"""
    # Format the string template first, then construct the path
    config_filename = KITE_CONFIG_FILE_TEMPLATE.format(user_id=user_id)
    return ROOT_DIR / config_filename

def load_kite_config(user_id=DEFAULT_KITE_USER):
    """Load Kite API configuration for a specific user"""
    try:
        config_file = get_kite_config_path(user_id)
        
        # Check if user-specific config exists
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded Kite configuration for user '{user_id}' from file")
                return config
        # Fall back to legacy config file for backward compatibility
        elif LEGACY_KITE_CONFIG_FILE.exists() and user_id == DEFAULT_KITE_USER:
            with open(LEGACY_KITE_CONFIG_FILE, "r") as f:
                config = json.load(f)
                logger.info(f"Loaded Kite configuration from legacy file")
                return config
        else:
            logger.warning(f"Kite config file not found for user '{user_id}', using defaults")
            return DEFAULT_KITE_CONFIG.copy()
    except Exception as e:
        logger.error(f"Error loading Kite configuration for user '{user_id}': {str(e)}")
        return DEFAULT_KITE_CONFIG.copy()

def save_kite_config(config, user_id=DEFAULT_KITE_USER):
    """Save Kite API configuration for a specific user"""
    try:
        config_file = get_kite_config_path(user_id)
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Saved Kite configuration for user '{user_id}' to file")
        
        # Also update legacy config if this is the default user (for backward compatibility)
        if user_id == DEFAULT_KITE_USER:
            with open(LEGACY_KITE_CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
            logger.info(f"Saved Kite configuration to legacy file for backward compatibility")
        
        return True
    except Exception as e:
        logger.error(f"Error saving Kite configuration for user '{user_id}': {str(e)}")
        return False

def update_kite_access_token(access_token, user_id=DEFAULT_KITE_USER):
    """Update Kite access token for a specific user"""
    try:
        config = load_kite_config(user_id)
        config["access_token"] = access_token
        config["token_timestamp"] = datetime.now().isoformat()
        return save_kite_config(config, user_id)
    except Exception as e:
        logger.error(f"Error updating Kite access token for user '{user_id}': {str(e)}")
        return False

def get_available_kite_users():
    """Get a list of available Kite users based on configuration files"""
    try:
        # Look for files matching the pattern
        pattern = str(ROOT_DIR / "kite_config_*.json")
        config_files = glob.glob(pattern)
        
        # Extract user IDs from file names
        user_ids = []
        for file_path in config_files:
            match = re.search(r'kite_config_(.+)\.json', file_path)
            if match:
                user_ids.append(match.group(1))
        
        # Ensure we have at least the default user
        if DEFAULT_KITE_USER not in user_ids and (
            LEGACY_KITE_CONFIG_FILE.exists() or 
            get_kite_config_path(DEFAULT_KITE_USER).exists()
        ):
            user_ids.append(DEFAULT_KITE_USER)
            
        logger.info(f"Found {len(user_ids)} Kite users: {', '.join(user_ids)}")
        return user_ids
    except Exception as e:
        logger.error(f"Error getting available Kite users: {str(e)}")
        return [DEFAULT_KITE_USER]  # Return at least the default user