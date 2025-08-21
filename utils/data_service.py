"""
Data service for accessing MongoDB data
Provides a unified interface for data access across the application
"""
import pandas as pd
import logging
from typing import Dict, Optional, List
from datetime import datetime
import streamlit as st
from utils.data_ingest import data_ingest_manager

logger = logging.getLogger(__name__)

class DataService:
    """MongoDB data service"""

    def __init__(self):
        """Initialize data service"""
        self._refresh_mongodb_status()

    def _refresh_mongodb_status(self):
        """Refresh MongoDB availability and data status"""
        self.use_mongodb = data_ingest_manager.is_available()

        if self.use_mongodb:
            # Check if MongoDB has data
            try:
                data_exists = data_ingest_manager.check_data_exists()
                self.mongodb_has_data = any(data_exists.values())

                if self.mongodb_has_data:
                    logger.info(f"MongoDB available with data: {data_exists}")
                else:
                    logger.warning("MongoDB available but no data found")
                    self.mongodb_has_data = False
            except Exception as e:
                logger.error(f"Error checking MongoDB data: {str(e)}")
                self.use_mongodb = False
                self.mongodb_has_data = False
        else:
            logger.error("MongoDB not available")
            self.mongodb_has_data = False
    
    def get_incidents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get incidents data from MongoDB"""
        try:
            # Refresh MongoDB status to catch newly ingested data
            self._refresh_mongodb_status()

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
                    logger.warning("No incidents found in MongoDB")
                    return pd.DataFrame()

            logger.error("MongoDB not available or has no data")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting incidents: {str(e)}")
            return pd.DataFrame()
    
    def get_agents(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get agents data from MongoDB"""
        try:
            # Refresh MongoDB status
            self._refresh_mongodb_status()

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
                    logger.warning("No agents found in MongoDB")
                    return pd.DataFrame()

            logger.error("MongoDB not available or has no data")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting agents: {str(e)}")
            return pd.DataFrame()
    
    def get_workload(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get current workload (unresolved unassigned incidents) from incidents collection"""
        try:
            # Refresh MongoDB status
            self._refresh_mongodb_status()

            if self.use_mongodb and self.mongodb_has_data:
                # Get unresolved incidents from MongoDB incidents collection
                incidents = data_ingest_manager.get_incidents(limit=None)  # Get all first, then filter
                if incidents:
                    df = pd.DataFrame(incidents)
                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)

                    # Filter for unresolved incidents only
                    if 'status' in df.columns:
                        unresolved_statuses = ['Open', 'In Progress', 'Assigned']
                        df = df[df['status'].isin(unresolved_statuses)]

                        # Further filter for unassigned incidents for the queue
                        if 'assigned_to' in df.columns:
                            df = df[(df['assigned_to'].isna()) | (df['assigned_to'] == '')]

                    # Apply limit after filtering
                    if limit and len(df) > limit:
                        df = df.head(limit)

                    logger.info(f"Loaded {len(df)} unresolved unassigned incidents from MongoDB")
                    return df
                else:
                    logger.warning("No incidents found in MongoDB")
                    return pd.DataFrame()

            logger.error("MongoDB not available or has no data")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting workload: {str(e)}")
            return pd.DataFrame()
    

    
    def get_data_source_info(self) -> Dict[str, str]:
        """Get information about current data source"""
        # Refresh MongoDB status
        self._refresh_mongodb_status()

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
                "source": "MongoDB",
                "status": "❌ Not Available",
                "incidents_count": "0",
                "agents_count": "0",
                "workload_count": "0"
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

            logger.error("MongoDB not available or has no data")
            return None

        except Exception as e:
            logger.error(f"Error getting incident {incident_id}: {str(e)}")
            return None

    def update_incident_priority(self, incident_id: str, priority: str) -> bool:
        """Update the priority of a specific incident"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Update in MongoDB
                result = data_ingest_manager.incidents_collection.update_one(
                    {"incident_id": incident_id},
                    {
                        "$set": {
                            "priority": priority,
                            "true_priority": priority,  # Update both fields for compatibility
                            "_updated_at": datetime.utcnow()
                        }
                    }
                )

                if result.modified_count > 0:
                    logger.info(f"Updated priority for incident {incident_id} to {priority}")
                    return True
                else:
                    logger.warning(f"No incident found with ID {incident_id} for priority update")
                    return False
            else:
                logger.error("MongoDB not available or has no data")
                return False

        except Exception as e:
            logger.error(f"Error updating incident priority: {str(e)}")
            return False

    def update_incident_assignment(self, incident_id: str, assigned_to: str) -> bool:
        """Update the assigned agent of a specific incident"""
        try:
            if self.use_mongodb and self.mongodb_has_data:
                # Update in MongoDB
                update_data = {
                    "assigned_to": assigned_to,
                    "_updated_at": datetime.utcnow()
                }

                # If assigning to someone, also update status to 'Assigned' if it's currently 'Open'
                incident = self.get_incident_by_id(incident_id)
                if incident and incident.get('status') == 'Open':
                    update_data["status"] = "Assigned"

                result = data_ingest_manager.incidents_collection.update_one(
                    {"incident_id": incident_id},
                    {"$set": update_data}
                )

                if result.modified_count > 0:
                    logger.info(f"Updated assignment for incident {incident_id} to {assigned_to}")
                    return True
                else:
                    logger.warning(f"No incident found with ID {incident_id} for assignment update")
                    return False
            else:
                logger.error("MongoDB not available or has no data")
                return False

        except Exception as e:
            logger.error(f"Error updating incident assignment: {str(e)}")
            return False
    
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
