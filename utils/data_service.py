"""
Data service for accessing MongoDB data with fallback to CSV
Provides a unified interface for data access across the application
"""
import pandas as pd
import logging
from typing import Dict, Optional, List
import streamlit as st
from utils.data_ingest import data_ingest_manager
from utils.data_loader import ensure_data_loaded

logger = logging.getLogger(__name__)

class DataService:
    """Unified data service with MongoDB primary, CSV fallback"""
    
    def __init__(self):
        """Initialize data service"""
        self.use_mongodb = data_ingest_manager.is_available()
        self.csv_data = None
        
        if self.use_mongodb:
            # Check if MongoDB has data
            data_exists = data_ingest_manager.check_data_exists()
            self.mongodb_has_data = any(data_exists.values())
            
            if not self.mongodb_has_data:
                logger.info("MongoDB available but no data found, will use CSV fallback")
                self.use_mongodb = False
        else:
            logger.info("MongoDB not available, using CSV data")
            self.mongodb_has_data = False
    
    def get_incidents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get incidents data from MongoDB or CSV"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Get from MongoDB
                incidents = data_ingest_manager.get_incidents(limit=limit)
                if incidents:
                    df = pd.DataFrame(incidents)
                    # Remove MongoDB _id field
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)
                    logger.info(f"Loaded {len(df)} incidents from MongoDB")
                    return df
                else:
                    logger.warning("No incidents found in MongoDB, falling back to CSV")
            
            # Fallback to CSV
            return self._get_csv_incidents(limit)
            
        except Exception as e:
            logger.error(f"Error getting incidents: {str(e)}")
            # Fallback to CSV on error
            return self._get_csv_incidents(limit)
    
    def get_agents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get agents data from MongoDB or CSV"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Get from MongoDB
                agents = data_ingest_manager.get_agents(limit=limit)
                if agents:
                    df = pd.DataFrame(agents)
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)
                    logger.info(f"Loaded {len(df)} agents from MongoDB")
                    return df
                else:
                    logger.warning("No agents found in MongoDB, falling back to CSV")
            
            # Fallback to CSV
            return self._get_csv_agents(limit)
            
        except Exception as e:
            logger.error(f"Error getting agents: {str(e)}")
            return self._get_csv_agents(limit)
    
    def get_workload(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get workload data from MongoDB or CSV"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Get from MongoDB
                workload = data_ingest_manager.get_workload(limit=limit)
                if workload:
                    df = pd.DataFrame(workload)
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)
                    logger.info(f"Loaded {len(df)} workload items from MongoDB")
                    return df
                else:
                    logger.warning("No workload found in MongoDB, falling back to CSV")
            
            # Fallback to CSV
            return self._get_csv_workload(limit)
            
        except Exception as e:
            logger.error(f"Error getting workload: {str(e)}")
            return self._get_csv_workload(limit)
    
    def _get_csv_incidents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get incidents from CSV files"""
        try:
            if self.csv_data is None:
                self.csv_data = ensure_data_loaded()
            
            # Get incidents with categories (the cleaned data we show in tables)
            df = self.csv_data.get("incidents_with_categories.csv", pd.DataFrame())
            
            if limit and len(df) > limit:
                df = df.head(limit)
            
            logger.info(f"Loaded {len(df)} incidents from CSV")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV incidents: {str(e)}")
            return pd.DataFrame()
    
    def _get_csv_agents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get agents from CSV files"""
        try:
            if self.csv_data is None:
                self.csv_data = ensure_data_loaded()
            
            df = self.csv_data.get("users_agents.csv", pd.DataFrame())
            
            if limit and len(df) > limit:
                df = df.head(limit)
            
            logger.info(f"Loaded {len(df)} agents from CSV")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV agents: {str(e)}")
            return pd.DataFrame()
    
    def _get_csv_workload(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get workload from CSV files"""
        try:
            if self.csv_data is None:
                self.csv_data = ensure_data_loaded()
            
            df = self.csv_data.get("workload_queue.csv", pd.DataFrame())
            
            if limit and len(df) > limit:
                df = df.head(limit)
            
            logger.info(f"Loaded {len(df)} workload items from CSV")
            return df
            
        except Exception as e:
            logger.error(f"Error loading CSV workload: {str(e)}")
            return pd.DataFrame()
    
    def get_data_source_info(self) -> Dict[str, str]:
        """Get information about current data source"""
        if self.use_mongodb and self.mongodb_has_data:
            stats = data_ingest_manager.get_data_stats()
            return {
                "source": "MongoDB",
                "status": "✅ Connected",
                "incidents_count": f"{stats.get('incidents', 0):,}",
                "agents_count": f"{stats.get('agents', 0):,}",
                "workload_count": f"{stats.get('workload', 0):,}"
            }
        else:
            return {
                "source": "CSV Files",
                "status": "📄 File-based",
                "incidents_count": "Variable",
                "agents_count": "Variable", 
                "workload_count": "Variable"
            }
    
    def refresh_data_source(self):
        """Refresh data source availability"""
        self.__init__()
    
    def search_incidents(self, query: str, limit: int = 100) -> pd.DataFrame:
        """Search incidents by text query"""
        try:
            df = self.get_incidents(limit=None)  # Get all for search
            
            if df.empty:
                return df
            
            # Search in title and description columns
            search_cols = ['short_description', 'description']
            mask = pd.Series([False] * len(df))
            
            for col in search_cols:
                if col in df.columns:
                    mask |= df[col].astype(str).str.contains(query, case=False, na=False)
            
            result = df[mask]
            
            if limit and len(result) > limit:
                result = result.head(limit)
            
            logger.info(f"Found {len(result)} incidents matching '{query}'")
            return result
            
        except Exception as e:
            logger.error(f"Error searching incidents: {str(e)}")
            return pd.DataFrame()
    
    def get_incident_by_id(self, incident_id: str) -> Optional[Dict]:
        """Get a specific incident by ID"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Search in MongoDB
                incident = data_ingest_manager.incidents_collection.find_one(
                    {"incident_id": incident_id},
                    {"_id": 0, "_ingested_at": 0, "_source": 0}
                )
                if incident:
                    return incident
            
            # Fallback to CSV
            df = self.get_incidents()
            if not df.empty and 'incident_id' in df.columns:
                matches = df[df['incident_id'] == incident_id]
                if not matches.empty:
                    return matches.iloc[0].to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting incident {incident_id}: {str(e)}")
            return None
    
    def get_incidents_by_priority(self, priority: str) -> pd.DataFrame:
        """Get incidents filtered by priority"""
        try:
            df = self.get_incidents()
            
            if df.empty or 'true_priority' not in df.columns:
                return df
            
            return df[df['true_priority'] == priority]
            
        except Exception as e:
            logger.error(f"Error filtering incidents by priority {priority}: {str(e)}")
            return pd.DataFrame()
    
    def get_incidents_by_category(self, category: str) -> pd.DataFrame:
        """Get incidents filtered by category"""
        try:
            df = self.get_incidents()
            
            if df.empty or 'category_name' not in df.columns:
                return df
            
            return df[df['category_name'] == category]
            
        except Exception as e:
            logger.error(f"Error filtering incidents by category {category}: {str(e)}")
            return pd.DataFrame()

# Global instance
data_service = DataService()
