"""Configuration management for the application"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Application root directory
ROOT_DIR = Path(__file__).parent

# Kite API configuration
KITE_CONFIG_FILE = ROOT_DIR / "kite_config.json"
DEFAULT_KITE_CONFIG = {
    "api_key": "",
    "api_secret": "",
    "access_token": "",
    "token_timestamp": ""
}

def load_kite_config():
    """Load Kite API configuration"""
    try:
        if KITE_CONFIG_FILE.exists():
            with open(KITE_CONFIG_FILE, "r") as f:
                config = json.load(f)
                logger.info("Loaded Kite configuration from file")
                return config
        else:
            logger.warning(f"Kite config file not found at {KITE_CONFIG_FILE}, using defaults")
            return DEFAULT_KITE_CONFIG.copy()
    except Exception as e:
        logger.error(f"Error loading Kite configuration: {str(e)}")
        return DEFAULT_KITE_CONFIG.copy()

def save_kite_config(config):
    """Save Kite API configuration"""
    try:
        with open(KITE_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        logger.info("Saved Kite configuration to file")
        return True
    except Exception as e:
        logger.error(f"Error saving Kite configuration: {str(e)}")
        return False

def update_kite_access_token(access_token):
    """Update Kite access token"""
    try:
        config = load_kite_config()
        config["access_token"] = access_token
        config["token_timestamp"] = datetime.now().isoformat()
        return save_kite_config(config)
    except Exception as e:
        logger.error(f"Error updating Kite access token: {str(e)}")
        return False
