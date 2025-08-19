"""
ITSM AI Demo Application - Main Entry Point
Multi-page Streamlit application for ITSM service desk operations with AI features
"""
import streamlit as st
import sys
import os

# Add the current directory to the path to import utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="ITSM AI Demo",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎫 ITSM AI Demo Application")
st.markdown("---")

# Welcome message
st.markdown("""
## Welcome to the ITSM AI Demo

This application demonstrates AI-powered ITSM (IT Service Management) capabilities including:

### 🎫 **Incidents Dashboard**
- View and manage incident tickets
- Filter by priority, category, and status
- AI-powered incident classification
- Interactive incident details and actions

### 📚 **Knowledge Base**
- Browse and search knowledge articles
- AI-generated solutions and recommendations
- Category-based article organization

### 📊 **Service Analytics** 
- Performance metrics and KPIs
- Service health monitoring
- Trend analysis and reporting

### 🔗 **Data Relationships**
- Explore connections between incidents, services, and CIs
- Dependency mapping and impact analysis
- Reference data management

### 🤖 **AI Features**
- **UC-02**: AI-Powered Incident Triage and Priority Classification
- **UC-21**: AI-Generated Knowledge Base Articles from Incident Patterns
- **UC-31**: AI-Powered Agent Assignment and Workload Optimization
- Model configuration and testing tools

### 🗄️ **Data Management**
- MongoDB data ingestion from CSV files
- Data source configuration and management
- Database administration tools

---

## Getting Started

1. **Configure AI Settings**: Go to the AI Features page to set up your model preferences
2. **Load Data**: Visit the Data Management page to ingest CSV data into MongoDB
3. **Explore Features**: Navigate through the different pages to explore AI-powered ITSM capabilities

## Data Sources

The application supports both MongoDB and CSV data sources:
- **MongoDB**: Primary data source for production use
- **CSV Files**: Fallback option located in the `dummydata/` directory

## AI Integration

This demo integrates with AWS Bedrock for AI capabilities:
- Multiple model support (Claude, Titan, Nova)
- Configurable system prompts for different use cases
- Persistent settings management via MongoDB

---

**Select a page from the sidebar to begin exploring the ITSM AI Demo!**
""")

# Show current data source status
try:
    from utils.data_service import data_service
    from utils.settings_manager import settings_manager
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Data Source Status")
        data_info = data_service.get_data_source_info()
        st.info(f"**Source**: {data_info['source']}\n**Status**: {data_info['status']}")
        
        if data_info['source'] == 'MongoDB':
            st.write("**Record Counts:**")
            st.write(f"- Incidents: {data_info['incidents_count']}")
            st.write(f"- Agents: {data_info['agents_count']}")
            st.write(f"- Workload: {data_info['workload_count']}")
    
    with col2:
        st.subheader("🤖 AI Configuration")
        if settings_manager.is_available():
            ai_settings = settings_manager.get_ai_model_settings()
            model_name = ai_settings.get('selected_model_name', 'Not configured')
            st.info(f"**Model**: {model_name}\n**Status**: ✅ MongoDB Connected")
        else:
            st.warning("**MongoDB**: ❌ Not Available\n**Settings**: Using session state fallback")

except Exception as e:
    st.error(f"Error loading status: {str(e)}")

# Footer
st.markdown("---")
st.markdown("*ITSM AI Demo - Powered by AWS Bedrock and MongoDB*")
