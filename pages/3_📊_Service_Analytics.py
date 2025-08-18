import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Service Analytics", page_icon="📊", layout="wide")
st.title("📊 Service Analytics")

dfs = st.session_state.get("dfs", {})
if not dfs:
    st.warning("Load data on the Home page first")
    st.stop()

# Get data
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())
categories = dfs.get("category_tree.csv", pd.DataFrame())
workload = dfs.get("workload_queue.csv", pd.DataFrame())
priority_matrix = dfs.get("priority_matrix.csv", pd.DataFrame())

# Create tabs for different analytics views
tab1, tab2, tab3 = st.tabs(["🔧 Service Performance", "📈 Trends", "🎯 SLA Analysis"])

with tab1:
    st.subheader("Service Performance Overview")
    
    if not services.empty:
        # Service catalog overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Services", len(services))
        
        with col2:
            if 'criticality' in services.columns:
                critical_services = len(services[services['criticality'] == 'Critical'])
                st.metric("Critical Services", critical_services)
        
        with col3:
            if 'criticality' in services.columns:
                high_services = len(services[services['criticality'] == 'High'])
                st.metric("High Priority Services", high_services)
        
        # Service details table
        st.subheader("Service Catalog")
        display_cols = []
        for col in ['service_id', 'name', 'criticality', 'service_owner_id']:
            if col in services.columns:
                display_cols.append(col)
        
        if display_cols:
            st.dataframe(services[display_cols], use_container_width=True, hide_index=True)
    
    # Service incident analysis
    if not incidents.empty and not services.empty:
        st.subheader("Service Incident Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Incidents by service
            if 'service_id' in incidents.columns:
                service_incidents = incidents['service_id'].value_counts().head(10)
                fig = px.bar(x=service_incidents.values, y=service_incidents.index, orientation='h',
                           title='Top 10 Services by Incident Count',
                           labels={'x': 'Incident Count', 'y': 'Service'})
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Average resolution time by service
            if 'service_id' in incidents.columns and 'time_to_resolve_mins' in incidents.columns:
                avg_resolution = incidents.groupby('service_id')['time_to_resolve_mins'].mean().sort_values(ascending=False).head(10)
                fig = px.bar(x=avg_resolution.values, y=avg_resolution.index, orientation='h',
                           title='Top 10 Services by Avg Resolution Time',
                           labels={'x': 'Avg Resolution Time (mins)', 'y': 'Service'})
                st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Service Trends")
    
    if not incidents.empty:
        # Time-based analysis
        if 'created_on' in incidents.columns:
            try:
                incidents['created_on'] = pd.to_datetime(incidents['created_on'])
                incidents['date'] = incidents['created_on'].dt.date
                
                # Daily incident trend
                daily_incidents = incidents.groupby('date').size().reset_index(name='count')
                fig = px.line(daily_incidents, x='date', y='count',
                            title='Daily Incident Trend')
                st.plotly_chart(fig, use_container_width=True)
                
                # Incidents by day of week
                incidents['day_of_week'] = incidents['created_on'].dt.day_name()
                dow_counts = incidents['day_of_week'].value_counts()
                # Reorder by actual day order
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                dow_counts = dow_counts.reindex([day for day in day_order if day in dow_counts.index])
                
                fig = px.bar(x=dow_counts.index, y=dow_counts.values,
                           title='Incidents by Day of Week',
                           labels={'x': 'Day of Week', 'y': 'Incident Count'})
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.warning(f"Could not parse date information: {str(e)}")
        
        # Category trends
        if 'category_id' in incidents.columns:
            st.subheader("Category Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top categories
                cat_counts = incidents['category_id'].value_counts().head(10)
                fig = px.bar(x=cat_counts.index, y=cat_counts.values,
                           title='Top 10 Incident Categories',
                           labels={'x': 'Category', 'y': 'Count'})
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Category hierarchy if available
                if not categories.empty and 'parent_id' in categories.columns:
                    st.write("**Category Hierarchy:**")
                    
                    # Show parent categories
                    parent_cats = categories[categories['parent_id'].isna() | (categories['parent_id'] == '')]
                    for _, parent in parent_cats.iterrows():
                        st.write(f"**{parent['name']}** ({parent['category_id']})")
                        
                        # Show child categories
                        children = categories[categories['parent_id'] == parent['category_id']]
                        for _, child in children.iterrows():
                            incident_count = len(incidents[incidents['category_id'] == child['category_id']]) if 'category_id' in incidents.columns else 0
                            st.write(f"  • {child['name']} ({child['category_id']}) - {incident_count} incidents")

with tab3:
    st.subheader("SLA and Priority Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority distribution
        if 'true_priority' in incidents.columns:
            priority_counts = incidents['true_priority'].value_counts()
            fig = px.pie(values=priority_counts.values, names=priority_counts.index,
                       title='Incident Priority Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        # Impact vs Urgency analysis
        if 'impact' in incidents.columns and 'urgency' in incidents.columns:
            impact_urgency = incidents.groupby(['impact', 'urgency']).size().reset_index(name='count')
            if not impact_urgency.empty:
                fig = px.density_heatmap(impact_urgency, x='urgency', y='impact', z='count',
                                       title='Impact vs Urgency Matrix')
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Resolution time analysis
        if 'time_to_resolve_mins' in incidents.columns:
            # Resolution time by priority
            if 'true_priority' in incidents.columns:
                fig = px.box(incidents, x='true_priority', y='time_to_resolve_mins',
                           title='Resolution Time by Priority')
                st.plotly_chart(fig, use_container_width=True)
            
            # Resolution time statistics
            st.subheader("Resolution Time Statistics")
            resolution_stats = incidents['time_to_resolve_mins'].describe()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Average Resolution", f"{resolution_stats['mean']:.1f} mins")
                st.metric("Median Resolution", f"{resolution_stats['50%']:.1f} mins")
            
            with col_b:
                st.metric("Fastest Resolution", f"{resolution_stats['min']:.1f} mins")
                st.metric("Slowest Resolution", f"{resolution_stats['max']:.1f} mins")
    
    # Current queue SLA analysis
    if not workload.empty:
        st.subheader("Current Queue SLA Status")
        
        if 'sla_due' in workload.columns:
            try:
                workload['sla_due'] = pd.to_datetime(workload['sla_due'])
                now = datetime.now()
                
                # SLA status
                overdue = len(workload[workload['sla_due'] < now])
                due_today = len(workload[(workload['sla_due'] >= now) & (workload['sla_due'] < now + timedelta(days=1))])
                due_soon = len(workload[(workload['sla_due'] >= now + timedelta(days=1)) & (workload['sla_due'] < now + timedelta(days=3))])
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Queue", len(workload))
                
                with col2:
                    st.metric("🚨 Overdue", overdue, delta=f"{overdue/len(workload)*100:.1f}%" if len(workload) > 0 else "0%")
                
                with col3:
                    st.metric("⚠️ Due Today", due_today)
                
                with col4:
                    st.metric("📅 Due Soon (3d)", due_soon)
                
            except Exception as e:
                st.warning(f"Could not parse SLA due dates: {str(e)}")
    
    # Priority matrix if available
    if not priority_matrix.empty:
        st.subheader("Priority Matrix Configuration")
        st.dataframe(priority_matrix, use_container_width=True, hide_index=True)
