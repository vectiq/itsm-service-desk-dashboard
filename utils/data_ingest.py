"""
MongoDB data ingest system for ITSM incident data
Pulls cleaned data from CSVs and seeds MongoDB collections
"""
import pymongo
import pandas as pd
import logging
from typing import Dict, List, Optional
import streamlit as st
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DataIngestManager:
    """Manages data ingestion from CSV files to MongoDB"""
    
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "itsm_app"):
        """Initialize MongoDB connection"""
        try:
            self.client = pymongo.MongoClient(mongo_uri)
            self.db = self.client[db_name]
            
            # Test connection
            self.client.admin.command('ping')
            self.available = True
            logger.info(f"Connected to MongoDB at {mongo_uri}")
            
            # Define collections
            self.incidents_collection = self.db.incidents
            self.agents_collection = self.db.agents
            self.workload_collection = self.db.workload
            self.metadata_collection = self.db.data_metadata
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.available = False
            st.error(f"MongoDB connection failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if MongoDB is available"""
        return self.available
    
    def check_data_exists(self) -> Dict[str, bool]:
        """Check which collections already have data"""
        if not self.available:
            return {}
        
        try:
            return {
                "incidents": self.incidents_collection.count_documents({}) > 0,
                "agents": self.agents_collection.count_documents({}) > 0,
                "workload": self.workload_collection.count_documents({}) > 0
            }
        except Exception as e:
            logger.error(f"Failed to check existing data: {str(e)}")
            return {}
    
    def get_data_stats(self) -> Dict[str, int]:
        """Get count of documents in each collection"""
        if not self.available:
            return {}
        
        try:
            return {
                "incidents": self.incidents_collection.count_documents({}),
                "agents": self.agents_collection.count_documents({}),
                "workload": self.workload_collection.count_documents({})
            }
        except Exception as e:
            logger.error(f"Failed to get data stats: {str(e)}")
            return {}
    
    def ingest_incidents_data(self, csv_path: str) -> bool:
        """Ingest incidents data from CSV"""
        if not self.available:
            return False
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Read {len(df)} incidents from {csv_path}")
            
            # Clean and prepare data
            df = self._clean_incidents_data(df)
            
            # Convert to records
            records = df.to_dict('records')
            
            # Add metadata
            for record in records:
                record['_ingested_at'] = datetime.utcnow()
                record['_source'] = os.path.basename(csv_path)
            
            # Clear existing data and insert new
            self.incidents_collection.delete_many({})
            result = self.incidents_collection.insert_many(records)
            
            logger.info(f"Inserted {len(result.inserted_ids)} incidents into MongoDB")
            
            # Update metadata
            self._update_metadata('incidents', len(records), csv_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest incidents data: {str(e)}")
            return False
    
    def ingest_agents_data(self, csv_path: str) -> bool:
        """Ingest agents data from CSV"""
        if not self.available:
            return False
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Read {len(df)} agents from {csv_path}")
            
            # Clean and prepare data
            df = self._clean_agents_data(df)
            
            # Convert to records
            records = df.to_dict('records')
            
            # Add metadata
            for record in records:
                record['_ingested_at'] = datetime.utcnow()
                record['_source'] = os.path.basename(csv_path)
            
            # Clear existing data and insert new
            self.agents_collection.delete_many({})
            result = self.agents_collection.insert_many(records)
            
            logger.info(f"Inserted {len(result.inserted_ids)} agents into MongoDB")
            
            # Update metadata
            self._update_metadata('agents', len(records), csv_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest agents data: {str(e)}")
            return False
    
    def ingest_workload_data(self, csv_path: str) -> bool:
        """Ingest workload data from CSV"""
        if not self.available:
            return False
        
        try:
            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"Read {len(df)} workload items from {csv_path}")
            
            # Clean and prepare data
            df = self._clean_workload_data(df)
            
            # Convert to records
            records = df.to_dict('records')
            
            # Add metadata
            for record in records:
                record['_ingested_at'] = datetime.utcnow()
                record['_source'] = os.path.basename(csv_path)
            
            # Clear existing data and insert new
            self.workload_collection.delete_many({})
            result = self.workload_collection.insert_many(records)
            
            logger.info(f"Inserted {len(result.inserted_ids)} workload items into MongoDB")
            
            # Update metadata
            self._update_metadata('workload', len(records), csv_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest workload data: {str(e)}")
            return False
    
    def _clean_incidents_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize incidents data with category enrichment"""
        # Convert datetime columns
        datetime_cols = ['created_on', 'updated_on', 'resolved_on']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Fill NaN values
        df = df.fillna('')

        # Ensure required columns exist
        required_cols = ['incident_id', 'short_description', 'description', 'true_priority']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''

        # Try to enrich with category names if category_tree.csv exists
        try:
            csv_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            category_file = os.path.join(csv_dir, "dummydata", "category_tree.csv")

            if os.path.exists(category_file):
                categories_df = pd.read_csv(category_file)
                if 'category_id' in df.columns and 'category_id' in categories_df.columns:
                    # Merge with categories to get category names
                    category_cols = ['category_id', 'name']
                    if 'path' in categories_df.columns:
                        category_cols.append('path')

                    df = df.merge(
                        categories_df[category_cols].rename(columns={'name': 'category_name'}),
                        on='category_id',
                        how='left'
                    )
                    logger.info("Enriched incidents with category names")
        except Exception as e:
            logger.warning(f"Could not enrich with categories: {str(e)}")

        # Try to enrich with service names if services_catalog.csv exists
        try:
            csv_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            services_file = os.path.join(csv_dir, "dummydata", "services_catalog.csv")

            if os.path.exists(services_file):
                services_df = pd.read_csv(services_file)
                if 'service_id' in df.columns and 'service_id' in services_df.columns:
                    # Merge with services to get service names
                    service_cols = ['service_id', 'name']
                    if 'criticality' in services_df.columns:
                        service_cols.append('criticality')

                    df = df.merge(
                        services_df[service_cols].rename(columns={'name': 'service_name'}),
                        on='service_id',
                        how='left'
                    )
                    logger.info("Enriched incidents with service names")
        except Exception as e:
            logger.warning(f"Could not enrich with services: {str(e)}")

        return df
    
    def _clean_agents_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize agents data"""
        # Fill NaN values
        df = df.fillna('')
        
        # Ensure required columns exist
        required_cols = ['user_id', 'name', 'email']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''
        
        return df
    
    def _clean_workload_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize workload data"""
        # Convert datetime columns
        datetime_cols = ['created_on', 'updated_on']
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Fill NaN values
        df = df.fillna('')
        
        return df
    
    def _update_metadata(self, collection_name: str, record_count: int, source_file: str):
        """Update metadata about the ingestion"""
        try:
            metadata = {
                "_id": f"{collection_name}_metadata",
                "collection": collection_name,
                "record_count": record_count,
                "source_file": source_file,
                "last_ingested": datetime.utcnow(),
                "status": "success"
            }
            
            self.metadata_collection.replace_one(
                {"_id": f"{collection_name}_metadata"},
                metadata,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Failed to update metadata: {str(e)}")
    
    def get_incidents(self, limit: Optional[int] = None) -> List[Dict]:
        """Get incidents from MongoDB"""
        if not self.available:
            return []
        
        try:
            cursor = self.incidents_collection.find({}, {"_ingested_at": 0, "_source": 0})
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get incidents: {str(e)}")
            return []
    
    def get_agents(self, limit: Optional[int] = None) -> List[Dict]:
        """Get agents from MongoDB"""
        if not self.available:
            return []
        
        try:
            cursor = self.agents_collection.find({}, {"_ingested_at": 0, "_source": 0})
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get agents: {str(e)}")
            return []
    
    def get_workload(self, limit: Optional[int] = None) -> List[Dict]:
        """Get workload from MongoDB"""
        if not self.available:
            return []
        
        try:
            cursor = self.workload_collection.find({}, {"_ingested_at": 0, "_source": 0})
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get workload: {str(e)}")
            return []

# Global instance
data_ingest_manager = DataIngestManager()
