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
from utils.data_service import data_service
from utils.bedrock_client import BedrockClient
from utils.settings_manager import settings_manager

st.set_page_config(page_title="Incidents Dashboard", page_icon="🎫", layout="wide")
st.title("🎫 Incidents Dashboard")

# Initialize bedrock client
bedrock_client = BedrockClient()

# Show data source info
data_source_info = data_service.get_data_source_info()
st.sidebar.info(f"**Data Source**: {data_source_info['source']}\n**Status**: {data_source_info['status']}")

# Load incidents data from MongoDB or CSV
incidents_df = data_service.get_incidents()

# Check if we have incidents data
if incidents_df.empty:
    st.error("No incidents data available. Please check the Data Management page to ingest data.")
    st.stop()

# Use the cleaned incidents data directly (already enriched with categories, services, etc.)
incidents_enriched = incidents_df.copy()

if incidents_enriched.empty:
    st.error("No incidents data available")
    st.stop()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["⏳ Current Queue", "📋 All Incidents", "📊 Analytics"])

with tab1:
    st.subheader("Current Workload Queue")

    # Load workload data
    workload = data_service.get_workload()

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
                    from datetime import datetime, timedelta
                    now = datetime.now()
                    due_soon = 0
                    for sla_due in workload['sla_due']:
                        if pd.notna(sla_due):
                            if isinstance(sla_due, str):
                                try:
                                    sla_date = pd.to_datetime(sla_due)
                                    if sla_date <= now + timedelta(hours=24):
                                        due_soon += 1
                                except:
                                    pass
                    st.metric("Due Soon", due_soon)
                except:
                    st.metric("Due Soon", "N/A")
            else:
                st.metric("Due Soon", "N/A")

        with col4:
            if 'assigned_to' in workload.columns:
                unassigned_items = len(workload[(workload['assigned_to'].isna()) | (workload['assigned_to'] == '')])
                st.metric("Unassigned", unassigned_items)
            else:
                st.metric("Unassigned", "N/A")

        # Current queue table with enriched data
        st.subheader("Queue Items")

        # Define preferred columns with human-readable names (using incident schema)
        preferred_queue_columns = [
            'incident_id', 'title', 'status', 'priority', 'urgency', 'impact',
            'service_name', 'category_name', 'location', 'channel', 'assigned_to', 'sla_due', 'created_on'
        ]

        # Build display columns list based on what's available
        queue_display_columns = []
        for col in preferred_queue_columns:
            if col in workload.columns:
                queue_display_columns.append(col)

        # Add any other important columns that aren't IDs
        additional_queue_columns = ['description', 'urgency', 'impact', 'created_on']
        for col in additional_queue_columns:
            if col in workload.columns and col not in queue_display_columns:
                queue_display_columns.append(col)

        if queue_display_columns:
            # Rename columns for better display
            queue_display_df = workload[queue_display_columns].copy()

            # Sort by priority (P1 highest, P2, P3, P4, P5 lowest)
            if 'priority' in queue_display_df.columns:
                # Create priority order mapping
                priority_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
                queue_display_df['priority_sort'] = queue_display_df['priority'].map(priority_order)
                queue_display_df = queue_display_df.sort_values('priority_sort', na_position='last')
                queue_display_df = queue_display_df.drop('priority_sort', axis=1)

            queue_column_renames = {
                'incident_id': 'Incident ID',
                'title': 'Title',
                'status': 'Status',
                'priority': 'Priority',
                'urgency': 'Urgency',
                'impact': 'Impact',
                'service_name': 'Service',
                'category_name': 'Category',
                'location': 'Location',
                'channel': 'Channel',
                'assigned_to': 'Assigned To',
                'sla_due': 'SLA Due',
                'created_on': 'Created'
            }

            queue_display_df = queue_display_df.rename(columns=queue_column_renames)

            # Display the table with row selection
            queue_event = st.dataframe(
                queue_display_df,
                use_container_width=True,
                hide_index=True,
                height=400,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Actions section for Current Queue
            st.write("**Actions:**")

            # Check if a row is selected
            if queue_event.selection.rows:
                selected_row_idx = queue_event.selection.rows[0]
                selected_row = queue_display_df.iloc[selected_row_idx]
                incident_data = workload.iloc[selected_row_idx]

                # Get incident ID
                if 'incident_id' in incident_data:
                    selected_incident_id = incident_data['incident_id']
                else:
                    selected_incident_id = f"Row_{selected_row_idx}"

                st.write(f"**Selected:** {selected_incident_id} - {selected_row.get('Title', 'No title')}")

                # Action buttons in a single panel
                st.markdown("**Available Actions:**")

                # Create a container for better visual grouping
                with st.container():
                    # Use columns for horizontal layout but keep them visually together
                    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                    with btn_col1:
                        view_clicked = st.button("👁️ View", key=f"queue_view_{selected_incident_id}", use_container_width=True)

                    with btn_col2:
                        edit_clicked = st.button("✏️ Edit", key=f"queue_edit_{selected_incident_id}", use_container_width=True)

                    with btn_col3:
                        delete_clicked = st.button("🗑️ Delete", key=f"queue_delete_{selected_incident_id}", use_container_width=True)

                    with btn_col4:
                        classify_clicked = st.button("🎯 Auto-Classify", key=f"queue_classify_{selected_incident_id}", use_container_width=True)

                    # Handle button clicks
                    if view_clicked:
                        st.session_state[f"show_queue_details_{selected_incident_id}"] = not st.session_state.get(f"show_queue_details_{selected_incident_id}", False)
                        st.rerun()

                    if edit_clicked:
                        st.info("Edit functionality coming soon...")

                    if delete_clicked:
                        st.warning(f"Delete {selected_incident_id} - Demo mode (no actual deletion)")

                    if classify_clicked:
                        # Get the incident data for classification - handle both CSV and AI-generated data
                        title = incident_data.get('short_description') or incident_data.get('title', '')
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
                                                # Show raw response for debugging
                                                with st.expander("🔍 Raw AI Response", expanded=False):
                                                    st.code(response)

                                                # Parse response with improved logic
                                                priority = "P3"  # Default
                                                reasoning = "Unable to determine"  # Default

                                                # Method 1: Look for Priority and Reasoning sections
                                                lines = response.split('\n')

                                                # Find priority
                                                for line in lines:
                                                    line = line.strip()
                                                    if line.startswith('Priority:'):
                                                        priority = line.split(':', 1)[1].strip()
                                                        break

                                                # Find reasoning - look for "Reasoning:" and capture everything after it
                                                reasoning_found = False
                                                reasoning_lines = []

                                                for line in lines:
                                                    line = line.strip()
                                                    if line.startswith('Reasoning:'):
                                                        reasoning_found = True
                                                        # Get any text after "Reasoning:" on the same line
                                                        after_colon = line.split(':', 1)[1].strip()
                                                        if after_colon:
                                                            reasoning_lines.append(after_colon)
                                                    elif reasoning_found and line:
                                                        # Continue collecting reasoning lines until we hit another section or end
                                                        if line.startswith(('Priority:', 'Confidence:', 'Summary:')):
                                                            break
                                                        reasoning_lines.append(line)

                                                # Join reasoning lines
                                                if reasoning_lines:
                                                    reasoning = '\n'.join(reasoning_lines).strip()

                                                # Method 2: If still no reasoning, try alternative parsing
                                                if reasoning == "Unable to determine":
                                                    # Look for text after "Reasoning:" in the entire response
                                                    if 'Reasoning:' in response:
                                                        parts = response.split('Reasoning:', 1)
                                                        if len(parts) > 1:
                                                            after_reasoning = parts[1].strip()
                                                            # Take everything until next section or end
                                                            next_section = None
                                                            for section in ['Priority:', 'Confidence:', 'Summary:']:
                                                                if section in after_reasoning:
                                                                    idx = after_reasoning.find(section)
                                                                    if next_section is None or idx < after_reasoning.find(next_section):
                                                                        next_section = section

                                                            if next_section:
                                                                reasoning = after_reasoning.split(next_section)[0].strip()
                                                            else:
                                                                reasoning = after_reasoning.strip()

                                                # Method 3: If still no reasoning, use everything after priority
                                                if reasoning == "Unable to determine" and 'Priority:' in response:
                                                    parts = response.split('Priority:', 1)
                                                    if len(parts) > 1:
                                                        after_priority = parts[1]
                                                        # Skip the priority line and use the rest
                                                        priority_lines = after_priority.split('\n')
                                                        if len(priority_lines) > 1:
                                                            reasoning = '\n'.join(priority_lines[1:]).strip()

                                                # Clean up priority (extract just P1, P2, P3, P4)
                                                import re
                                                priority_match = re.search(r'P[1-4]', priority.upper())
                                                if priority_match:
                                                    priority = priority_match.group()

                                                st.success(f"**AI Classification for {selected_incident_id}:**")
                                                st.write(f"**Predicted Priority:** {priority}")
                                                st.markdown(f"**Reasoning:**")
                                                st.markdown(reasoning)

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
                if st.session_state.get(f"show_queue_details_{selected_incident_id}", False):
                    with st.expander(f"Details for {selected_incident_id}", expanded=True):
                        detail_cols = st.columns(2)
                        with detail_cols[0]:
                            for col in queue_display_df.columns[:len(queue_display_df.columns)//2]:
                                st.write(f"**{col}:** {selected_row[col]}")
                        with detail_cols[1]:
                            for col in queue_display_df.columns[len(queue_display_df.columns)//2:]:
                                st.write(f"**{col}:** {selected_row[col]}")
            else:
                st.info("👆 Click on a row in the table above to select it and perform actions")

        else:
            st.info("No queue data columns available for display")
    else:
        st.info("No current workload queue data available")

with tab2:
    st.subheader("All Incidents")

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
        # Status filter
        if 'status' in incidents_enriched.columns:
            statuses = ['All'] + sorted(incidents_enriched['status'].dropna().unique().tolist())
            selected_status = st.selectbox("Status", statuses)
        else:
            selected_status = 'All'

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

    if selected_status != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['status'] == selected_status]

    # Display filtered results
    total_incidents = len(filtered_incidents)
    st.write(f"Showing {total_incidents:,} of {len(incidents_enriched):,} incidents")

    # Enhanced display columns - handle both CSV and AI-generated formats
    display_columns = []

    # Define column mappings for different data sources
    column_mappings = [
        # (preferred_column, fallback_column, display_name)
        ('incident_id', None, 'Incident ID'),
        ('created_on', None, 'Created'),
        ('short_description', 'title', 'Title'),  # CSV vs AI-generated
        ('description', None, 'Description'),  # Add description column
        ('true_priority', 'priority', 'Priority'),  # CSV vs AI-generated
        ('status', None, 'Status'),
        ('category_name', 'category', 'Category'),  # Enriched vs AI-generated readable
        ('service_name', 'service', 'Service'),  # Enriched vs AI-generated readable
        ('urgency', None, 'Urgency'),
        ('impact', None, 'Impact'),
        ('assigned_to', None, 'Assigned To'),
        ('resolution_notes', None, 'Resolution Notes'),
        ('resolved_date', None, 'Resolved Date'),
        ('created_by', None, 'Created By'),
        ('location', None, 'Location'),
    ]

    # Build display columns based on what's available
    column_renames = {}
    for preferred, fallback, display_name in column_mappings:
        if preferred in filtered_incidents.columns:
            display_columns.append(preferred)
            column_renames[preferred] = display_name
        elif fallback and fallback in filtered_incidents.columns:
            display_columns.append(fallback)
            column_renames[fallback] = display_name

    if display_columns and total_incidents > 0:
        # Create display dataframe with selected columns
        display_df = filtered_incidents[display_columns].copy()

        # Apply column renames (already built above)
        display_df = display_df.rename(columns=column_renames)

        # Display the table (read-only)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # All Incidents table is read-only - actions available in Current Queue tab
        st.info("💡 This table is read-only. Use the Current Queue tab to perform actions on incidents.")

    elif total_incidents == 0:
        st.info("No incidents match the selected filters")

with tab3:
    st.subheader("Incident Analytics")

    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        if 'true_priority' in incidents_enriched.columns:
            priority_counts = incidents_enriched['true_priority'].value_counts()
            fig = px.pie(values=priority_counts.values, names=priority_counts.index,
                       title='Incident Priority Distribution')
            st.plotly_chart(fig, use_container_width=True)

        # Resolution time distribution
        if 'time_to_resolve_mins' in incidents_enriched.columns:
            fig = px.histogram(incidents_enriched, x='time_to_resolve_mins', nbins=30,
                             title='Resolution Time Distribution (Minutes)')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Category distribution
        if 'category_id' in incidents_enriched.columns:
            cat_counts = incidents_enriched['category_id'].value_counts().head(10)
            fig = px.bar(x=cat_counts.values, y=cat_counts.index, orientation='h',
                       title='Top 10 Incident Categories',
                       labels={'x': 'Count', 'y': 'Category'})
            st.plotly_chart(fig, use_container_width=True)

        # Channel distribution
        if 'channel' in incidents_enriched.columns:
            channel_counts = incidents_enriched['channel'].value_counts()
            fig = px.bar(x=channel_counts.index, y=channel_counts.values,
                       title='Incidents by Channel',
                       labels={'x': 'Channel', 'y': 'Count'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Resolution codes analysis
    if 'resolution_code' in incidents_enriched.columns:
        st.subheader("Resolution Analysis")
        resolution_counts = incidents_enriched['resolution_code'].value_counts().head(10)
        fig = px.bar(x=resolution_counts.index, y=resolution_counts.values,
                   title='Top 10 Resolution Codes',
                   labels={'x': 'Resolution Code', 'y': 'Count'})
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Current Workload Queue")

    # Load workload data
    workload = data_service.get_workload()

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
            if 'assigned_to' in workload.columns:
                unassigned_items = len(workload[(workload['assigned_to'].isna()) | (workload['assigned_to'] == '')])
                st.metric("Unassigned", unassigned_items)
        
        # Current queue table with enriched data
        st.subheader("Queue Items")

        # Define preferred columns with human-readable names (using incident schema)
        preferred_queue_columns = [
            'incident_id', 'title', 'status', 'priority', 'urgency', 'impact',
            'service_name', 'category_name', 'location', 'channel', 'assigned_to', 'sla_due'
        ]

        # Build display columns list
        queue_display_columns = []
        for col in preferred_queue_columns:
            if col in workload.columns:
                queue_display_columns.append(col)

        # Add any other important columns that aren't IDs
        additional_queue_columns = ['description', 'urgency', 'impact', 'created_on']
        for col in additional_queue_columns:
            if col in workload.columns and col not in queue_display_columns:
                queue_display_columns.append(col)

        if queue_display_columns:
            # Rename columns for better display
            queue_display_df = workload[queue_display_columns].copy()

            # Sort by priority (P1 highest, P2, P3, P4, P5 lowest)
            if 'priority' in queue_display_df.columns:
                # Create priority order mapping
                priority_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
                queue_display_df['priority_sort'] = queue_display_df['priority'].map(priority_order)
                queue_display_df = queue_display_df.sort_values('priority_sort', na_position='last')
                queue_display_df = queue_display_df.drop('priority_sort', axis=1)

            queue_column_renames = {
                'incident_id': 'Incident ID',
                'title': 'Title',
                'status': 'Status',
                'priority': 'Priority',
                'urgency': 'Urgency',
                'impact': 'Impact',
                'service_name': 'Service',
                'category_name': 'Category',
                'location': 'Location',
                'channel': 'Channel',
                'assigned_to': 'Assigned To',
                'sla_due': 'SLA Due',
                'created_on': 'Created'
            }

            queue_display_df = queue_display_df.rename(columns=queue_column_renames)

            # Display the table with row selection
            queue_event = st.dataframe(
                queue_display_df,
                use_container_width=True,
                hide_index=True,
                height=400,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Actions section for Current Queue
            st.write("**Actions:**")

            # Check if a row is selected
            if queue_event.selection.rows:
                selected_row_idx = queue_event.selection.rows[0]
                selected_row = queue_display_df.iloc[selected_row_idx]
                incident_data = workload.iloc[selected_row_idx]

                # Get incident ID
                if 'incident_id' in incident_data:
                    selected_incident_id = incident_data['incident_id']
                else:
                    selected_incident_id = f"Row_{selected_row_idx}"

                st.write(f"**Selected:** {selected_incident_id} - {selected_row.get('Title', 'No title')}")

                # Action buttons in a single panel
                st.markdown("**Available Actions:**")

                # Create a container for better visual grouping
                with st.container():
                    # Use columns for horizontal layout but keep them visually together
                    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                    with btn_col1:
                        view_clicked = st.button("👁️ View", key=f"queue_view_{selected_incident_id}", use_container_width=True)

                    with btn_col2:
                        edit_clicked = st.button("✏️ Edit", key=f"queue_edit_{selected_incident_id}", use_container_width=True)

                    with btn_col3:
                        delete_clicked = st.button("🗑️ Delete", key=f"queue_delete_{selected_incident_id}", use_container_width=True)

                    with btn_col4:
                        classify_clicked = st.button("🎯 Auto-Classify", key=f"queue_classify_{selected_incident_id}", use_container_width=True)

                    # Handle button clicks
                    if view_clicked:
                        st.session_state[f"show_queue_details_{selected_incident_id}"] = not st.session_state.get(f"show_queue_details_{selected_incident_id}", False)
                        st.rerun()

                    if edit_clicked:
                        st.info("Edit functionality coming soon...")

                    if delete_clicked:
                        st.warning(f"Delete {selected_incident_id} - Demo mode (no actual deletion)")

                    if classify_clicked:
                        # Get the incident data for classification - handle both CSV and AI-generated data
                        title = incident_data.get('short_description') or incident_data.get('title', '')
                        description = incident_data.get('description', '')

                        if title and description:
                            st.info("Auto-classification functionality available - configure AI model in AI Features page")
                        else:
                            st.warning("⚠️ Incident missing title or description")

                # Show details if requested
                if st.session_state.get(f"show_queue_details_{selected_incident_id}", False):
                    with st.expander(f"Details for {selected_incident_id}", expanded=True):
                        detail_cols = st.columns(2)
                        with detail_cols[0]:
                            for col in queue_display_df.columns[:len(queue_display_df.columns)//2]:
                                st.write(f"**{col}:** {selected_row[col]}")
                        with detail_cols[1]:
                            for col in queue_display_df.columns[len(queue_display_df.columns)//2:]:
                                st.write(f"**{col}:** {selected_row[col]}")
            else:
                st.info("👆 Click on a row in the table above to select it and perform actions")

        else:
            st.info("No queue data columns available for display")
    else:
        st.info("No current workload queue data available")
