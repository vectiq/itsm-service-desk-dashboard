import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import ensure_data_loaded

st.set_page_config(page_title="Knowledge Base", page_icon="📚", layout="wide")
st.title("📚 Knowledge Base")

# Ensure data is loaded
dfs = ensure_data_loaded()

# Get knowledge base data
kb_articles = dfs.get("kb_articles.csv", pd.DataFrame())
kb_templates = dfs.get("kb_templates.csv", pd.DataFrame())
categories = dfs.get("category_tree.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())

# Create tabs for different KB views
tab1, tab2, tab3 = st.tabs(["📄 Articles", "📋 Templates", "📊 Analytics"])

with tab1:
    st.subheader("Knowledge Base Articles")
    
    if not kb_articles.empty:
        # Filters for articles
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'service_id' in kb_articles.columns:
                services_list = ['All'] + sorted(kb_articles['service_id'].dropna().unique().tolist())
                selected_service = st.selectbox("Service", services_list, key="articles_service")
            else:
                selected_service = 'All'
        
        with col2:
            if 'category_id' in kb_articles.columns:
                categories_list = ['All'] + sorted(kb_articles['category_id'].dropna().unique().tolist())
                selected_category = st.selectbox("Category", categories_list, key="articles_category")
            else:
                selected_category = 'All'
        
        with col3:
            if 'publish_state' in kb_articles.columns:
                states = ['All'] + sorted(kb_articles['publish_state'].dropna().unique().tolist())
                selected_state = st.selectbox("Publish State", states, key="articles_state")
            else:
                selected_state = 'All'
        
        # Apply filters
        filtered_articles = kb_articles.copy()
        
        if selected_service != 'All':
            filtered_articles = filtered_articles[filtered_articles['service_id'] == selected_service]
        
        if selected_category != 'All':
            filtered_articles = filtered_articles[filtered_articles['category_id'] == selected_category]
        
        if selected_state != 'All':
            filtered_articles = filtered_articles[filtered_articles['publish_state'] == selected_state]
        
        st.write(f"Showing {len(filtered_articles):,} of {len(kb_articles):,} articles")
        
        # Display articles
        if not filtered_articles.empty:
            for idx, article in filtered_articles.iterrows():
                with st.expander(f"📄 {article.get('title', 'Untitled Article')} (ID: {article.get('article_id', 'N/A')})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if 'body' in article and pd.notna(article['body']):
                            st.write("**Content:**")
                            st.write(article['body'])
                        else:
                            st.write("*No content available*")
                    
                    with col2:
                        st.write("**Details:**")
                        if 'service_id' in article and pd.notna(article['service_id']):
                            st.write(f"**Service:** {article['service_id']}")
                        if 'category_id' in article and pd.notna(article['category_id']):
                            st.write(f"**Category:** {article['category_id']}")
                        if 'tags' in article and pd.notna(article['tags']):
                            st.write(f"**Tags:** {article['tags']}")
                        if 'publish_state' in article and pd.notna(article['publish_state']):
                            st.write(f"**Status:** {article['publish_state']}")
                        if 'owner_group_id' in article and pd.notna(article['owner_group_id']):
                            st.write(f"**Owner:** {article['owner_group_id']}")
        else:
            st.info("No articles match the selected filters")
    else:
        st.info("No knowledge base articles available")

with tab2:
    st.subheader("Knowledge Base Templates")
    
    if not kb_templates.empty:
        # Display templates
        st.write(f"Total templates: {len(kb_templates):,}")
        
        # Show templates in expandable sections
        for idx, template in kb_templates.iterrows():
            template_title = template.get('template_name', f'Template {idx + 1}')
            
            with st.expander(f"📋 {template_title}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if 'template_body' in template and pd.notna(template['template_body']):
                        st.write("**Template Content:**")
                        st.code(template['template_body'], language='text')
                    else:
                        st.write("*No template content available*")
                
                with col2:
                    st.write("**Template Details:**")
                    for col_name in template.index:
                        if col_name not in ['template_body'] and pd.notna(template[col_name]):
                            st.write(f"**{col_name.replace('_', ' ').title()}:** {template[col_name]}")
    else:
        st.info("No knowledge base templates available")

with tab3:
    st.subheader("Knowledge Base Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # KB Articles by category
        if not kb_articles.empty and 'category_id' in kb_articles.columns:
            cat_counts = kb_articles['category_id'].value_counts()
            if not cat_counts.empty:
                fig = px.pie(values=cat_counts.values, names=cat_counts.index,
                           title='KB Articles by Category')
                st.plotly_chart(fig, use_container_width=True)
        
        # KB coverage vs incidents
        if not incidents.empty and not kb_articles.empty:
            st.subheader("Knowledge Coverage Analysis")
            
            # Get incident categories
            if 'category_id' in incidents.columns:
                incident_cats = set(incidents['category_id'].dropna().unique())
                kb_cats = set(kb_articles['category_id'].dropna().unique()) if 'category_id' in kb_articles.columns else set()
                
                coverage_data = {
                    'Category': 'Knowledge Coverage',
                    'Covered': len(incident_cats & kb_cats),
                    'Not Covered': len(incident_cats - kb_cats)
                }
                
                fig = go.Figure(data=[
                    go.Bar(name='Covered', x=['Categories'], y=[coverage_data['Covered']]),
                    go.Bar(name='Not Covered', x=['Categories'], y=[coverage_data['Not Covered']])
                ])
                fig.update_layout(title='Incident Categories with KB Coverage', barmode='stack')
                st.plotly_chart(fig, use_container_width=True)
                
                # Show uncovered categories
                uncovered = incident_cats - kb_cats
                if uncovered:
                    st.write("**Categories without KB coverage:**")
                    for cat in sorted(uncovered):
                        st.write(f"• {cat}")
    
    with col2:
        # KB Articles by service
        if not kb_articles.empty and 'service_id' in kb_articles.columns:
            service_counts = kb_articles['service_id'].value_counts()
            if not service_counts.empty:
                fig = px.bar(x=service_counts.index, y=service_counts.values,
                           title='KB Articles by Service',
                           labels={'x': 'Service', 'y': 'Article Count'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Template usage analysis
        if not kb_templates.empty:
            st.subheader("Template Statistics")
            st.metric("Total Templates", len(kb_templates))
            
            # Show template types if available
            template_cols = kb_templates.columns.tolist()
            st.write("**Available Template Fields:**")
            for col in template_cols:
                st.write(f"• {col.replace('_', ' ').title()}")
    
    # Overall KB metrics
    st.subheader("Overall Knowledge Base Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_articles = len(kb_articles) if not kb_articles.empty else 0
        st.metric("Total Articles", total_articles)
    
    with col2:
        total_templates = len(kb_templates) if not kb_templates.empty else 0
        st.metric("Total Templates", total_templates)
    
    with col3:
        if not kb_articles.empty and 'publish_state' in kb_articles.columns:
            published = len(kb_articles[kb_articles['publish_state'] == 'Published'])
            st.metric("Published Articles", published)
        else:
            st.metric("Published Articles", "N/A")
    
    with col4:
        total_kb_items = total_articles + total_templates
        st.metric("Total KB Items", total_kb_items)
