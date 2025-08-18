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

# Get incidents data
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())
workload = dfs.get("workload_queue.csv", pd.DataFrame())
categories = dfs.get("category_tree.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())

if incidents.empty:
    st.error("No incidents data available")
    st.stop()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["📋 All Incidents", "📊 Analytics", "⏳ Current Queue"])

with tab1:
    st.subheader("All Resolved Incidents")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'true_priority' in incidents.columns:
            priorities = ['All'] + sorted(incidents['true_priority'].dropna().unique().tolist())
            selected_priority = st.selectbox("Priority", priorities)
        else:
            selected_priority = 'All'
    
    with col2:
        if 'category_id' in incidents.columns:
            categories_list = ['All'] + sorted(incidents['category_id'].dropna().unique().tolist())
            selected_category = st.selectbox("Category", categories_list)
        else:
            selected_category = 'All'
    
    with col3:
        if 'service_id' in incidents.columns:
            services_list = ['All'] + sorted(incidents['service_id'].dropna().unique().tolist())
            selected_service = st.selectbox("Service", services_list)
        else:
            selected_service = 'All'
    
    with col4:
        if 'location' in incidents.columns:
            locations = ['All'] + sorted(incidents['location'].dropna().unique().tolist())
            selected_location = st.selectbox("Location", locations)
        else:
            selected_location = 'All'
    
    # Apply filters
    filtered_incidents = incidents.copy()
    
    if selected_priority != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['true_priority'] == selected_priority]
    
    if selected_category != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['category_id'] == selected_category]
    
    if selected_service != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['service_id'] == selected_service]
    
    if selected_location != 'All':
        filtered_incidents = filtered_incidents[filtered_incidents['location'] == selected_location]
    
    # Display filtered results
    st.write(f"Showing {len(filtered_incidents):,} of {len(incidents):,} incidents")
    
    # Display incidents table
    display_columns = []
    for col in ['incident_id', 'created_on', 'short_description', 'true_priority', 'category_id', 'service_id', 'location', 'resolution_code', 'time_to_resolve_mins']:
        if col in filtered_incidents.columns:
            display_columns.append(col)
    
    if display_columns:
        st.dataframe(
            filtered_incidents[display_columns].head(100),
            use_container_width=True,
            hide_index=True
        )
        
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
