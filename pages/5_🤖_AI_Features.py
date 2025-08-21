import streamlit as st
import pandas as pd
import sys
import os
import logging

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_service import data_service
from utils.bedrock_client import bedrock_client, refresh_bedrock_client
from utils.settings_manager import settings_manager
from utils.data_ingest import data_ingest_manager

st.set_page_config(page_title="AI Features", page_icon="🤖", layout="wide")
st.title("🤖 AI-Powered ITSM Features")

# Show data source info
data_source_info = data_service.get_data_source_info()
st.sidebar.info(f"**Data Source**: {data_source_info['source']}\n**Status**: {data_source_info['status']}")

# Check if Bedrock is available
if not bedrock_client.is_available():
    st.error("🚫 AWS Bedrock is not available. Please check your .env configuration.")
    st.info("Required environment variable: AWS_BEARER_TOKEN_BEDROCK")
    st.info("Optional: AWS_REGION (defaults to us-east-1)")
    st.stop()

st.success("✅ AWS Bedrock AI is connected and ready!")

# Check MongoDB availability
if not settings_manager.is_available():
    st.warning("⚠️ MongoDB not available. Some settings may not persist.")

# Admin settings in sidebar
st.sidebar.header("⚙️ AI Model Configuration")

# Show current region and refresh button
current_region = bedrock_client.get_current_region()
st.sidebar.info(f"**AWS Region**: {current_region}")

if st.sidebar.button("🔄 Refresh Models", help="Reload models after changing .env file"):
    with st.spinner("Refreshing Bedrock client..."):
        success = refresh_bedrock_client()
        if success:
            st.sidebar.success("✅ Models refreshed successfully!")
            st.rerun()
        else:
            st.sidebar.error("❌ Failed to refresh models")

# Get available models
available_models = bedrock_client.get_available_models()
model_options = list(available_models.keys())
model_labels = [f"{available_models[model_id]}" for model_id in model_options]

# Get current settings from MongoDB
current_ai_settings = settings_manager.get_ai_model_settings()
current_model_id = current_ai_settings.get("selected_model_id")

# Find current model index
selected_model_idx = 0
if current_model_id and current_model_id in model_options:
    selected_model_idx = model_options.index(current_model_id)

# Model selection
new_model_idx = st.sidebar.selectbox(
    "AI Model:",
    range(len(model_options)),
    format_func=lambda x: model_labels[x],
    index=selected_model_idx,
    key="global_model_selector"
)

selected_model_id = model_options[new_model_idx]
selected_model_name = available_models[selected_model_id]

# Model parameters with dynamic ranges
if "claude" in selected_model_id:
    max_tokens_range = (100, 4000)
elif "nova" in selected_model_id:
    max_tokens_range = (100, 5000)
else:
    max_tokens_range = (100, 2000)

# Get current values from MongoDB
current_max_tokens = current_ai_settings.get("max_tokens", 1000)
current_temperature = current_ai_settings.get("temperature", 0.7)

# Ensure current values are within range
current_max_tokens = min(current_max_tokens, max_tokens_range[1])

max_tokens = st.sidebar.slider(
    "Max Tokens:",
    max_tokens_range[0],
    max_tokens_range[1],
    current_max_tokens,
    key="global_max_tokens"
)

temperature = st.sidebar.slider(
    "Temperature:",
    0.0,
    1.0,
    current_temperature,
    0.1,
    key="global_temperature"
)

# Update MongoDB when settings change
if (selected_model_id != current_model_id or
    max_tokens != current_max_tokens or
    temperature != current_temperature):

    success = settings_manager.update_ai_model_settings(
        selected_model_id,
        selected_model_name,
        max_tokens,
        temperature
    )
    if success:
        st.sidebar.success("✅ Settings saved to database")
    else:
        st.sidebar.error("❌ Failed to save settings")

st.sidebar.success(f"✅ Using: **{selected_model_name}**")
st.sidebar.write(f"Model ID: `{selected_model_id}`")

st.sidebar.markdown("---")
st.sidebar.caption("💡 **Tip**: If you change your AWS region in the .env file, click 'Refresh Models' to reload the available models for the new region.")

