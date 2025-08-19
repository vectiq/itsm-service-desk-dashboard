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

st.set_page_config(page_title="Data Management", page_icon="🗄️", layout="wide")
st.title("🗄️ Data Management")

# Check MongoDB availability
if not data_ingest_manager.is_available():
    st.error("🚫 MongoDB is not available. Please check your MongoDB connection.")
    st.info("Make sure MongoDB is running on localhost:27017")
    st.stop()

# Get current data status for internal use
data_exists = data_ingest_manager.check_data_exists()
data_stats = data_ingest_manager.get_data_stats()
st.header("🤖 AI Data Generation")
st.write("Generate realistic ITSM data using AWS Bedrock AI")

# Check if Bedrock is available
from utils.bedrock_client import bedrock_client

if bedrock_client.is_available():
    st.success("✅ AWS Bedrock AI is connected")

    # AI Incident Generation
    st.subheader("🎫 Generate AI Incidents")

    # Dedicated model settings for data generation
    st.write("**Model Configuration for Data Generation:**")

    # Get available models
    try:
        available_models = bedrock_client.get_available_models()
        model_options = {}
        for model in available_models:
            if isinstance(model, dict):
                model_id = model.get('modelId', '')
                model_name = model.get('modelName', model_id)
            else:
                # Handle case where model is a string
                model_id = str(model)
                model_name = model_id
            model_options[f"{model_name} ({model_id})"] = model_id
    except Exception as e:
        st.error(f"Error loading models: {str(e)}")
        model_options = {"Claude Sonnet (fallback)": "anthropic.claude-3-sonnet-20240229-v1:0"}

    # Model selection
    col1, col2 = st.columns([2, 1])
    with col1:
        if model_options:
            # Default to Claude Sonnet if available
            default_model = None
            for display_name, model_id in model_options.items():
                if "claude-3-5-sonnet" in model_id.lower():
                    default_model = display_name
                    break
            if not default_model:
                default_model = list(model_options.keys())[0]

            selected_model_display = st.selectbox(
                "Select Model for Data Generation",
                options=list(model_options.keys()),
                index=list(model_options.keys()).index(default_model) if default_model in model_options else 0
            )
            selected_model_id = model_options[selected_model_display]
        else:
            st.error("No models available")
            selected_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    with col2:
        max_tokens = st.number_input("Max Tokens", min_value=1000, max_value=8000, value=4000, step=500)
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

    st.info(f"**Selected**: {selected_model_display}\n**Settings**: {max_tokens} tokens, temperature {temperature}")

    incident_count = st.number_input("Total incidents to generate", min_value=1, max_value=500, value=100)
    resolved_percentage = st.slider("Percentage resolved", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

    resolved_count = int(incident_count * resolved_percentage)
    unresolved_count = incident_count - resolved_count

    st.info(f"Will generate {resolved_count} resolved and {unresolved_count} unresolved incidents")

    if any(data_exists.values()):
        st.warning("⚠️ **Warning**: This will replace all existing data in MongoDB!")

    # Debug console toggle
    show_debug = st.checkbox("🔍 Show Debug Console", help="Show detailed error messages and logs")

    if st.button("🤖 Generate AI Incidents", type="primary"):
        debug_container = st.container()

        with st.spinner("Generating AI-powered incidents... This may take a few minutes."):
            try:
                if show_debug:
                    with debug_container:
                        st.subheader("🔍 Debug Console")
                        debug_log = st.empty()
                        debug_log.text("Starting AI incident generation...")

                success = data_ingest_manager.generate_ai_incidents(
                    incident_count, resolved_percentage,
                    model_id=selected_model_id, max_tokens=max_tokens, temperature=temperature
                )

                if success:
                    st.success(f"✅ Generated {incident_count} AI-powered incidents!")
                    st.info("💡 Workload queue now shows unresolved unassigned incidents")
                    st.info("🔄 Refresh the page to see the new data in the preview below")
                    if show_debug:
                        with debug_container:
                            st.success("🔍 Generation completed successfully!")
                else:
                    st.error("❌ Failed to generate AI incidents")
                    if show_debug:
                        with debug_container:
                            st.error("🔍 Generation failed - check logs for details")

                            # Try to get more specific error information
                            st.subheader("🔍 Debug Console - Generation Failure")
                            st.error("The generation function returned False, indicating failure.")
                            st.info("Common causes:")
                            st.write("• MongoDB connection issues")
                            st.write("• AWS Bedrock API errors")
                            st.write("• Model token limits exceeded")
                            st.write("• Invalid model configuration")

                            # Show current settings for debugging
                            st.subheader("📋 Current Settings")
                            st.write(f"**Model ID**: {selected_model_id}")
                            st.write(f"**Max Tokens**: {max_tokens}")
                            st.write(f"**Temperature**: {temperature}")
                            st.write(f"**Incident Count**: {incident_count}")
                            st.write(f"**Resolved Percentage**: {resolved_percentage}")
                    else:
                        st.info("Enable 'Show Debug Console' for detailed debugging information.")

            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ Failed to generate AI incidents: {error_msg}")

                if show_debug:
                    with debug_container:
                        st.subheader("🔍 Debug Console - Error Details")
                        st.error(f"**Error Type**: {type(e).__name__}")
                        st.error(f"**Error Message**: {error_msg}")

                        # Show more detailed error info
                        import traceback
                        st.code(traceback.format_exc(), language="python")

                        # Show recent logs if available
                        st.subheader("📋 Recent Logs")
                        st.info("Check the application logs for more detailed information about the AI generation process.")

    st.divider()

    # Agent Generation (existing functionality)
    st.subheader("👥 Generate Sample Agents")
    st.write("Generate agents with skills for workload assignment")

    if st.button("🎲 Generate Sample Agents"):
        # This will use the existing agent generation from the Agents page
        st.info("Use the Agents page to generate sample agents with skills")

else:
    st.error("❌ AWS Bedrock not available")
    st.info("Please configure AWS_BEARER_TOKEN_BEDROCK in your .env file")
    st.write("**Required environment variables:**")
    st.code("AWS_BEARER_TOKEN_BEDROCK=your_token_here")
    st.code("AWS_REGION=us-east-1  # optional, defaults to us-east-1")

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

                # Select key columns for better display
                key_columns = ['incident_id', 'title', 'status', 'priority', 'urgency', 'impact',
                              'category_id', 'assigned_to', 'created_on', 'sla_due']
                available_columns = [col for col in key_columns if col in df.columns]

                if available_columns:
                    display_df = df[available_columns]
                    st.dataframe(display_df, use_container_width=True)

                    # Show column info
                    st.caption(f"Showing {len(available_columns)} key columns out of {len(df.columns)} total columns")

                    # Option to show all columns
                    if st.checkbox("Show all columns"):
                        st.dataframe(df, use_container_width=True)
                else:
                    st.dataframe(df, use_container_width=True)
            else:
                st.info("No incidents data found")
        except Exception as e:
            st.error(f"Error loading incidents: {str(e)}")
    else:
        st.info("No incidents data in MongoDB. Use the AI generation controls above to create data.")

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
        st.info("No agents data in MongoDB. Use the Agents page to generate sample agents.")

with preview_tabs[2]:
    st.write("**Current Workload Queue** (Unresolved unassigned incidents)")
    try:
        # Get workload from data service (which filters incidents)
        from utils.data_service import data_service
        workload_df = data_service.get_workload()

        if not workload_df.empty:
            st.write(f"**Showing first 10 workload items** (Total: {len(workload_df):,})")
            display_df = workload_df.head(10)

            # Select key columns for display
            display_columns = ['incident_id', 'title', 'status', 'priority', 'created_on', 'sla_due']
            available_columns = [col for col in display_columns if col in display_df.columns]

            if available_columns:
                st.dataframe(display_df[available_columns], use_container_width=True)
            else:
                st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No unresolved unassigned incidents in the workload queue")
    except Exception as e:
        st.error(f"Error loading workload: {str(e)}")



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
