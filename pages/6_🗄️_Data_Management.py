"""
Data Management page for MongoDB data ingestion and management
"""
import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_ingest import data_ingest_manager
from utils.data_loader import ensure_data_loaded

st.set_page_config(page_title="Data Management", page_icon="🗄️", layout="wide")
st.title("🗄️ Data Management")

# Check MongoDB availability
if not data_ingest_manager.is_available():
    st.error("🚫 MongoDB is not available. Please check your MongoDB connection.")
    st.info("Make sure MongoDB is running on localhost:27017")
    st.stop()

# Get current data status
data_exists = data_ingest_manager.check_data_exists()
data_stats = data_ingest_manager.get_data_stats()

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📊 Current Data Status")
    
    # Show current status
    for collection, exists in data_exists.items():
        count = data_stats.get(collection, 0)
        if exists:
            st.success(f"✅ **{collection.title()}**: {count:,} records")
        else:
            st.warning(f"⚠️ **{collection.title()}**: No data")
    
    # Show last ingestion info
    st.subheader("📅 Last Ingestion")
    try:
        metadata_cursor = data_ingest_manager.metadata_collection.find({})
        metadata_list = list(metadata_cursor)
        
        if metadata_list:
            for meta in metadata_list:
                collection_name = meta.get('collection', 'Unknown')
                last_ingested = meta.get('last_ingested', 'Unknown')
                source_file = meta.get('source_file', 'Unknown')
                record_count = meta.get('record_count', 0)
                
                if isinstance(last_ingested, datetime):
                    last_ingested_str = last_ingested.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    last_ingested_str = str(last_ingested)
                
                st.info(f"**{collection_name.title()}**: {record_count:,} records from `{source_file}` at {last_ingested_str}")
        else:
            st.info("No ingestion history found")
            
    except Exception as e:
        st.error(f"Error reading metadata: {str(e)}")

with col2:
    st.header("🔄 Data Ingestion")

    # CSV directory configuration
    st.subheader("📁 CSV Data Directory")

    # Default to dummydata folder
    default_csv_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dummydata")

    dir_col1, dir_col2 = st.columns([3, 1])

    with dir_col1:
        csv_directory = st.text_input(
            "CSV Directory Path:",
            value=default_csv_dir,
            help="Path to directory containing CSV files for ingestion"
        )

    with dir_col2:
        st.write("")  # Spacing
        if st.button("🔄 Refresh", help="Refresh directory contents"):
            st.rerun()

    # Validate directory exists
    if not os.path.exists(csv_directory):
        st.error(f"❌ Directory does not exist: `{csv_directory}`")
        st.stop()

    st.success(f"✅ Directory found: `{csv_directory}`")

    # Show available files in the directory
    st.write("**Expected CSV Files:**")
    try:
        # Define expected CSV files with descriptions
        csv_files = {
            "incidents": {
                "filename": "incidents_resolved.csv",
                "description": "Main incidents data with categories, priorities, and resolution info"
            },
            "agents": {
                "filename": "users_agents.csv",
                "description": "User and agent information with contact details"
            },
            "workload": {
                "filename": "workload_queue.csv",
                "description": "Current workload and assignment queue data"
            }
        }

        for data_type, file_info in csv_files.items():
            filename = file_info["filename"]
            description = file_info["description"]
            file_path = os.path.join(csv_directory, filename)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / 1024  # KB
                # Count rows
                try:
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    row_count = len(df)
                    st.write(f"📄 **{data_type.title()}**: `{filename}` ({file_size:.1f} KB, {row_count:,} rows)")
                    st.caption(f"   {description}")
                except Exception:
                    st.write(f"📄 **{data_type.title()}**: `{filename}` ({file_size:.1f} KB)")
                    st.caption(f"   {description}")
            else:
                st.write(f"❌ **{data_type.title()}**: `{filename}` (Not found)")
                st.caption(f"   {description}")

    except Exception as e:
        st.error(f"Error checking CSV files: {str(e)}")

    st.write("---")
    
    # Ingestion controls
    st.subheader("🚀 Ingest Data")
    
    # Warning about data replacement
    if any(data_exists.values()):
        st.warning("⚠️ **Warning**: Ingestion will replace existing data in MongoDB!")
    
    # Ingest buttons
    ingest_col1, ingest_col2 = st.columns(2)
    
    with ingest_col1:
        if st.button("📥 Ingest Incidents", type="primary"):
            incidents_file = os.path.join(csv_directory, "incidents_resolved.csv")
            if os.path.exists(incidents_file):
                with st.spinner("Ingesting incidents data..."):
                    success = data_ingest_manager.ingest_incidents_data(incidents_file)
                    if success:
                        st.success("✅ Incidents data ingested successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to ingest incidents data")
            else:
                st.error(f"❌ File not found: {incidents_file}")

        if st.button("👥 Ingest Agents"):
            agents_file = os.path.join(csv_directory, "users_agents.csv")
            if os.path.exists(agents_file):
                with st.spinner("Ingesting agents data..."):
                    success = data_ingest_manager.ingest_agents_data(agents_file)
                    if success:
                        st.success("✅ Agents data ingested successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to ingest agents data")
            else:
                st.error(f"❌ File not found: {agents_file}")

    with ingest_col2:
        if st.button("📋 Ingest Workload"):
            workload_file = os.path.join(csv_directory, "workload_queue.csv")
            if os.path.exists(workload_file):
                with st.spinner("Ingesting workload data..."):
                    success = data_ingest_manager.ingest_workload_data(workload_file)
                    if success:
                        st.success("✅ Workload data ingested successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to ingest workload data")
            else:
                st.error(f"❌ File not found: {workload_file}")

        if st.button("🔄 Ingest All Data", type="secondary"):
            with st.spinner("Ingesting all data..."):
                results = []
                files_to_ingest = [
                    ("incidents", "incidents_resolved.csv", data_ingest_manager.ingest_incidents_data),
                    ("agents", "users_agents.csv", data_ingest_manager.ingest_agents_data),
                    ("workload", "workload_queue.csv", data_ingest_manager.ingest_workload_data)
                ]

                for data_type, filename, ingest_func in files_to_ingest:
                    file_path = os.path.join(csv_directory, filename)
                    if os.path.exists(file_path):
                        st.write(f"Ingesting {data_type}...")
                        results.append(ingest_func(file_path))
                    else:
                        st.error(f"❌ File not found: {file_path}")
                        results.append(False)

                if all(results):
                    st.success("✅ All data ingested successfully!")
                    st.rerun()
                else:
                    st.error("❌ Some data ingestion failed")