# Initialize system prompts in session state
if "system_prompts" not in st.session_state:
    st.session_state.system_prompts = {
        "incident_triage": "You are an expert ITSM analyst specializing in incident classification and priority assessment. You have deep knowledge of IT infrastructure, business impact analysis, and service level agreements.",
        "kb_generation": "You are a technical documentation specialist with expertise in creating clear, actionable knowledge base articles. You excel at transforming incident resolution patterns into structured, searchable documentation.",
        "agent_assignment": "You are an ITSM resource allocation expert with deep understanding of skill matching, workload balancing, and performance optimization for technical support teams."
    }


# Debug section
if st.sidebar.checkbox("🔍 Show Debug Info"):
    st.sidebar.write("**Foundation Models from AWS:**")
    foundation_models = bedrock_client.get_foundation_models()
    if foundation_models:
        st.sidebar.write(f"Total models: {len(foundation_models)}")
        text_models = [m for m in foundation_models if bedrock_client._supports_text_generation(m)]
        st.sidebar.write(f"Text generation models: {len(text_models)}")

        st.sidebar.write("**Sample Text Models:**")
        for model in text_models[:3]:  # Show first 3
            model_id = model.get('modelId', 'Unknown')
            model_name = model.get('modelName', 'Unknown')
            st.sidebar.write(f"- `{model_id}`")
            st.sidebar.write(f"  {model_name}")
        if len(text_models) > 3:
            st.sidebar.write(f"... and {len(text_models) - 3} more")
    else:
        st.sidebar.write("❌ No foundation models retrieved")

    # Show inference profiles
    st.sidebar.write("**Inference Profiles:**")
    try:
        profiles = bedrock_client._list_inference_profiles()
        if profiles:
            st.sidebar.write(f"Total profiles: {len(profiles)}")
            for profile in profiles[:3]:  # Show first 3
                profile_id = profile.get('inferenceProfileId', 'Unknown')
                profile_name = profile.get('inferenceProfileName', 'Unknown')
                st.sidebar.write(f"- `{profile_id}`")
                st.sidebar.write(f"  {profile_name}")
            if len(profiles) > 3:
                st.sidebar.write(f"... and {len(profiles) - 3} more")
        else:
            st.sidebar.write("No inference profiles found")
    except Exception as e:
        st.sidebar.write(f"Error getting profiles: {str(e)}")

    st.sidebar.write("**Available for Selection:**")
    available = bedrock_client.get_available_models()
    st.sidebar.write(f"Total available: {len(available)}")
    for model_id, name in list(available.items())[:3]:
        st.sidebar.write(f"- `{model_id}`")
        st.sidebar.write(f"  {name}")

# Create tabs for different AI features
tab1, tab2, tab3, tab4 = st.tabs(["🎯 UC-02: Incident Triage", "📚 UC-21: KB Generation", "👥 UC-31: Agent Matching", "⚙️ Admin & Testing"])

