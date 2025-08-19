"""
MongoDB data ingest system for ITSM incident data
Pulls cleaned data from CSVs and seeds MongoDB collections
"""
import pymongo
import pandas as pd
import logging
from typing import Dict, List, Optional
import streamlit as st
from datetime import datetime, timedelta
import os
import random

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

    def _generate_past_datetime(self, days_back: int = 30) -> str:
        """Generate a random datetime in the past"""
        days_ago = random.randint(1, days_back)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)

        past_time = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        return past_time.strftime('%Y-%m-%d %H:%M:%S')

    def _generate_future_datetime(self, hours_ahead: int = 24) -> str:
        """Generate a random datetime in the future"""
        hours_forward = random.randint(1, hours_ahead)
        minutes_forward = random.randint(0, 59)

        future_time = datetime.utcnow() + timedelta(hours=hours_forward, minutes=minutes_forward)
        return future_time.strftime('%Y-%m-%d %H:%M:%S')

    def generate_ai_incidents(self, count: int = 100, resolved_percentage: float = 0.7, model_id: str = None, max_tokens: int = None, temperature: float = None) -> bool:
        """Generate realistic incidents using AI, with mix of resolved and unresolved"""
        if not self.available:
            return False

        try:
            from utils.bedrock_client import bedrock_client

            if not bedrock_client.is_available():
                logger.error("Bedrock client not available for AI incident generation")
                return False

            logger.info(f"Generating {count} AI-powered incidents...")

            # Calculate counts
            resolved_count = int(count * resolved_percentage)
            unresolved_count = count - resolved_count

            all_incidents = []

            # Generate resolved incidents
            if resolved_count > 0:
                resolved_incidents = self._generate_ai_incidents_batch(
                    bedrock_client, resolved_count, status_type='resolved',
                    model_id=model_id, max_tokens=max_tokens, temperature=temperature
                )
                all_incidents.extend(resolved_incidents)

            # Generate unresolved incidents
            if unresolved_count > 0:
                unresolved_incidents = self._generate_ai_incidents_batch(
                    bedrock_client, unresolved_count, status_type='unresolved',
                    model_id=model_id, max_tokens=max_tokens, temperature=temperature
                )
                all_incidents.extend(unresolved_incidents)

            # Clear existing incidents and insert new ones
            self.incidents_collection.delete_many({})

            # Also clear workload collection since we're consolidating
            self.workload_collection.delete_many({})

            if all_incidents:
                result = self.incidents_collection.insert_many(all_incidents)
                logger.info(f"Generated and inserted {len(result.inserted_ids)} AI incidents")

                # Update metadata
                self._update_metadata('incidents', len(all_incidents), 'ai_generated')

                return True
            else:
                logger.error("No incidents were generated")
                return False

        except Exception as e:
            logger.error(f"Failed to generate AI incidents: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _generate_ai_incidents_batch(self, bedrock_client, count: int, status_type: str, model_id: str = None, max_tokens: int = None, temperature: float = None) -> List[Dict]:
        """Generate a batch of incidents using AI"""
        incidents = []

        # Generate incidents in smaller batches to avoid token limits
        batch_size = 10
        batches = (count + batch_size - 1) // batch_size

        for batch_num in range(batches):
            batch_count = min(batch_size, count - batch_num * batch_size)

            if batch_count <= 0:
                break

            try:
                batch_incidents = self._generate_ai_batch(
                    bedrock_client, batch_count, status_type,
                    model_id=model_id, max_tokens=max_tokens, temperature=temperature
                )
                incidents.extend(batch_incidents)
                logger.info(f"Generated batch {batch_num + 1}/{batches} ({len(batch_incidents)} incidents)")

            except Exception as e:
                error_msg = f"Failed to generate batch {batch_num + 1}: {str(e)}"
                logger.error(error_msg)
                # Re-raise the exception to propagate it up for debugging
                raise Exception(f"Batch generation failed: {error_msg}")

        return incidents

    def _generate_ai_batch(self, bedrock_client, count: int, status_type: str, model_id: str = None, max_tokens: int = None, temperature: float = None) -> List[Dict]:
        """Generate a single batch of incidents using AI"""

        # Use provided model settings or fallback to defaults
        if not model_id:
            # Fallback to global settings if no model provided
            from utils.settings_manager import settings_manager
            ai_settings = settings_manager.get_ai_model_settings()
            model_id = ai_settings.get("selected_model_id")

            if not model_id:
                model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
                logger.warning("No model configured, using Claude Sonnet as fallback")

        if temperature is None:
            temperature = 0.7

        if max_tokens is None:
            # Default token allocation for incident generation - optimized for batches of 10
            max_tokens = max(3000, min(count, 10) * 300)  # Minimum 3000, or 300 per incident (max 10 per batch)

        # Create prompt for AI generation
        if status_type == 'resolved':
            status_prompt = """Generate RESOLVED incidents with:
- Status: "Resolved"
- Resolution details: resolution_code, resolved_on (within last 30 days), resolution_notes
- Realistic resolution times based on priority
- IMPORTANT: resolution_notes should vary dramatically in quality and detail:
  * Lazy agents: "fixed", "done", "sorted", "working now", "resolved"
  * Average agents: "Reset password", "Restarted service", "Updated driver"
  * Diligent agents: Detailed technical explanations with steps taken, root cause analysis, and preventive measures"""
        else:
            status_prompt = """Generate UNRESOLVED incidents with:
- Status: "Open", "In Progress", or "Assigned"
- No resolution details (empty resolution_code, resolved_on, resolution_notes)
- Some assigned to agents (AGT001-AGT010), some unassigned"""

        prompt = f"""Generate exactly {count} realistic ICT service desk incidents in JSON format. CRITICAL: You must generate exactly {count} incidents, no more, no less. {status_prompt}

Each incident should have these exact fields:
- incident_id: Format INC#### (sequential numbers)
- title: Concise problem description
- description: Detailed technical description
- priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)
- status: Based on type above
- category: Choose from "Password Reset", "VPN Issues", "Multi-Factor Authentication", "Printer Support", "Email Problems", "WiFi Connectivity", "Software Installation", "File Share Access", "Phone System", "Hardware Failure", "Application Error", "Account Lockout", "Network Connectivity", "System Performance"
- service: Choose from "Workplace Technology", "Network Services", "Collaboration Tools", "Security Services", "Infrastructure"
- urgency: Low, Medium, High, Critical
- impact: Low, Medium, High, Critical
- location: Sydney, Melbourne, Brisbane, Perth, Adelaide
- channel: Phone, Email, Portal, Chat, Walk-in
- assigned_to: For unresolved: mix of empty and AGT001-AGT010. For resolved: AGT001-AGT010
- created_on: YYYY-MM-DD HH:MM:SS format (last 30 days)
- sla_due: YYYY-MM-DD HH:MM:SS format (future for unresolved, past for resolved)
- customer_id: USR#### format
- resolution_code: For resolved: "Fixed", "Workaround", "User Error", "Duplicate". For unresolved: empty
- resolved_on: For resolved: YYYY-MM-DD HH:MM:SS. For unresolved: empty
- resolution_notes: For resolved: Vary quality dramatically - Examples:
  * Lazy: "fixed", "done", "sorted", "working now"
  * Average: "Reset user password", "Restarted print spooler service", "Updated network driver"
  * Detailed: "Issue caused by corrupted user profile. Backed up user data, created new profile, restored data and settings. Tested all applications. Advised user on profile maintenance best practices to prevent recurrence."
  For unresolved: empty

Focus on common ICT issues: password resets, VPN problems, email issues, printer troubles, software installations, hardware failures, network connectivity, application errors, account lockouts, file access problems.

IMPORTANT: Return ONLY a JSON array with exactly {count} incident objects. Do not include any markdown formatting, code blocks, or additional text. The response must be valid JSON that can be parsed directly."""

        try:
            logger.info(f"Generating {count} {status_type} incidents using model: {model_id}")
            logger.info(f"Model settings: max_tokens={max_tokens}, temperature={temperature}")
            logger.debug(f"Prompt length: {len(prompt)} characters")

            response = bedrock_client.invoke_model(
                prompt=prompt,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if not response:
                error_msg = "No response from Bedrock"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.debug(f"Received response length: {len(response)} characters")

            # Parse JSON response - handle markdown code blocks
            import json
            import re
            try:
                # Clean the response - remove markdown code blocks if present
                cleaned_response = response.strip()

                # Remove ```json and ``` markers if present
                if cleaned_response.startswith('```json'):
                    cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
                if cleaned_response.startswith('```'):
                    cleaned_response = re.sub(r'^```\s*', '', cleaned_response)
                if cleaned_response.endswith('```'):
                    cleaned_response = re.sub(r'\s*```$', '', cleaned_response)

                logger.debug(f"Cleaned response preview: {cleaned_response[:200]}...")

                incidents_data = json.loads(cleaned_response)
                if not isinstance(incidents_data, list):
                    error_msg = f"Response is not a JSON array, got: {type(incidents_data)}"
                    logger.error(error_msg)
                    logger.error(f"Cleaned response content: {cleaned_response[:1000]}...")
                    raise Exception(error_msg)

                logger.info(f"Successfully parsed {len(incidents_data)} incidents from AI response")

                # Process and validate each incident
                processed_incidents = []
                for i, incident in enumerate(incidents_data):
                    processed_incident = self._process_ai_incident(incident, i, status_type)
                    if processed_incident:
                        processed_incidents.append(processed_incident)
                    else:
                        logger.warning(f"Failed to process incident {i}: {incident}")

                logger.info(f"Successfully processed {len(processed_incidents)} out of {len(incidents_data)} incidents")
                return processed_incidents

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Original response was: {response[:1000]}...")
                logger.error(f"Cleaned response was: {cleaned_response[:1000]}...")
                raise Exception(f"{error_msg}. Cleaned response preview: {cleaned_response[:200]}...")

        except Exception as e:
            error_msg = f"Error in AI batch generation: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _process_ai_incident(self, incident_data: Dict, index: int, status_type: str) -> Optional[Dict]:
        """Process and validate a single AI-generated incident"""
        try:
            # Generate unique incident ID if not provided or invalid
            base_id = 1000 + (int(datetime.utcnow().timestamp()) % 10000) + index
            incident_id = incident_data.get('incident_id', f'INC{base_id:04d}')

            # Ensure incident_id format
            if not incident_id.startswith('INC'):
                incident_id = f'INC{base_id:04d}'

            # Build the incident record with readable field names
            record = {
                'incident_id': incident_id,
                'title': incident_data.get('title', 'IT Support Request'),
                'description': incident_data.get('description', 'User requires technical assistance'),
                'priority': incident_data.get('priority', 'P3'),
                'status': incident_data.get('status', 'Open'),
                'category': incident_data.get('category', 'Password Reset'),  # Now readable name
                'service': incident_data.get('service', 'Workplace Technology'),  # Now readable name
                'urgency': incident_data.get('urgency', 'Medium'),
                'impact': incident_data.get('impact', 'Medium'),
                'location': incident_data.get('location', 'Sydney'),
                'channel': incident_data.get('channel', 'Email'),
                'assigned_to': incident_data.get('assigned_to', ''),
                'created_on': incident_data.get('created_on', self._generate_past_datetime(30)),
                'sla_due': incident_data.get('sla_due', self._generate_future_datetime(24)),
                'customer_id': incident_data.get('customer_id', f'USR{random.randint(1001, 1999)}'),
                'resolution_code': incident_data.get('resolution_code', ''),
                'resolved_on': incident_data.get('resolved_on', ''),
                'resolution_notes': incident_data.get('resolution_notes', ''),
                '_ingested_at': datetime.utcnow(),
                '_source': 'ai_generated'
            }

            # Validate status-specific fields
            if status_type == 'resolved':
                if not record['resolution_code']:
                    record['resolution_code'] = random.choice(['Fixed', 'Workaround', 'User Error', 'Duplicate'])
                if not record['resolved_on']:
                    record['resolved_on'] = self._generate_past_datetime(30)
                if not record['resolution_notes']:
                    record['resolution_notes'] = 'Issue resolved successfully'
                if not record['assigned_to']:
                    record['assigned_to'] = f'AGT{random.randint(1, 10):03d}'
                record['status'] = 'Resolved'
            else:
                # Unresolved incidents
                record['resolution_code'] = ''
                record['resolved_on'] = ''
                record['resolution_notes'] = ''
                if record['status'] not in ['Open', 'In Progress', 'Assigned']:
                    record['status'] = random.choice(['Open', 'In Progress', 'Assigned'])
                # Some unassigned
                if random.random() < 0.3:  # 30% unassigned
                    record['assigned_to'] = ''
                elif not record['assigned_to']:
                    record['assigned_to'] = f'AGT{random.randint(1, 10):03d}'

            return record

        except Exception as e:
            logger.error(f"Error processing AI incident: {str(e)}")
            return None

# Global instance
data_ingest_manager = DataIngestManager()