# Data preview section
st.header("👀 Data Preview")

preview_tabs = st.tabs(["🎫 Incidents", "👥 Agents", "📋 Workload"])

with preview_tabs[0]:
    if data_exists.get("incidents", False):
        st.write(f"**Showing first 10 incidents** (Total: {data_stats.get('incidents', 0):,})")
        try:
            incidents = data_ingest_manager.get_incidents(limit=10)
            if incidents:
                # Convert to DataFrame for display
                df = pd.DataFrame(incidents)
                # Remove MongoDB _id field for cleaner display
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No incidents data found")
        except Exception as e:
            st.error(f"Error loading incidents: {str(e)}")
    else:
        st.info("No incidents data in MongoDB. Use the ingestion controls above to load data.")

with preview_tabs[1]:
    if data_exists.get("agents", False):
        st.write(f"**Showing first 10 agents** (Total: {data_stats.get('agents', 0):,})")
        try:
            agents = data_ingest_manager.get_agents(limit=10)
            if agents:
                df = pd.DataFrame(agents)
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No agents data found")
        except Exception as e:
            st.error(f"Error loading agents: {str(e)}")
    else:
        st.info("No agents data in MongoDB. Use the ingestion controls above to load data.")

with preview_tabs[2]:
    if data_exists.get("workload", False):
        st.write(f"**Showing first 10 workload items** (Total: {data_stats.get('workload', 0):,})")
        try:
            workload = data_ingest_manager.get_workload(limit=10)
            if workload:
                df = pd.DataFrame(workload)
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No workload data found")
        except Exception as e:
            st.error(f"Error loading workload: {str(e)}")
    else:
        st.info("No workload data in MongoDB. Use the ingestion controls above to load data.")

# Database management section
st.header("🛠️ Database Management")

danger_col1, danger_col2 = st.columns(2)

with danger_col1:
    st.subheader("⚠️ Danger Zone")
    
    if st.button("🗑️ Clear All Data", type="secondary"):
        if st.checkbox("I understand this will delete all data"):
            with st.spinner("Clearing all data..."):
                try:
                    data_ingest_manager.incidents_collection.delete_many({})
                    data_ingest_manager.agents_collection.delete_many({})
                    data_ingest_manager.workload_collection.delete_many({})
                    data_ingest_manager.metadata_collection.delete_many({})
                    st.success("✅ All data cleared successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error clearing data: {str(e)}")

with danger_col2:
    st.subheader("📊 Database Info")
    try:
        # Get database stats
        db_stats = data_ingest_manager.db.command("dbstats")
        st.write(f"**Database Size**: {db_stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
        st.write(f"**Collections**: {db_stats.get('collections', 0)}")
        st.write(f"**Indexes**: {db_stats.get('indexes', 0)}")
    except Exception as e:
        st.write(f"Could not get database stats: {str(e)}")