with tab1:
    st.subheader("🎯 UC-02: AI-Powered Incident Triage")
    st.write("Automatically classify incident priority using AI analysis of title and description.")

    # System prompt for this use case
    st.write("**System Prompt:**")
    current_triage_prompt = settings_manager.get_setting("system_prompts.incident_triage",
        "You are an expert ITSM analyst specializing in incident classification and priority assessment.")

    new_triage_prompt = st.text_area(
        "Define the AI's role and expertise for incident triage:",
        value=current_triage_prompt,
        height=100,
        key="system_prompt_triage"
    )

    # Add save button for system prompt
    col_prompt1, col_prompt2 = st.columns([3, 1])
    with col_prompt2:
        if st.button("💾 Save Prompt", key="save_triage_prompt", help="Save system prompt to MongoDB"):
            if settings_manager.update_system_prompt("incident_triage", new_triage_prompt):
                st.success("✅ System prompt saved!")
                st.rerun()
            else:
                st.error("❌ Failed to save prompt")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**Test Incident Classification:**")
        
        # Sample incidents for testing
        sample_incidents = [
            ("Email server down", "All users unable to access email. Business operations severely impacted."),
            ("Printer not working", "Printer in office 3B is not printing. Users can use other printers."),
            ("Password reset request", "User forgot password and needs reset for domain account."),
            ("Database performance slow", "Customer-facing application experiencing slow response times due to database issues.")
        ]
        
        selected_sample = st.selectbox(
            "Choose a sample incident or enter custom:",
            ["Custom"] + [f"{title} - {desc[:50]}..." for title, desc in sample_incidents]
        )
        
        if selected_sample != "Custom":
            idx = [f"{title} - {desc[:50]}..." for title, desc in sample_incidents].index(selected_sample)
            default_title, default_desc = sample_incidents[idx]
        else:
            default_title, default_desc = "", ""
        
        incident_title = st.text_input("Incident Title:", value=default_title)
        incident_description = st.text_area("Incident Description:", value=default_desc, height=100)
        
        if st.button("🎯 Classify Priority", type="primary"):
            if incident_title and incident_description:
                with st.spinner(f"AI is analyzing the incident using {selected_model_name}..."):
                    # Use global model settings and system prompt
                    prompt = f"""Analyze this incident and determine its priority level.

                    Incident Title: {incident_title}
                    Incident Description: {incident_description}

                    Priority Levels:
                    - P1: Critical - System down, major business impact
                    - P2: High - Significant impact, workaround available
                    - P3: Medium - Moderate impact, standard response
                    - P4: Low - Minor impact, can be scheduled

                    Respond with:
                    Priority: [P1/P2/P3/P4]
                    Reasoning: [Brief explanation]
                    """

                    response = bedrock_client.invoke_model(
                        prompt,
                        selected_model_id,
                        min(max_tokens, 300),
                        temperature,
                        system_prompt=settings_manager.get_setting("system_prompts.incident_triage")
                    )

                    if response:
                        lines = response.split('\n')
                        priority = "P3"  # Default
                        reasoning = "Unable to determine"

                        for line in lines:
                            if line.startswith('Priority:'):
                                priority = line.split(':')[1].strip()
                            elif line.startswith('Reasoning:'):
                                reasoning = line.split(':', 1)[1].strip()

                        result = {"priority": priority, "reasoning": reasoning}
                    else:
                        result = {"priority": "P3", "reasoning": "AI classification failed"}

                st.success(f"**Predicted Priority: {result['priority']}**")
                st.write(f"**Reasoning:** {result['reasoning']}")
            else:
                st.warning("Please enter both title and description")
    
    with col2:
        st.write("**Historical Incident Analysis:**")
        
        incidents = data_service.get_incidents()
        if not incidents.empty:
            # Show priority distribution
            if 'true_priority' in incidents.columns:
                priority_counts = incidents['true_priority'].value_counts()
                st.write("**Current Priority Distribution:**")
                for priority, count in priority_counts.items():
                    st.write(f"- {priority}: {count} incidents")
            
            # Sample incidents for batch processing
            st.write("**Batch Processing Demo:**")
            if st.button("🔄 Analyze Random Sample"):
                sample_incidents = incidents.sample(min(3, len(incidents)))
                
                for idx, incident in sample_incidents.iterrows():
                    title = incident.get('short_description', 'No title')
                    desc = incident.get('description', 'No description')
                    actual_priority = incident.get('true_priority', 'Unknown')
                    
                    with st.spinner(f"Analyzing: {title[:30]}..."):
                        prompt = f"""Analyze this incident and determine its priority level.

                        Incident Title: {title}
                        Incident Description: {desc}

                        Priority Levels:
                        - P1: Critical - System down, major business impact
                        - P2: High - Significant impact, workaround available
                        - P3: Medium - Moderate impact, standard response
                        - P4: Low - Minor impact, can be scheduled

                        Respond with:
                        Priority: [P1/P2/P3/P4]
                        Reasoning: [Brief explanation]
                        """

                        response = bedrock_client.invoke_model(
                            prompt,
                            selected_model_id,
                            min(max_tokens, 200),
                            temperature,
                            system_prompt=settings_manager.get_setting("system_prompts.incident_triage")
                        )

                        if response:
                            lines = response.split('\n')
                            priority = "P3"
                            reasoning = "Unable to determine"

                            for line in lines:
                                if line.startswith('Priority:'):
                                    priority = line.split(':')[1].strip()
                                elif line.startswith('Reasoning:'):
                                    reasoning = line.split(':', 1)[1].strip()

                            result = {"priority": priority, "reasoning": reasoning}
                        else:
                            result = {"priority": "P3", "reasoning": "AI classification failed"}
                    
                    st.write(f"**{title[:50]}...**")
                    st.write(f"- AI Predicted: {result['priority']} | Actual: {actual_priority}")
                    st.write(f"- Reasoning: {result['reasoning']}")
                    st.write("---")

