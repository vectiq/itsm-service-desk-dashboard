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

# Get KB articles from MongoDB (both AI-generated and manually created)
mongodb_kb_articles = []
if data_ingest_manager.is_available():
    try:
        mongodb_articles = list(data_ingest_manager.kb_articles_collection.find({}, {"_id": 0}))
        mongodb_kb_articles = pd.DataFrame(mongodb_articles) if mongodb_articles else pd.DataFrame()
    except Exception as e:
        st.sidebar.warning(f"Could not load MongoDB articles: {str(e)}")
        mongodb_kb_articles = pd.DataFrame()
else:
    mongodb_kb_articles = pd.DataFrame()

# Combine CSV and MongoDB articles
kb_articles = pd.concat([kb_articles_csv, mongodb_kb_articles], ignore_index=True) if not mongodb_kb_articles.empty else kb_articles_csv
categories = dfs.get("category_tree.csv", pd.DataFrame())
services = dfs.get("services_catalog.csv", pd.DataFrame())
incidents = dfs.get("incidents_resolved.csv", pd.DataFrame())

# Create tabs for CRUD operations
tab1, tab2 = st.tabs(["📖 Browse Articles", "➕ Create Article"])

with tab1:
    st.subheader("Browse Knowledge Base Articles")

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
        ai_count = len([a for _, a in filtered_articles.iterrows() if a.get('ai_generated', False)])
        standard_count = len(filtered_articles) - ai_count
        st.write(f"Showing {len(filtered_articles):,} articles ({ai_count} AI-generated, {standard_count} standard) of {len(kb_articles):,} total")

        # Display articles
        if not filtered_articles.empty:
            for idx, article in filtered_articles.iterrows():
                # Check if this is an AI-generated article
                is_ai_generated = article.get('ai_generated', False)

                # Create title with tag and unique key
                title = article.get('title', 'Untitled Article')
                article_key = f"{title}_{article.get('_created_at', idx)}"  # Use title + timestamp as unique key
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

                        # Action buttons for AI-generated articles
                        if data_ingest_manager.is_available():
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️ Edit", key=f"edit_ai_{article_key}"):
                                    st.session_state[f"editing_article_{article_key}"] = True
                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_ai_{article_key}"):
                                    try:
                                        data_ingest_manager.kb_articles_collection.delete_one({"title": article['title'], "_created_at": article.get('_created_at')})
                                        st.success("✅ Article deleted! Please refresh the page (F5) to see the updated list.")
                                    except Exception as e:
                                        st.error(f"Error deleting article: {str(e)}")
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

                        # Action buttons for standard articles
                        if data_ingest_manager.is_available():
                            st.write("---")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️ Edit", key=f"edit_std_{article_key}"):
                                    st.session_state[f"editing_article_{article_key}"] = True
                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_std_{article_key}"):
                                    try:
                                        # For standard articles, use a different identifier
                                        delete_filter = {"title": article['title']}
                                        if 'service_id' in article and pd.notna(article['service_id']):
                                            delete_filter['service_id'] = article['service_id']
                                        data_ingest_manager.kb_articles_collection.delete_one(delete_filter)
                                        st.success("✅ Article deleted! Please refresh the page (F5) to see the updated list.")
                                    except Exception as e:
                                        st.error(f"Error deleting article: {str(e)}")

                # Show edit form if editing this article
                if st.session_state.get(f"editing_article_{article_key}", False):
                    st.write("---")
                    st.write("**Edit Article:**")

                    with st.form(f"edit_form_{article_key}"):
                        # Pre-populate form with existing data
                        edit_title = st.text_input("Title", value=article.get('title', ''))

                        if is_ai_generated:
                            # Edit structured fields
                            edit_problem = st.text_area("Problem Description", value=article.get('problem', ''), height=100)
                            edit_root_cause = st.text_area("Root Cause", value=article.get('root_cause', ''), height=100)
                            edit_solution = st.text_area("Solution Steps", value=article.get('solution', ''), height=150)
                            edit_prevention = st.text_area("Prevention", value=article.get('prevention', ''), height=100)
                            edit_tags = st.text_input("Tags", value=article.get('tags', ''))
                        else:
                            # Edit standard fields
                            edit_body = st.text_area("Content", value=article.get('body', ''), height=200)
                            edit_category = st.text_input("Category ID", value=article.get('category_id', ''))
                            edit_service = st.text_input("Service ID", value=article.get('service_id', ''))
                            edit_tags = st.text_input("Tags", value=article.get('tags', ''))
                            edit_status = st.selectbox("Status", ["Draft", "Published", "Archived"],
                                                     index=["Draft", "Published", "Archived"].index(article.get('publish_state', 'Draft')) if article.get('publish_state') in ["Draft", "Published", "Archived"] else 0)

                        col1, col2 = st.columns(2)
                        with col1:
                            save_clicked = st.form_submit_button("💾 Save Changes", type="primary")
                        with col2:
                            cancel_clicked = st.form_submit_button("❌ Cancel")

                        if save_clicked:
                            if not edit_title.strip():
                                st.error("Title is required")
                            else:
                                try:
                                    # Prepare update data
                                    update_data = {
                                        'title': edit_title.strip(),
                                        '_updated_at': pd.Timestamp.now().isoformat()
                                    }

                                    if is_ai_generated:
                                        update_data.update({
                                            'problem': edit_problem.strip(),
                                            'root_cause': edit_root_cause.strip(),
                                            'solution': edit_solution.strip(),
                                            'prevention': edit_prevention.strip(),
                                            'tags': edit_tags.strip()
                                        })
                                    else:
                                        update_data.update({
                                            'body': edit_body.strip(),
                                            'category_id': edit_category.strip(),
                                            'service_id': edit_service.strip(),
                                            'tags': edit_tags.strip(),
                                            'publish_state': edit_status
                                        })

                                    # Update in MongoDB
                                    filter_criteria = {"title": article['title']}
                                    if '_created_at' in article:
                                        filter_criteria['_created_at'] = article['_created_at']

                                    result = data_ingest_manager.kb_articles_collection.update_one(
                                        filter_criteria,
                                        {"$set": update_data}
                                    )

                                    if result.modified_count > 0:
                                        st.success("✅ Article updated successfully!")
                                        st.session_state[f"editing_article_{article_key}"] = False
                                    else:
                                        st.error("No changes were made or article not found")

                                except Exception as e:
                                    st.error(f"Error updating article: {str(e)}")

                        if cancel_clicked:
                            st.session_state[f"editing_article_{article_key}"] = False
        else:
            st.info("No articles match the selected filters")
    else:
        st.info("No knowledge base articles available")

