import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Incidents Dashboard", page_icon="🎫", layout="wide")
st.title("🎫 Incidents Dashboard")

dfs = st.session_state.get("dfs", {})
if not dfs:
    st.warning("Load data on the Home page first")
    st.stop()

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
    incidents_enriched = incidents_enriched.merge(
        services[['service_id', 'name', 'criticality']].rename(columns={'name': 'service_name'}),
        on='service_id', how='left'
    )

# Join with categories
if not categories.empty and 'category_id' in incidents.columns and 'category_id' in categories.columns:
    incidents_enriched = incidents_enriched.merge(
        categories[['category_id', 'name', 'parent_id']].rename(columns={'name': 'category_name'}),
        on='category_id', how='left'
    )

# Join with assignment groups
if not assignment_groups.empty and 'true_assignment_group_id' in incidents.columns and 'group_id' in assignment_groups.columns:
    incidents_enriched = incidents_enriched.merge(
        assignment_groups[['group_id', 'name']].rename(columns={'group_id': 'true_assignment_group_id', 'name': 'group_name'}),
        on='true_assignment_group_id', how='left'
    )

# Join with CMDB CIs
if not cmdb_ci.empty and 'ci_id' in incidents.columns and 'ci_id' in cmdb_ci.columns:
    incidents_enriched = incidents_enriched.merge(
        cmdb_ci[['ci_id', 'name', 'type']].rename(columns={'name': 'ci_name', 'type': 'ci_type'}),
        on='ci_id', how='left'
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
    st.write(f"Showing {len(filtered_incidents):,} of {len(incidents):,} incidents")

    # Enhanced display columns with enriched data
    display_columns = []
    preferred_columns = [
        'incident_id', 'created_on', 'short_description', 'true_priority',
        'category_name', 'service_name', 'group_name', 'ci_name',
        'location', 'resolution_code', 'time_to_resolve_mins'
    ]

    # Fallback to original columns if enriched ones don't exist
    fallback_columns = [
        'incident_id', 'created_on', 'short_description', 'true_priority',
        'category_id', 'service_id', 'true_assignment_group_id', 'ci_id',
        'location', 'resolution_code', 'time_to_resolve_mins'
    ]

    for col in preferred_columns:
        if col in filtered_incidents.columns:
            display_columns.append(col)
        elif col.replace('_name', '_id') in filtered_incidents.columns:
            display_columns.append(col.replace('_name', '_id'))

    # Add any missing essential columns
    for col in fallback_columns:
        if col in filtered_incidents.columns and col not in display_columns:
            display_columns.append(col)

    if display_columns:
        # Rename columns for better display
        display_df = filtered_incidents[display_columns].head(100).copy()

        column_renames = {
            'incident_id': 'Incident ID',
            'created_on': 'Created',
            'short_description': 'Description',
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

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        if len(filtered_incidents) > 100:
            st.info(f"Showing first 100 rows. Total: {len(filtered_incidents):,} incidents")

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
        
        # Current queue table
        st.subheader("Queue Items")
        queue_columns = []
        for col in ['record_id', 'record_type', 'service_id', 'category_id', 'priority', 'location', 'channel', 'sla_due', 'required_skills']:
            if col in workload.columns:
                queue_columns.append(col)
        
        if queue_columns:
            st.dataframe(workload[queue_columns], use_container_width=True, hide_index=True)
    else:
        st.info("No current workload queue data available")