with tab2:
    st.subheader("📚 UC-21: AI-Generated Knowledge Base Articles")
    st.write("Generate KB articles from clusters of similar resolved incidents.")

    # System prompt for this use case
    st.write("**System Prompt:**")
    current_kb_prompt = settings_manager.get_setting("system_prompts.kb_generation",
        "You are a technical documentation specialist with expertise in creating clear, actionable knowledge base articles.")

    new_kb_prompt = st.text_area(
        "Define the AI's role and expertise for KB article generation:",
        value=current_kb_prompt,
        height=100,
        key="system_prompt_kb"
    )

    # Add save button for system prompt
    col_prompt1, col_prompt2 = st.columns([3, 1])
    with col_prompt2:
        if st.button("💾 Save Prompt", key="save_kb_prompt", help="Save system prompt to MongoDB"):
            if settings_manager.update_system_prompt("kb_generation", new_kb_prompt):
                st.success("✅ System prompt saved!")
                st.rerun()
            else:
                st.error("❌ Failed to save prompt")

    # Get resolved incidents only
    incidents = data_service.get_incidents()
    
    if not incidents.empty:
        # Filter for resolved incidents only
        resolved_incidents = incidents[incidents['resolution_notes'].notna() & (incidents['resolution_notes'] != '')].copy()
        
        if resolved_incidents.empty:
            st.warning("No resolved incidents found with resolution notes.")
        else:
            st.info(f"Found {len(resolved_incidents)} resolved incidents with resolution notes.")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Filter Resolved Tickets for KB Generation:**")
                
                # Filter options
                filter_col1, filter_col2 = st.columns([1, 1])
                
                with filter_col1:
                    # Priority filter - handle both MongoDB and CSV column names
                    priority_col = 'priority' if 'priority' in resolved_incidents.columns else 'true_priority'
                    if priority_col in resolved_incidents.columns:
                        priorities = ['All'] + sorted(resolved_incidents[priority_col].dropna().unique().tolist())
                        selected_priority = st.selectbox("Filter by Priority:", priorities)
                        
                        if selected_priority != 'All':
                            resolved_incidents = resolved_incidents[resolved_incidents[priority_col] == selected_priority]
                    else:
                        selected_priority = 'All'
                
                with filter_col2:
                    # Category filter - handle both MongoDB and CSV column names
                    category_col = 'category' if 'category' in resolved_incidents.columns else 'category_id'
                    if category_col in resolved_incidents.columns:
                        categories = ['All'] + sorted(resolved_incidents[category_col].dropna().unique().tolist())
                        selected_category = st.selectbox("Filter by Category:", categories)
                        
                        if selected_category != 'All':
                            resolved_incidents = resolved_incidents[resolved_incidents[category_col] == selected_category]
                    else:
                        selected_category = 'All'
                
                # Ground truth cluster filter (for similar incidents) - only available in CSV data
                if 'ground_truth_cluster' in resolved_incidents.columns:
                    clusters = ['All'] + sorted(resolved_incidents['ground_truth_cluster'].dropna().unique().tolist())
                    selected_cluster = st.selectbox("Filter by Issue Type:", clusters, help="Groups similar incidents together")
                    
                    if selected_cluster != 'All':
                        resolved_incidents = resolved_incidents[resolved_incidents['ground_truth_cluster'] == selected_cluster]
                else:
                    selected_cluster = 'All'
                
                st.write(f"**Filtered Results: {len(resolved_incidents)} incidents**")
                
                # Show sample incidents
                if len(resolved_incidents) > 0:
                    st.write("**Sample incidents to include:**")
                    sample_incidents = resolved_incidents.head(5)
                    for idx, incident in sample_incidents.iterrows():
                        st.write(f"- **{incident.get('short_description', 'No description')}**")
                        priority = incident.get('priority', incident.get('true_priority', 'Unknown'))
                        st.write(f"  Priority: {priority} | Resolution: {incident.get('resolution_notes', 'No notes')[:50]}...")
                    
                    if len(resolved_incidents) > 5:
                        st.write(f"... and {len(resolved_incidents) - 5} more incidents")
                    
                    if st.button("📝 Generate KB Article from Filtered Tickets", type="primary"):
                        # Use all filtered incidents, limit to 10 for token efficiency
                        incident_cluster = resolved_incidents.head(10).to_dict('records')
                        
                        with st.spinner(f"AI is analyzing {len(incident_cluster)} resolved tickets using {selected_model_name}..."):
                            # Prepare detailed incident summaries with resolutions
                            incident_summaries = []
                            for i, incident in enumerate(incident_cluster, 1):
                                summary = f"{i}. **Issue:** {incident.get('short_description', 'No description')}"
                                if incident.get('description'):
                                    summary += f"\n   **Details:** {incident.get('description', '')[:100]}..."
                                if incident.get('resolution_notes'):
                                    summary += f"\n   **Resolution:** {incident.get('resolution_notes', '')}"
                                if incident.get('time_to_resolve_mins'):
                                    summary += f"\n   **Resolution Time:** {incident.get('time_to_resolve_mins')} minutes"
                                incident_summaries.append(summary)

                            incidents_text = '\n\n'.join(incident_summaries)

                            prompt = f"""Analyze these {len(incident_cluster)} resolved IT support tickets and create a comprehensive knowledge base article.

                            RESOLVED TICKETS:
                            {incidents_text}

                            Based on the common patterns in these resolved tickets, create a knowledge base article that would help users and support agents resolve similar issues quickly.

                            Requirements:
                            1. **Title**: Create a clear, searchable title that covers the main issue
                            2. **Problem Description**: Describe what users typically experience
                            3. **Root Cause**: Explain why this issue occurs
                            4. **Solution Steps**: Provide step-by-step resolution instructions
                            5. **Prevention**: Suggest how to prevent this issue
                            6. **Tags**: List relevant keywords for searchability

                            Format your response exactly as:
                            Title: [Clear, specific title]
                            Problem: [What users experience]
                            Root Cause: [Why this happens]
                            Solution: [Step-by-step instructions]
                            Prevention: [How to avoid this issue]
                            Tags: [comma-separated keywords]
                            """

                            response = bedrock_client.invoke_model(
                                prompt,
                                selected_model_id,
                                min(max_tokens, 1500),
                                temperature,
                                system_prompt=settings_manager.get_setting("system_prompts.kb_generation")
                            )

                            if response:
                                sections = {"title": "", "problem": "", "root_cause": "", "solution": "", "prevention": "", "tags": ""}
                                current_section = None

                                for line in response.split('\n'):
                                    line = line.strip()
                                    if line.startswith('Title:'):
                                        sections['title'] = line.split(':', 1)[1].strip()
                                    elif line.startswith('Problem:'):
                                        sections['problem'] = line.split(':', 1)[1].strip()
                                        current_section = 'problem'
                                    elif line.startswith('Root Cause:'):
                                        sections['root_cause'] = line.split(':', 1)[1].strip()
                                        current_section = 'root_cause'
                                    elif line.startswith('Solution:'):
                                        sections['solution'] = line.split(':', 1)[1].strip()
                                        current_section = 'solution'
                                    elif line.startswith('Prevention:'):
                                        sections['prevention'] = line.split(':', 1)[1].strip()
                                        current_section = 'prevention'
                                    elif line.startswith('Tags:'):
                                        sections['tags'] = line.split(':', 1)[1].strip()
                                        current_section = None
                                    elif current_section and line:
                                        sections[current_section] += '\n' + line

                                article = sections
                            else:
                                article = {"title": "Generated Article", "problem": "", "root_cause": "", "solution": "", "prevention": "", "tags": ""}
                        
                        # Store in session state
                        st.session_state.generated_article = article
                        st.session_state.incident_cluster = incident_cluster
                        st.session_state.selected_priority = selected_priority
                        st.session_state.selected_category = selected_category
                        st.session_state.selected_cluster = selected_cluster
                        
                        st.success("✅ KB Article Generated from Resolved Tickets!")
                        
                        
            # Display generated article if it exists in session state
            if 'generated_article' in st.session_state:
                article = st.session_state.generated_article
                incident_cluster = st.session_state.incident_cluster
                selected_priority = st.session_state.selected_priority
                selected_category = st.session_state.selected_category
                selected_cluster = st.session_state.selected_cluster
                
                with col2:
                    st.write("**Generated Knowledge Base Article:**")
                    
                    st.markdown(f"### {article['title']}")
                    
                    st.write("**Problem Description:**")
                    st.markdown(article['problem'])

                    st.write("**Root Cause:**")
                    st.markdown(article['root_cause'])

                    st.write("**Solution Steps:**")
                    st.markdown(article['solution'])

                    st.write("**Prevention:**")
                    st.markdown(article['prevention'])
                    
                    st.write("**Tags:**")
                    st.code(article['tags'])
                    
                    # Show source information
                    st.write("---")
                    st.write(f"**Generated from:** {len(incident_cluster)} resolved tickets")
                    if selected_priority != 'All':
                        st.write(f"**Priority Filter:** {selected_priority}")
                    if selected_category != 'All':
                        st.write(f"**Category Filter:** {selected_category}")
                    if selected_cluster != 'All':
                        st.write(f"**Issue Type:** {selected_cluster}")
                    
                    # Option to save to KB
                    if st.button("💾 Save to Knowledge Base", help="Save this article to the knowledge base"):
                        # Save to MongoDB
                        kb_data = {
                            'title': article['title'],
                            'problem': article['problem'],
                            'root_cause': article['root_cause'],
                            'solution': article['solution'],
                            'prevention': article['prevention'],
                            'tags': article['tags'],
                            'source_incidents': len(incident_cluster),
                            'ai_generated': True,
                            'filters': {
                                'priority': selected_priority if selected_priority != 'All' else None,
                                'category': selected_category if selected_category != 'All' else None,
                                'cluster': selected_cluster if selected_cluster != 'All' else None
                            }
                        }
                        
                        success = data_ingest_manager.save_kb_article(kb_data)
                        if success:
                            st.success("✅ Article saved to knowledge base!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to save article. Check MongoDB connection.")
            
            elif 'generated_article' not in st.session_state:
                with col2:
                    st.info("👈 Filter resolved tickets and generate KB article")
                    
                    # Show statistics about resolved incidents
                    st.write("**Resolved Incidents Overview:**")
                    
                    priority_col = 'priority' if 'priority' in resolved_incidents.columns else 'true_priority'
                    if priority_col in resolved_incidents.columns:
                        priority_counts = resolved_incidents[priority_col].value_counts()
                        st.write("**By Priority:**")
                        for priority, count in priority_counts.items():
                            st.write(f"- {priority}: {count} incidents")
                    
                    if 'ground_truth_cluster' in resolved_incidents.columns:
                        cluster_counts = resolved_incidents['ground_truth_cluster'].value_counts().head(5)
                        st.write("**Top Issue Types:**")
                        for cluster, count in cluster_counts.items():
                            st.write(f"- {cluster}: {count} incidents")
                    
                    if 'time_to_resolve_mins' in resolved_incidents.columns:
                        avg_resolution = resolved_incidents['time_to_resolve_mins'].mean()
                        st.write(f"**Average Resolution Time:** {avg_resolution:.1f} minutes")
    else:
        st.warning("No incident data available. Please check your data source.")

