"""
Agents Management Page
Manage IT support agents and their skills
"""
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from utils.data_ingest import data_ingest_manager
from utils.data_service import data_service

# Page configuration
st.set_page_config(
    page_title="Agents Management",
    page_icon="👥",
    layout="wide"
)

st.title("👥 Agents Management")

# Check data source
data_source = "MongoDB" if data_service.use_mongodb and data_service.mongodb_has_data else "CSV"
status_icon = "✅" if data_source == "MongoDB" else "⚠️"
st.sidebar.info(f"**Data Source**: {data_source} **Status**: {status_icon} Connected")

def generate_sample_agents():
    """Generate sample agent data with skills"""
    
    # Available skills from the current queue
    available_skills = [
        'MFA/Authenticator Support',
        'Outlook/Exchange', 
        'VPN Troubleshooting',
        'Printer Support',
        'Password Reset',
        'Wi-Fi Access Issues'
    ]
    
    # Sample agent names
    agent_names = [
        "Sarah Johnson", "Michael Chen", "Emma Williams", "David Rodriguez",
        "Lisa Thompson", "James Wilson", "Maria Garcia", "Robert Taylor",
        "Jennifer Brown", "Christopher Lee"
    ]
    
    # Generate agents
    agents = []
    for i, name in enumerate(agent_names):
        # Assign 1-2 skills randomly
        num_skills = random.randint(1, 2)
        agent_skills = random.sample(available_skills, num_skills)

        # Generate current queue (0-5, where 5 is full)
        current_queue = random.randint(0, 5)

        # Status based on queue level
        if current_queue >= 5:
            status = 'Busy'
        elif current_queue >= 3:
            status = random.choice(['Available', 'Busy'])
        else:
            status = random.choice(['Available', 'Available', 'Away'])

        agent = {
            'agent_id': f'AGT{str(i+1).zfill(3)}',
            'name': name,
            'email': f"{name.lower().replace(' ', '.')}.{random.randint(100,999)}@company.com",
            'department': 'IT Support',
            'status': status,
            'current_queue': current_queue,
            'skills': agent_skills,
            'skill_count': len(agent_skills),
            'last_updated': datetime.now().isoformat()
        }
        agents.append(agent)
    
    return agents

def save_agents_to_mongodb(agents_data):
    """Save agents to MongoDB"""
    try:
        if data_ingest_manager.available:
            # Clear existing agents
            data_ingest_manager.db.agents.delete_many({})
            
            # Insert new agents
            result = data_ingest_manager.db.agents.insert_many(agents_data)
            return len(result.inserted_ids)
        return 0
    except Exception as e:
        st.error(f"Error saving agents: {str(e)}")
        return 0

def get_agents_from_mongodb():
    """Get agents from MongoDB"""
    try:
        if data_ingest_manager.available:
            agents = list(data_ingest_manager.db.agents.find({}, {'_id': 0}))
            return pd.DataFrame(agents) if agents else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading agents: {str(e)}")
        return pd.DataFrame()

# Main content
tab1, tab2, tab3 = st.tabs(["📋 All Agents", "➕ Add Agent", "⚙️ Manage Data"])

with tab1:
    st.subheader("Current Agents")
    
    # Load agents from MongoDB
    agents_df = get_agents_from_mongodb()
    
    if not agents_df.empty:
        # Check if the data has the expected structure
        required_columns = ['status', 'skill_count', 'current_queue']
        missing_columns = [col for col in required_columns if col not in agents_df.columns]

        if missing_columns:
            st.error(f"❌ Agent data is missing required columns: {missing_columns}")
            st.info("Please use the 'Manage Data' tab to clear and regenerate the agent data.")
        else:
            # Display summary statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Agents", len(agents_df))

            with col2:
                available_count = len(agents_df[agents_df['status'] == 'Available'])
                st.metric("Available", available_count)

            with col3:
                avg_skills = agents_df['skill_count'].mean()
                st.metric("Avg Skills per Agent", f"{avg_skills:.1f}")

            with col4:
                avg_queue = agents_df['current_queue'].mean()
                st.metric("Avg Queue Load", f"{avg_queue:.1f}/5")
        
            # Filters
            st.subheader("Filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                status_filter = st.selectbox("Status", ["All"] + list(agents_df['status'].unique()))

            with col2:
                queue_filter = st.selectbox("Queue Load", ["All", "Light (0-1)", "Medium (2-3)", "Heavy (4-5)"])

            with col3:
                # Get all unique skills
                all_skills = []
                for skills_list in agents_df['skills']:
                    all_skills.extend(skills_list)
                unique_skills = list(set(all_skills))
                skill_filter = st.selectbox("Has Skill", ["All"] + unique_skills)
        
            # Apply filters
            filtered_df = agents_df.copy()

            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]

            if queue_filter != "All":
                if queue_filter == "Light (0-1)":
                    filtered_df = filtered_df[filtered_df['current_queue'] <= 1]
                elif queue_filter == "Medium (2-3)":
                    filtered_df = filtered_df[(filtered_df['current_queue'] >= 2) & (filtered_df['current_queue'] <= 3)]
                elif queue_filter == "Heavy (4-5)":
                    filtered_df = filtered_df[filtered_df['current_queue'] >= 4]

            if skill_filter != "All":
                filtered_df = filtered_df[filtered_df['skills'].apply(lambda x: skill_filter in x)]

            # Display agents table
            st.subheader(f"Agents ({len(filtered_df)} of {len(agents_df)})")

            if not filtered_df.empty:
                # Prepare display dataframe
                display_df = filtered_df.copy()
                display_df['skills_display'] = display_df['skills'].apply(lambda x: ', '.join(x))
                display_df['queue_display'] = display_df['current_queue'].apply(lambda x: f"{x}/5")

                # Select columns for display
                display_columns = ['agent_id', 'name', 'email', 'status', 'queue_display', 'skills_display']
                display_df = display_df[display_columns]

                # Rename columns
                display_df = display_df.rename(columns={
                    'agent_id': 'Agent ID',
                    'name': 'Name',
                    'email': 'Email',
                    'status': 'Status',
                    'queue_display': 'Current Queue',
                    'skills_display': 'Skills'
                })

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No agents match the selected filters.")
    
    else:
        st.info("No agents found. Use the 'Manage Data' tab to generate sample data.")

with tab2:
    st.subheader("Add New Agent")
    st.info("Manual agent creation functionality - Coming soon!")

with tab3:
    st.subheader("Data Management")
    
    # Check current data
    agents_df = get_agents_from_mongodb()
    
    if not agents_df.empty:
        st.success(f"✅ Found {len(agents_df)} agents in MongoDB")
        
        if st.button("🗑️ Clear All Agents", type="secondary"):
            if data_ingest_manager.available:
                data_ingest_manager.db.agents.delete_many({})
                st.success("All agents cleared!")
                st.rerun()
    else:
        st.warning("No agents found in MongoDB")
    
    st.markdown("---")
    
    # Generate sample data
    st.subheader("Generate Sample Data")
    st.write("Generate 10 sample agents with skills based on current queue requirements")
    
    if st.button("🎲 Generate Sample Agents", type="primary"):
        with st.spinner("Generating sample agents..."):
            # Generate sample data
            sample_agents = generate_sample_agents()
            
            # Save to MongoDB
            saved_count = save_agents_to_mongodb(sample_agents)
            
            if saved_count > 0:
                st.success(f"✅ Generated and saved {saved_count} sample agents!")
                st.rerun()
            else:
                st.error("❌ Failed to save agents to MongoDB")