with tab2:
    st.subheader("Create New Knowledge Base Article")

    # Create article form
    with st.form("create_article_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Article Title*", placeholder="Enter a clear, descriptive title")
            category_id = st.text_input("Category ID", placeholder="e.g., network, software, hardware")
            service_id = st.text_input("Service ID", placeholder="e.g., email, vpn, printer")

        with col2:
            publish_state = st.selectbox("Publish State", ["Draft", "Published", "Archived"], index=0)
            owner_group_id = st.text_input("Owner Group", placeholder="e.g., IT Support, Network Team")
            tags = st.text_input("Tags", placeholder="Comma-separated tags")

        # Article content
        st.write("**Article Content:**")
        article_type = st.radio("Article Type", ["Standard Article", "Structured Article (Problem/Solution)"], horizontal=True)

        if article_type == "Standard Article":
            body = st.text_area("Article Body*", height=300, placeholder="Enter the full article content...")

        else:  # Structured Article
            problem = st.text_area("Problem Description*", height=100, placeholder="Describe what users typically experience...")
            root_cause = st.text_area("Root Cause", height=100, placeholder="Explain why this issue occurs...")
            solution = st.text_area("Solution Steps*", height=150, placeholder="Provide step-by-step resolution instructions...")
            prevention = st.text_area("Prevention", height=100, placeholder="Suggest how to prevent this issue...")

        # Submit button
        submitted = st.form_submit_button("Create Article", type="primary")

        if submitted:
            # Validation
            if not title.strip():
                st.error("Article title is required")
            elif article_type == "Standard Article" and not body.strip():
                st.error("Article body is required")
            elif article_type == "Structured Article" and (not problem.strip() or not solution.strip()):
                st.error("Problem description and solution steps are required for structured articles")
            else:
                # Create article data
                new_article = {
                    'title': title.strip(),
                    'category_id': category_id.strip() if category_id.strip() else None,
                    'service_id': service_id.strip() if service_id.strip() else None,
                    'publish_state': publish_state,
                    'owner_group_id': owner_group_id.strip() if owner_group_id.strip() else None,
                    'tags': tags.strip() if tags.strip() else None,
                    'ai_generated': False
                }

                # Add content based on article type
                if article_type == "Standard Article":
                    new_article['body'] = body.strip()
                else:
                    new_article.update({
                        'problem': problem.strip(),
                        'root_cause': root_cause.strip(),
                        'solution': solution.strip(),
                        'prevention': prevention.strip()
                    })

                # Save to MongoDB
                if data_ingest_manager.is_available():
                    try:
                        # Add timestamp
                        from datetime import datetime
                        new_article['_created_at'] = datetime.now().isoformat()
                        new_article['_updated_at'] = datetime.now().isoformat()

                        # Insert into MongoDB
                        result = data_ingest_manager.kb_articles_collection.insert_one(new_article)

                        if result.inserted_id:
                            st.success(f"✅ Article '{title}' created successfully!")
                            st.info("💡 Switch to the Browse Articles tab to see your new article")
                        else:
                            st.error("Failed to create article")
                    except Exception as e:
                        st.error(f"Error creating article: {str(e)}")
                else:
                    st.error("❌ MongoDB connection not available. Cannot create article.")