with tab3:
    st.subheader("👥 UC-31: AI-Powered Agent Assignment")
    st.write("Intelligently match incidents to the best available agents based on skills, capacity, and performance.")

    # System prompt for this use case
    st.write("**System Prompt:**")
    current_agent_prompt = settings_manager.get_setting("system_prompts.agent_assignment",
        "You are an ITSM resource allocation expert with deep understanding of skill matching, workload balancing, and performance optimization.")

    new_agent_prompt = st.text_area(
        "Define the AI's role and expertise for agent assignment:",
        value=current_agent_prompt,
        height=100,
        key="system_prompt_agent"
    )

    # Add save button for system prompt
    col_prompt1, col_prompt2 = st.columns([3, 1])
    with col_prompt2:
        if st.button("💾 Save Prompt", key="save_agent_prompt", help="Save system prompt to MongoDB"):
            if settings_manager.update_system_prompt("agent_assignment", new_agent_prompt):
                st.success("✅ System prompt saved!")
                st.rerun()
            else:
                st.error("❌ Failed to save prompt")

    workload = data_service.get_workload()
    agents = data_service.get_agents()
    # Note: agent_skills and skills_catalog not yet in MongoDB, using empty DataFrames
    agent_skills = pd.DataFrame()
    skills_catalog = pd.DataFrame()
    
    if not workload.empty and not agents.empty:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Select Incident for Assignment:**")
            
            # Show current queue items
            if len(workload) > 0:
                queue_options = []
                for idx, item in workload.head(10).iterrows():
                    desc = item.get('description', item.get('record_id', 'Unknown'))
                    queue_options.append(f"{desc[:50]}...")
                
                selected_incident_idx = st.selectbox("Choose incident:", range(len(queue_options)), format_func=lambda x: queue_options[x])
                selected_incident = workload.iloc[selected_incident_idx]
                
                st.write("**Incident Details:**")
                st.write(f"- **Type:** {selected_incident.get('record_type', 'Unknown')}")
                st.write(f"- **Priority:** {selected_incident.get('priority', 'Unknown')}")
                st.write(f"- **Required Skills:** {selected_incident.get('required_skills', 'None')}")
                
                # Mock available agents with skills
                mock_agents = [
                    {"name": "Alice Johnson", "skills": ["Password Reset", "VPN Troubleshooting"], "current_capacity": "60%", "performance_score": "4.8/5"},
                    {"name": "Bob Smith", "skills": ["Printer Support", "Wi-Fi Access"], "current_capacity": "40%", "performance_score": "4.6/5"},
                    {"name": "Carol Davis", "skills": ["Outlook/Exchange", "MFA Support"], "current_capacity": "80%", "performance_score": "4.9/5"},
                    {"name": "David Wilson", "skills": ["VPN Troubleshooting", "Printer Support"], "current_capacity": "30%", "performance_score": "4.7/5"}
                ]
                
                if st.button("🎯 Find Best Agent", type="primary"):
                    with st.spinner(f"AI is analyzing agent assignments using {selected_model_name}..."):
                        # Prepare agent information
                        agent_info = []
                        for agent in mock_agents[:10]:  # Limit to 10 agents
                            skills = agent.get('skills', [])
                            capacity = agent.get('current_capacity', 'Unknown')
                            performance = agent.get('performance_score', 'Unknown')

                            agent_summary = f"- {agent.get('name', 'Unknown')}: Skills: {', '.join(skills)}, Capacity: {capacity}, Performance: {performance}"
                            agent_info.append(agent_summary)

                        agents_text = '\n'.join(agent_info)

                        prompt = f"""Recommend the best agent for this incident.

                        Incident Details:
                        - Title: {selected_incident.get('description', 'No title')}
                        - Type: {selected_incident.get('record_type', 'Unknown')}
                        - Priority: {selected_incident.get('priority', 'Unknown')}
                        - Required Skills: {selected_incident.get('required_skills', 'None specified')}

                        Available Agents:
                        {agents_text}

                        Consider:
                        1. Skill match for the incident type
                        2. Current capacity/workload
                        3. Performance history
                        4. Priority level urgency

                        Respond with:
                        Recommended Agent: [Agent name]
                        Reasoning: [Why this agent is best suited]
                        Confidence: [High/Medium/Low]
                        """

                        response = bedrock_client.invoke_model(
                            prompt,
                            selected_model_id,
                            min(max_tokens, 400),
                            temperature,
                            system_prompt=settings_manager.get_setting("system_prompts.agent_assignment")
                        )

                        if response:
                            lines = response.split('\n')
                            agent = "No recommendation"
                            reasoning = "Unable to determine"
                            confidence = "Low"

                            for line in lines:
                                if line.startswith('Recommended Agent:'):
                                    agent = line.split(':', 1)[1].strip()
                                elif line.startswith('Reasoning:'):
                                    reasoning = line.split(':', 1)[1].strip()
                                elif line.startswith('Confidence:'):
                                    confidence = line.split(':', 1)[1].strip()

                            recommendation = {"agent": agent, "reasoning": reasoning, "confidence": confidence}
                        else:
                            recommendation = {"agent": "No recommendation", "reasoning": "AI assignment failed", "confidence": "Low"}
                    
                    st.success("✅ Assignment Recommendation Generated!")
                    
                    with col2:
                        st.write("**AI Recommendation:**")
                        st.write(f"**Recommended Agent:** {recommendation['agent']}")
                        st.write(f"**Reasoning:** {recommendation['reasoning']}")
                        st.write(f"**Confidence:** {recommendation['confidence']}")
                        
                        st.write("**Available Agents:**")
                        for agent in mock_agents:
                            st.write(f"- **{agent['name']}**: {', '.join(agent['skills'])} (Capacity: {agent['current_capacity']}, Score: {agent['performance_score']})")
                        
                        if st.button("✅ Assign to Recommended Agent"):
                            st.success(f"Incident assigned to {recommendation['agent']}! (Demo)")
        
        with col2:
            if 'recommendation' not in locals():
                st.info("👈 Select an incident and get AI recommendation")

