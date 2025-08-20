import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import ensure_data_loaded
from utils.data_ingest import data_ingest_manager

st.set_page_config(page_title="Knowledge Base", page_icon="📚", layout="wide")
st.title("📚 Knowledge Base")

# Ensure data is loaded
dfs = ensure_data_loaded()

# Get knowledge base data from MongoDB and CSV
kb_articles_csv = dfs.get("kb_articles.csv", pd.DataFrame())
kb_templates = dfs.get("kb_templates.csv", pd.DataFrame())

# Get AI-generated KB articles from MongoDB
ai_kb_articles = []
if data_ingest_manager.is_available():
    try:
        ai_articles = list(data_ingest_manager.kb_articles_collection.find({}, {"_id": 0}))
        ai_kb_articles = pd.DataFrame(ai_articles) if ai_articles else pd.DataFrame()
    except Exception as e:
        st.sidebar.warning(f"Could not load AI-generated articles: {str(e)}")
        ai_kb_articles = pd.DataFrame()
else:
    ai_kb_articles = pd.DataFrame()

# Combine CSV and AI-generated articles
kb_articles = pd.concat([kb_articles_csv, ai_kb_articles], ignore_index=True) if not ai_kb_articles.empty else kb_articles_csv
categories = dfs.get("category_tree.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())

# Display knowledge base articles directly (no tabs needed)
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

    # Show article counts
    ai_count = len([a for _, a in filtered_articles.iterrows() if a.get('ai_generated', False) or ('problem' in a and pd.notna(a.get('problem')))])
    standard_count = len(filtered_articles) - ai_count
    st.write(f"Showing {len(filtered_articles):,} articles ({ai_count} AI-generated, {standard_count} standard) of {len(kb_articles):,} total")

    # Display articles
    if not filtered_articles.empty:
        for idx, article in filtered_articles.iterrows():
            # Check if this is an AI-generated article
            is_ai_generated = article.get('ai_generated', False) or ('problem' in article and pd.notna(article.get('problem')))

            # Create title with tag
            title = article.get('title', 'Untitled Article')
            if is_ai_generated:
                title_display = f"{title} 🤖"
            else:
                title_display = title

            with st.expander(title_display):
                if is_ai_generated:
                    # Display AI-generated article format
                    st.markdown(f"### {article.get('title', 'Untitled Article')}")

                    if article.get('problem'):
                        st.write("**Problem Description:**")
                        st.markdown(article['problem'])

                    if article.get('root_cause'):
                        st.write("**Root Cause:**")
                        st.markdown(article['root_cause'])

                        if article.get('solution'):
                            st.write("**Solution Steps:**")
                            st.markdown(article['solution'])

                        if article.get('prevention'):
                            st.write("**Prevention:**")
                            st.markdown(article['prevention'])
                        
                        if article.get('tags'):
                            st.write("**Tags:**")
                            st.code(article['tags'])
                        
                        # Show generation metadata
                        st.write("---")
                        st.write("**Generation Info:**")
                        if article.get('source_incidents'):
                            st.write(f"Generated from {article['source_incidents']} resolved incidents")
                        if article.get('_created_at'):
                            st.write(f"Created: {article['_created_at']}")
                    else:
                        # Display standard article format
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
