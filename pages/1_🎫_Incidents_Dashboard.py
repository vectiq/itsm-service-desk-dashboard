import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import ensure_data_loaded
from utils.bedrock_client import BedrockClient
from utils.settings_manager import settings_manager

st.set_page_config(page_title="Incidents Dashboard", page_icon="🎫", layout="wide")
st.title("🎫 Incidents Dashboard")

# Initialize bedrock client
bedrock_client = BedrockClient()

# Ensure data is loaded
dfs = ensure_data_loaded()

# Get all related data with proper relationships
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())
workload = dfs.get("workload_queue.csv", pd.DataFrame())
categories = dfs.get("category_tree.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())
cmdb_ci = dfs.get("cmdb_ci.csv", pd.DataFrame())
assignment_groups = dfs.get("assignment_groups.csv", pd.DataFrame())
users_agents = dfs.get("users_agents.csv", pd.DataFrame())
priority_matrix = dfs.get("priority_matrix.csv", pd.DataFrame())

# Enrich incidents with related data
incidents_enriched = incidents.copy()

# Join with services catalog
if not services.empty and 'service_id' in incidents.columns and 'service_id' in services.columns:
    service_cols = ['service_id', 'name']
    if 'criticality' in services.columns:
        service_cols.append('criticality')
    incidents_enriched = incidents_enriched.merge(
        services[service_cols].rename(columns={'name': 'service_name'}),
        on='service_id', how='left'
    )

# Join with categories
if not categories.empty and 'category_id' in incidents.columns and 'category_id' in categories.columns:
    category_cols = ['category_id', 'name']
    if 'parent_id' in categories.columns:
        category_cols.append('parent_id')
    if 'path' in categories.columns:
        category_cols.append('path')
    incidents_enriched = incidents_enriched.merge(
        categories[category_cols].rename(columns={'name': 'category_name'}),
        on='category_id', how='left'
    )

# Join with assignment groups
if not assignment_groups.empty and 'true_assignment_group_id' in incidents.columns and 'group_id' in assignment_groups.columns:
    group_cols = ['group_id', 'name']
    if 'service' in assignment_groups.columns:
        group_cols.append('service')
    if 'queue_type' in assignment_groups.columns:
        group_cols.append('queue_type')
    incidents_enriched = incidents_enriched.merge(
        assignment_groups[group_cols].rename(columns={'group_id': 'true_assignment_group_id', 'name': 'group_name'}),
        on='true_assignment_group_id', how='left'
    )

# Join with CMDB CIs
if not cmdb_ci.empty and 'ci_id' in incidents.columns and 'ci_id' in cmdb_ci.columns:
    ci_cols = ['ci_id', 'name']
    if 'class' in cmdb_ci.columns:
        ci_cols.append('class')
    if 'environment' in cmdb_ci.columns:
        ci_cols.append('environment')
    if 'status' in cmdb_ci.columns:
        ci_cols.append('status')

    incidents_enriched = incidents_enriched.merge(
        cmdb_ci[ci_cols].rename(columns={'name': 'ci_name', 'class': 'ci_class'}),
        on='ci_id', how='left'
    )

# Enrich workload queue with related data
workload_enriched = workload.copy()

# Join workload with services catalog
if not services.empty and 'service_id' in workload.columns and 'service_id' in services.columns:
    service_cols = ['service_id', 'name']
    if 'criticality' in services.columns:
        service_cols.append('criticality')
    workload_enriched = workload_enriched.merge(
        services[service_cols].rename(columns={'name': 'service_name'}),
        on='service_id', how='left'
    )

# Join workload with categories
if not categories.empty and 'category_id' in workload.columns and 'category_id' in categories.columns:
    category_cols = ['category_id', 'name']
    if 'parent_id' in categories.columns:
        category_cols.append('parent_id')
    if 'path' in categories.columns:
        category_cols.append('path')
    workload_enriched = workload_enriched.merge(
        categories[category_cols].rename(columns={'name': 'category_name'}),
        on='category_id', how='left'
    )

# Join workload with assignment groups (if applicable)
if not assignment_groups.empty and 'assignment_group_id' in workload.columns and 'group_id' in assignment_groups.columns:
    group_cols = ['group_id', 'name']
    if 'service' in assignment_groups.columns:
        group_cols.append('service')
    if 'queue_type' in assignment_groups.columns:
        group_cols.append('queue_type')
    workload_enriched = workload_enriched.merge(
        assignment_groups[group_cols].rename(columns={'group_id': 'assignment_group_id', 'name': 'group_name'}),
        on='assignment_group_id', how='left'
    )

# Join workload with skills catalog
skills = dfs.get("skills_catalog.csv", pd.DataFrame())
if not skills.empty and 'required_skills' in workload.columns and 'skill_id' in skills.columns:
    skill_cols = ['skill_id', 'skill_name']
    if 'domain' in skills.columns:
        skill_cols.append('domain')

    workload_enriched = workload_enriched.merge(
        skills[skill_cols].rename(columns={'skill_id': 'required_skills', 'skill_name': 'required_skill_name'}),
        on='required_skills', how='left'
    )

if incidents.empty:
    st.error("No incidents data available")
    st.stop()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📋 All Incidents", "📊 Analytics", "⏳ Current Queue"])

with tab1:
    st.subheader("All Resolved Incidents")
    
    # Enhanced filters using enriched data
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if 'true_priority' in incidents_enriched.columns:
            priorities = ['All'] + sorted(incidents_enriched['true_priority'].dropna().unique().tolist())
            selected_priority = st.selectbox("Priority", priorities)
        else:
            selected_priority = 'All'

    with col2:
        # Use enriched category names if available
        if 'category_name' in incidents_enriched.columns:
            category_options = incidents_enriched[['category_id', 'category_name']].dropna().drop_duplicates()
            category_choices = ['All'] + [f"{row['category_name']} ({row['category_id']})"
                                        for _, row in category_options.iterrows()]
            selected_category_display = st.selectbox("Category", category_choices)
            if selected_category_display == 'All':
                selected_category = 'All'
            else:
                selected_category = selected_category_display.split('(')[-1].rstrip(')')
        elif 'category_id' in incidents_enriched.columns:
            categories_list = ['All'] + sorted(incidents_enriched['category_id'].dropna().unique().tolist())
            selected_category = st.selectbox("Category", categories_list)
        else:
            selected_category = 'All'

    with col3:
        # Use enriched service names if available
        if 'service_name' in incidents_enriched.columns:
            service_options = incidents_enriched[['service_id', 'service_name']].dropna().drop_duplicates()
            service_choices = ['All'] + [f"{row['service_name']} ({row['service_id']})"
                                       for _, row in service_options.iterrows()]
            selected_service_display = st.selectbox("Service", service_choices)
            if selected_service_display == 'All':
                selected_service = 'All'
            else:
                selected_service = selected_service_display.split('(')[-1].rstrip(')')
        elif 'service_id' in incidents_enriched.columns:
            services_list = ['All'] + sorted(incidents_enriched['service_id'].dropna().unique().tolist())
            selected_service = st.selectbox("Service", services_list)
        else:
            selected_service = 'All'

    with col4:
        # Assignment group filter
        if 'group_name' in incidents_enriched.columns:
            group_options = incidents_enriched[['true_assignment_group_id', 'group_name']].dropna().drop_duplicates()
            group_choices = ['All'] + [f"{row['group_name']} ({row['true_assignment_group_id']})"
                                     for _, row in group_options.iterrows()]
            selected_group_display = st.selectbox("Assignment Group", group_choices)
            if selected_group_display == 'All':
                selected_group = 'All'
            else:
                selected_group = selected_group_display.split('(')[-1].rstrip(')')
        else:
            selected_group = 'All'

    with col5:
        if 'location' in incidents_enriched.columns:
            locations = ['All'] + sorted(incidents_enriched['location'].dropna().unique().tolist())
            selected_location = st.selectbox("Location", locations)
        else:
            selected_location = 'All'
    
    # Apply filters to enriched data
    filtered_incidents = incidents_enriched.copy()

    if selected_priority != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['true_priority'] == selected_priority]

    if selected_category != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['category_id'] == selected_category]

    if selected_service != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['service_id'] == selected_service]

    if selected_group != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['true_assignment_group_id'] == selected_group]

    if selected_location != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['location'] == selected_location]

    # Display filtered results
    total_incidents = len(filtered_incidents)
    st.write(f"Showing {total_incidents:,} of {len(incidents):,} incidents")

    # Enhanced display columns with enriched data - prefer names over IDs
    display_columns = []
    preferred_columns = [
        'incident_id', 'created_on', 'short_description', 'true_priority',
        'category_name', 'service_name', 'group_name', 'ci_name',
        'location', 'resolution_code', 'time_to_resolve_mins'
    ]

    # Only add columns that exist, prioritizing human-readable names
    for col in preferred_columns:
        if col in filtered_incidents.columns:
            display_columns.append(col)

    # Add any other important columns that aren't IDs
    additional_columns = ['impact', 'urgency', 'channel', 'description']
    for col in additional_columns:
        if col in filtered_incidents.columns and col not in display_columns:
            display_columns.append(col)

    if display_columns and total_incidents > 0:
        # Rename columns for better display
        display_df = filtered_incidents[display_columns].copy()

        column_renames = {
            'incident_id': 'Incident ID',
            'created_on': 'Created',
            'short_description': 'Title',
            'true_priority': 'Priority',
            'category_name': 'Category',
            'service_name': 'Service',
            'group_name': 'Assigned Group',
            'ci_name': 'Configuration Item',
            'location': 'Location',
            'resolution_code': 'Resolution',
            'time_to_resolve_mins': 'Resolution Time (mins)'
        }

        display_df = display_df.rename(columns=column_renames)

        # Display the table with row selection
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
            on_select="rerun",
            selection_mode="single-row"
        )

        # Actions section
        st.write("**Actions:**")

        # Check if a row is selected
        if event.selection.rows:
            selected_row_idx = event.selection.rows[0]
            selected_row = display_df.iloc[selected_row_idx]
            incident_data = filtered_incidents.iloc[selected_row_idx]

            # Get incident ID
            if 'incident_id' in incident_data:
                selected_incident_id = incident_data['incident_id']
            else:
                selected_incident_id = f"Row_{selected_row_idx}"

            st.write(f"**Selected:** {selected_incident_id} - {selected_row.get('Title', 'No title')}")

            # Action buttons in columns
            action_cols = st.columns(4)

            with action_cols[0]:
                if st.button("👁️ View", key=f"view_{selected_incident_id}"):
                    st.session_state[f"show_details_{selected_incident_id}"] = not st.session_state.get(f"show_details_{selected_incident_id}", False)
                    st.rerun()

            with action_cols[1]:
                if st.button("✏️ Edit", key=f"edit_{selected_incident_id}"):
                    st.info("Edit functionality coming soon...")

            with action_cols[2]:
                if st.button("🗑️ Delete", key=f"delete_{selected_incident_id}"):
                    st.warning(f"Delete {selected_incident_id} - Demo mode (no actual deletion)")

            with action_cols[3]:
                if st.button("🎯 Auto-Classify", key=f"classify_{selected_incident_id}"):
                    # Get the incident data for classification
                    title = incident_data.get('short_description', '')
                    description = incident_data.get('description', '')

                    if title and description:
                        if bedrock_client.is_available():
                            with st.spinner(f"Classifying {selected_incident_id}..."):
                                # Get settings from MongoDB
                                ai_settings = settings_manager.get_ai_model_settings()
                                system_prompt = settings_manager.get_setting("system_prompts.incident_triage",
                                    "You are an expert ITSM analyst specializing in incident classification and priority assessment.")

                                model_id = ai_settings.get("selected_model_id")
                                model_name = ai_settings.get("selected_model_name", "Unknown Model")
                                max_tokens = ai_settings.get("max_tokens", 300)
                                temperature = ai_settings.get("temperature", 0.3)

                                if model_id:
                                    # Use same prompt structure as UC-02
                                    prompt = f"""Analyze this incident and determine its priority level.

                                    Incident Title: {title}
                                    Incident Description: {description}

                                    Priority Levels:
                                    - P1: Critical - System down, major business impact
                                    - P2: High - Significant impact, workaround available
                                    - P3: Medium - Moderate impact, standard response
                                    - P4: Low - Minor impact, can be scheduled

                                    Respond with:
                                    Priority: [P1/P2/P3/P4]
                                    Reasoning: [Brief explanation]
                                    """

                                    st.info(f"Using MongoDB settings: {model_name} | Tokens: {max_tokens} | Temp: {temperature}")

                                    try:
                                        response = bedrock_client.invoke_model(
                                            prompt,
                                            model_id,
                                            max_tokens,
                                            temperature,
                                            system_prompt=system_prompt
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

                                            st.success(f"**AI Classification for {selected_incident_id}:**")
                                            st.write(f"**Predicted Priority:** {priority}")
                                            st.write(f"**Reasoning:** {reasoning}")

                                            # Show the system prompt used
                                            with st.expander("🔍 Classification Details", expanded=False):
                                                st.write(f"**Model:** {model_name}")
                                                st.write(f"**Model ID:** {model_id}")
                                                st.write(f"**System Prompt:** {system_prompt}")
                                                st.write(f"**Title:** {title}")
                                                st.write(f"**Description:** {description}")
                                        else:
                                            st.error("❌ No response from AI model")
                                    except Exception as e:
                                        st.error(f"❌ Error during classification: {str(e)}")
                                else:
                                    st.warning("⚠️ No model configured. Please go to AI Features page and select a model first.")
                        else:
                            st.error("❌ AI service not available - check AWS credentials")
                    else:
                        st.warning("⚠️ Incident missing title or description")

            # Show details if requested
            if st.session_state.get(f"show_details_{selected_incident_id}", False):
                with st.expander(f"Details for {selected_incident_id}", expanded=True):
                    detail_cols = st.columns(2)
                    with detail_cols[0]:
                        for col in display_df.columns[:len(display_df.columns)//2]:
                            st.write(f"**{col}:** {selected_row[col]}")
                    with detail_cols[1]:
                        for col in display_df.columns[len(display_df.columns)//2:]:
                            st.write(f"**{col}:** {selected_row[col]}")
        else:
            st.info("👆 Click on a row in the table above to select it and perform actions")

    elif total_incidents == 0:
        st.info("No incidents match the selected filters")

with tab2:
    st.subheader("Incident Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        if 'true_priority' in incidents.columns:
            priority_counts = incidents['true_priority'].value_counts()
            fig = px.pie(values=priority_counts.values, names=priority_counts.index,
                       title='Incident Priority Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        # Resolution time distribution
        if 'time_to_resolve_mins' in incidents.columns:
            fig = px.histogram(incidents, x='time_to_resolve_mins', nbins=30,
                             title='Resolution Time Distribution (Minutes)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Category distribution
        if 'category_id' in incidents.columns:
            cat_counts = incidents['category_id'].value_counts().head(10)
            fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h',
                       title='Top 10 Incident Categories',
                       labels={'x': 'Count', 'y': 'Category'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Channel distribution
        if 'channel' in incidents.columns:
            channel_counts = incidents['channel'].value_counts()
            fig = px.bar(x=channel_counts.index, y=channel_counts.values,
                       title='Incidents by Channel',
                       labels={'x': 'Channel', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Resolution codes analysis
    if 'resolution_code' in incidents.columns:
        st.subheader("Resolution Analysis")
        resolution_counts = incidents['resolution_code'].value_counts().head(10)
        fig = px.bar(x=resolution_counts.index, y=resolution_counts.values,
                   title='Top 10 Resolution Codes',
                   labels={'x': 'Resolution Code', 'y': 'Count'})
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Current Workload Queue")
    
    if not workload.empty:
        # Queue metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Items", len(workload))
        
        with col2:
            if 'priority' in workload.columns:
                high_priority = len(workload[workload['priority'].isin(['P1', 'P2'])])
                st.metric("High Priority", high_priority)
        
        with col3:
            if 'sla_due' in workload.columns:
                # Count items due soon (within 24 hours)
                try:
                    workload['sla_due'] = pd.to_datetime(workload['sla_due'])
                    now = datetime.now()
                    due_soon = len(workload[workload['sla_due'] <= now + timedelta(hours=24)])
                    st.metric("Due Soon (24h)", due_soon)
                except:
                    st.metric("Due Soon (24h)", "N/A")
        
        with col4:
            if 'required_skills' in workload.columns:
                skilled_items = len(workload[workload['required_skills'].notna() & (workload['required_skills'] != '')])
                st.metric("Requiring Skills", skilled_items)
        
        # Current queue table with enriched data
        st.subheader("Queue Items")

        # Define preferred columns with human-readable names
        preferred_queue_columns = [
            'record_id', 'record_type', 'service_name', 'category_name',
            'priority', 'location', 'channel', 'sla_due', 'required_skill_name'
        ]

        # Build display columns list
        queue_display_columns = []
        for col in preferred_queue_columns:
            if col in workload_enriched.columns:
                queue_display_columns.append(col)

        # Add any other important columns that aren't IDs
        additional_queue_columns = ['description', 'urgency', 'impact', 'created_on']
        for col in additional_queue_columns:
            if col in workload_enriched.columns and col not in queue_display_columns:
                queue_display_columns.append(col)

        if queue_display_columns:
            # Rename columns for better display
            queue_display_df = workload_enriched[queue_display_columns].copy()

            # Sort by priority (P1 highest, P2, P3, P4, P5 lowest)
            if 'priority' in queue_display_df.columns:
                # Create priority order mapping
                priority_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
                queue_display_df['priority_sort'] = queue_display_df['priority'].map(priority_order)
                queue_display_df = queue_display_df.sort_values('priority_sort', na_position='last')
                queue_display_df = queue_display_df.drop('priority_sort', axis=1)

            queue_column_renames = {
                'record_id': 'Record ID',
                'record_type': 'Type',
                'service_name': 'Service',
                'category_name': 'Category',
                'priority': 'Priority',
                'location': 'Location',
                'channel': 'Channel',
                'sla_due': 'SLA Due',
                'required_skill_name': 'Required Skill',
                'description': 'Description',
                'urgency': 'Urgency',
                'impact': 'Impact',
                'created_on': 'Created'
            }

            queue_display_df = queue_display_df.rename(columns=queue_column_renames)

            st.dataframe(
                queue_display_df,
                use_container_width=True,
                hide_index=True,
                height=400
            )
        else:
            st.info("No queue data columns available for display")
    else:
        st.info("No current workload queue data available")