with tab4:
    st.subheader("⚙️ Admin & Testing Interface")
    st.write("Configure AI models globally and test custom prompts.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**Current Configuration:**")
        st.info(f"**Model:** {selected_model_name}")
        st.info(f"**Model ID:** `{selected_model_id}`")
        st.info(f"**Max Tokens:** {max_tokens}")
        st.info(f"**Temperature:** {temperature}")

        st.write("**Test Prompt:**")
        custom_prompt = st.text_area(
            "Enter a test prompt:",
            value="Explain the benefits of AI in IT Service Management in 3 bullet points.",
            height=120,
            help="Use this to test your current model configuration"
        )

        # Optional system prompt for testing
        use_system_prompt = st.checkbox("Use system prompt for testing")
        test_system_prompt = None
        if use_system_prompt:
            test_system_prompt = st.text_area(
                "Test system prompt:",
                value="You are a helpful AI assistant specializing in IT Service Management.",
                height=80,
                help="Optional system prompt to test with"
            )

        if st.button("🧪 Test Current Configuration", type="primary"):
            with st.spinner(f"Testing {selected_model_name}..."):
                response = bedrock_client.invoke_model(
                    custom_prompt,
                    selected_model_id,
                    max_tokens,
                    temperature,
                    system_prompt=test_system_prompt if use_system_prompt else None
                )

            if response:
                with col2:
                    st.write("**Test Response:**")
                    st.write(response)

                    # Show test details
                    st.write("---")
                    st.write("**Test Details:**")
                    st.write(f"- Model: {selected_model_name}")
                    st.write(f"- Tokens: {max_tokens}")
                    st.write(f"- Temperature: {temperature}")
                    st.write(f"- Response Length: {len(response)} characters")
            else:
                st.error("❌ Test failed - check model configuration")

        st.write("---")
        st.write("**Configuration Notes:**")
        st.write("• Model settings in sidebar apply to ALL use cases")
        st.write("• Lower temperature = more consistent responses")
        st.write("• Higher temperature = more creative responses")
        st.write("• Max tokens controls response length")

    with col2:
        if 'response' not in locals():
            st.write("**Available Models:**")

            # Show model capabilities
            for model_id, model_name in available_models.items():
                if "claude" in model_id:
                    capabilities = "🧠 Advanced reasoning, coding, analysis"
                    max_tokens_info = "Up to 4,000 tokens"
                elif "nova-pro" in model_id:
                    capabilities = "⚡ High performance, multimodal"
                    max_tokens_info = "Up to 5,000 tokens"
                elif "nova-lite" in model_id:
                    capabilities = "🚀 Fast, cost-effective"
                    max_tokens_info = "Up to 5,000 tokens"
                else:
                    capabilities = "🤖 General purpose"
                    max_tokens_info = "Up to 2,000 tokens"

                # Highlight current model
                if model_id == selected_model_id:
                    st.success(f"**✅ {model_name}** (Currently Selected)")
                    st.write(f"   {capabilities}")
                    st.write(f"   {max_tokens_info}")
                else:
                    st.write(f"**{model_name}**")
                    st.write(f"   {capabilities}")
                    st.write(f"   {max_tokens_info}")
                st.write("")

            st.write("**💡 Tips:**")
            st.write("• Use sidebar to change model for all use cases")
            st.write("• Test prompts here before using in production")
            st.write("• Monitor token usage for cost optimization")

# Footer
st.markdown("---")
st.markdown("**💡 Tip:** These AI features demonstrate the three core ITSM use cases. In production, you would integrate these directly into your incident management workflow.")
