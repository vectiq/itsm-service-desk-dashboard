"""
MongoDB-based settings manager for persistent global configuration
"""
import pymongo
import logging
from typing import Dict, Any, Optional
import streamlit as st

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages global application settings using MongoDB"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "itsm_app"):
        """Initialize MongoDB connection"""
        try:
            self.client = pymongo.MongoClient(mongo_uri)
            self.db = self.client[db_name]
            self.settings_collection = self.db.global_settings
            
            # Test connection
            self.client.admin.command('ping')
            self.available = True
            logger.info(f"Connected to MongoDB at {mongo_uri}")
            
            # Initialize default settings if not exists
            self._initialize_defaults()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.available = False
            st.error(f"MongoDB connection failed: {str(e)}")
    
    def _initialize_defaults(self):
        """Initialize default settings if they don't exist"""
        if not self.available:
            return
            
        try:
            # Check if settings exist
            existing = self.settings_collection.find_one({"_id": "global_config"})
            
            if not existing:
                default_settings = {
                    "_id": "global_config",
                    "ai_model": {
                        "selected_model_id": None,
                        "selected_model_name": None,
                        "max_tokens": 1000,
                        "temperature": 0.7
                    },
                    "system_prompts": {
                        "incident_triage": "You are an expert ITSM analyst specializing in incident classification and priority assessment. You have deep knowledge of IT infrastructure, business impact analysis, and service level agreements.",
                        "kb_generation": "You are a technical documentation specialist with expertise in creating clear, actionable knowledge base articles. You excel at transforming incident resolution patterns into structured, searchable documentation.",
                        "agent_assignment": "You are an ITSM resource allocation expert with deep understanding of skill matching, workload balancing, and performance optimization for technical support teams."
                    },
                    "ui_preferences": {
                        "theme": "light",
                        "default_page": "dashboard"
                    }
                }
                
                self.settings_collection.insert_one(default_settings)
                logger.info("Initialized default settings in MongoDB")
                
        except Exception as e:
            logger.error(f"Failed to initialize default settings: {str(e)}")
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation
        Example: get_setting("ai_model.selected_model_id")
        """
        if not self.available:
            return default
            
        try:
            settings = self.settings_collection.find_one({"_id": "global_config"})
            if not settings:
                return default
            
            # Navigate nested keys
            keys = key_path.split('.')
            value = settings
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            logger.error(f"Failed to get setting {key_path}: {str(e)}")
            return default
    
    def set_setting(self, key_path: str, value: Any) -> bool:
        """
        Set a setting value using dot notation
        Example: set_setting("ai_model.selected_model_id", "claude-3-5-sonnet")
        """
        if not self.available:
            return False
            
        try:
            keys = key_path.split('.')
            
            # Build the update query for nested fields
            update_query = {}
            current = update_query
            for i, key in enumerate(keys):
                if i == len(keys) - 1:
                    current[key] = value
                else:
                    current[key] = {}
                    current = current[key]
            
            # Use $set to update nested field
            flattened = self._flatten_dict(update_query)
            mongo_update = {"$set": flattened}

            result = self.settings_collection.update_one(
                {"_id": "global_config"},
                mongo_update,
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to set setting {key_path}: {str(e)}")
            return False
    
    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '.'):
        """Flatten nested dictionary for MongoDB update"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        if not self.available:
            return {}
            
        try:
            settings = self.settings_collection.find_one({"_id": "global_config"})
            if settings:
                # Remove MongoDB _id field
                settings.pop('_id', None)
                return settings
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get all settings: {str(e)}")
            return {}
    
    def update_ai_model_settings(self, model_id: str, model_name: str, max_tokens: int, temperature: float) -> bool:
        """Update AI model settings"""
        try:
            update_data = {
                "ai_model.selected_model_id": model_id,
                "ai_model.selected_model_name": model_name,
                "ai_model.max_tokens": max_tokens,
                "ai_model.temperature": temperature
            }
            
            mongo_update = {"$set": update_data}
            result = self.settings_collection.update_one(
                {"_id": "global_config"},
                mongo_update,
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            logger.error(f"Failed to update AI model settings: {str(e)}")
            return False
    
    def update_system_prompt(self, use_case: str, prompt: str) -> bool:
        """Update system prompt for a specific use case"""
        return self.set_setting(f"system_prompts.{use_case}", prompt)
    
    def get_ai_model_settings(self) -> Dict[str, Any]:
        """Get AI model settings"""
        return {
            "selected_model_id": self.get_setting("ai_model.selected_model_id"),
            "selected_model_name": self.get_setting("ai_model.selected_model_name"),
            "max_tokens": self.get_setting("ai_model.max_tokens", 1000),
            "temperature": self.get_setting("ai_model.temperature", 0.7)
        }
    
    def get_system_prompts(self) -> Dict[str, str]:
        """Get all system prompts"""
        return self.get_setting("system_prompts", {})
    
    def is_available(self) -> bool:
        """Check if MongoDB is available"""
        return self.available

# Global instance
settings_manager = SettingsManager()
