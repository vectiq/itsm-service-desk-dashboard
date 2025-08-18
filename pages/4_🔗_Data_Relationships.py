import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Data Relationships", page_icon="🔗", layout="wide")
st.title("🔗 Data Relationships & Quality")

dfs = st.session_state.get("dfs", {})
if not dfs:
    st.warning("Load data on the Home page first")
    st.stop()

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["🗂️ Data Catalog", "🔗 Relationships", "✅ Quality Checks", "📊 Data Lineage"])

with tab1:
    st.subheader("Data Catalog Overview")
    
    # Create comprehensive data catalog
    catalog_data = []
    
    # Define file categories as per requirements
    reference_files = [
        "dataset_catalog.csv", "services_catalog.csv", "category_tree.csv", "cmdb_ci.csv",
        "users_agents.csv", "assignment_groups.csv", "agent_group_membership.csv",
        "skills_catalog.csv", "agent_skills.csv", "synonyms_glossary.csv", "priority_matrix.csv"
    ]
    
    fact_files = ["incidents_resolved.csv"]
    
    live_files = [
        "workload_queue.csv", "agent_capacity_snapshots.csv", 
        "agent_performance_history.csv", "schedules.csv"
    ]
    
    kb_files = ["kb_templates.csv", "kb_articles.csv"]
    
    # Build catalog
    for filename, df in dfs.items():
        if filename in reference_files:
            category = "📋 Reference Data"
        elif filename in fact_files:
            category = "📊 Historical Facts"
        elif filename in live_files:
            category = "⚡ Live/Demo Data"
        elif filename in kb_files:
            category = "📚 Knowledge Base"
        else:
            category = "🔍 Other"
        
        catalog_data.append({
            "File": filename,
            "Category": category,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Memory (MB)": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "Key Columns": ", ".join(df.columns[:5].tolist()) + ("..." if len(df.columns) > 5 else "")
        })
    
    catalog_df = pd.DataFrame(catalog_data).sort_values(["Category", "File"])
    
    # Display by category
    for category in catalog_df["Category"].unique():
        st.subheader(category)
        category_data = catalog_df[catalog_df["Category"] == category].drop("Category", axis=1)
        st.dataframe(category_data, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Data Relationships & Foreign Keys")
    
    # Define key relationships as per requirements
    relationships = [
        {
            "From Table": "incidents_resolved.csv",
            "From Column": "service_id",
            "To Table": "services_catalog.csv", 
            "To Column": "service_id",
            "Relationship": "Many-to-One",
            "Purpose": "Link incidents to services"
        },
        {
            "From Table": "incidents_resolved.csv",
            "From Column": "category_id",
            "To Table": "category_tree.csv",
            "To Column": "category_id", 
            "Relationship": "Many-to-One",
            "Purpose": "Categorize incidents"
        },
        {
            "From Table": "incidents_resolved.csv",
            "From Column": "ci_id",
            "To Table": "cmdb_ci.csv",
            "To Column": "ci_id",
            "Relationship": "Many-to-One", 
            "Purpose": "Link to configuration items"
        },
        {
            "From Table": "incidents_resolved.csv",
            "From Column": "true_assignment_group_id",
            "To Table": "assignment_groups.csv",
            "To Column": "group_id",
            "Relationship": "Many-to-One",
            "Purpose": "Track assigned groups"
        },
        {
            "From Table": "agent_skills.csv",
            "From Column": "agent_id", 
            "To Table": "users_agents.csv",
            "To Column": "agent_id",
            "Relationship": "Many-to-One",
            "Purpose": "Agent skill assignments"
        },
        {
            "From Table": "agent_skills.csv",
            "From Column": "skill_id",
            "To Table": "skills_catalog.csv", 
            "To Column": "skill_id",
            "Relationship": "Many-to-One",
            "Purpose": "Define skill types"
        },
        {
            "From Table": "agent_group_membership.csv",
            "From Column": "agent_id",
            "To Table": "users_agents.csv",
            "To Column": "agent_id", 
            "Relationship": "Many-to-One",
            "Purpose": "Agent group memberships"
        },
        {
            "From Table": "agent_group_membership.csv",
            "From Column": "group_id",
            "To Table": "assignment_groups.csv",
            "To Column": "group_id",
            "Relationship": "Many-to-One", 
            "Purpose": "Group definitions"
        },
        {
            "From Table": "workload_queue.csv",
            "From Column": "service_id",
            "To Table": "services_catalog.csv",
            "To Column": "service_id",
            "Relationship": "Many-to-One",
            "Purpose": "Queue item services"
        }
    ]
    
    relationships_df = pd.DataFrame(relationships)
    st.dataframe(relationships_df, use_container_width=True, hide_index=True)
    
    # Relationship validation
    st.subheader("Relationship Integrity Check")
    
    integrity_results = []
    
    for rel in relationships:
        from_table = rel["From Table"]
        from_col = rel["From Column"] 
        to_table = rel["To Table"]
        to_col = rel["To Column"]
        
        if from_table in dfs and to_table in dfs:
            from_df = dfs[from_table]
            to_df = dfs[to_table]
            
            if from_col in from_df.columns and to_col in to_df.columns:
                # Check referential integrity
                from_values = set(from_df[from_col].dropna().astype(str))
                to_values = set(to_df[to_col].dropna().astype(str))
                
                missing_refs = from_values - to_values
                integrity_pct = ((len(from_values) - len(missing_refs)) / len(from_values) * 100) if from_values else 100
                
                integrity_results.append({
                    "Relationship": f"{from_table}.{from_col} → {to_table}.{to_col}",
                    "Integrity %": f"{integrity_pct:.1f}%",
                    "Missing References": len(missing_refs),
                    "Status": "✅ Good" if integrity_pct >= 90 else "⚠️ Issues" if integrity_pct >= 70 else "❌ Poor"
                })
            else:
                integrity_results.append({
                    "Relationship": f"{from_table}.{from_col} → {to_table}.{to_col}",
                    "Integrity %": "N/A",
                    "Missing References": "Column not found",
                    "Status": "❌ Missing Column"
                })
        else:
            integrity_results.append({
                "Relationship": f"{from_table}.{from_col} → {to_table}.{to_col}",
                "Integrity %": "N/A", 
                "Missing References": "Table not found",
                "Status": "❌ Missing Table"
            })
    
    if integrity_results:
        integrity_df = pd.DataFrame(integrity_results)
        st.dataframe(integrity_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Data Quality Checks")
    
    # Quality checks as specified in requirements
    quality_checks = []
    
    # Expected row counts (approximate)
    expected_counts = {
        "incidents_resolved.csv": (250, 350),  # ~300 rows
        "services_catalog.csv": (1, 20),
        "category_tree.csv": (5, 50),
        "users_agents.csv": (1, 50),
        "skills_catalog.csv": (1, 100),
        "workload_queue.csv": (10, 100)
    }
    
    for filename, df in dfs.items():
        if filename in expected_counts:
            min_rows, max_rows = expected_counts[filename]
            row_count = len(df)
            row_status = "✅ Good" if min_rows <= row_count <= max_rows else "⚠️ Unexpected"
        else:
            row_status = "ℹ️ No expectation"
            
        # Check for key columns
        key_columns = []
        if 'id' in filename or filename.startswith('incidents') or filename.startswith('workload'):
            key_columns = [col for col in df.columns if col.endswith('_id') or col == 'id']
        
        # Null percentage
        null_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100) if not df.empty else 0
        null_status = "✅ Good" if null_pct < 10 else "⚠️ High" if null_pct < 25 else "❌ Very High"
        
        # Duplicate check for key columns
        duplicate_status = "N/A"
        if key_columns:
            for key_col in key_columns:
                if key_col in df.columns:
                    duplicates = df[key_col].duplicated().sum()
                    if duplicates == 0:
                        duplicate_status = "✅ No duplicates"
                    else:
                        duplicate_status = f"⚠️ {duplicates} duplicates"
                    break
        
        quality_checks.append({
            "File": filename,
            "Row Count": f"{len(df):,}",
            "Row Status": row_status,
            "Null %": f"{null_pct:.1f}%",
            "Null Status": null_status,
            "Key Columns": ", ".join(key_columns) if key_columns else "None identified",
            "Duplicate Status": duplicate_status
        })
    
    quality_df = pd.DataFrame(quality_checks)
    st.dataframe(quality_df, use_container_width=True, hide_index=True)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_files = len(dfs)
        st.metric("Total Files Loaded", total_files)
    
    with col2:
        good_row_counts = len([q for q in quality_checks if q["Row Status"] == "✅ Good"])
        st.metric("Files with Good Row Counts", f"{good_row_counts}/{total_files}")
    
    with col3:
        low_null_files = len([q for q in quality_checks if q["Null Status"] == "✅ Good"])
        st.metric("Files with Low Null %", f"{low_null_files}/{total_files}")
    
    with col4:
        no_dup_files = len([q for q in quality_checks if "No duplicates" in q["Duplicate Status"]])
        st.metric("Files with No Key Duplicates", f"{no_dup_files}/{total_files}")

with tab4:
    st.subheader("Data Lineage & Flow")
    
    st.markdown("""
    ### ITSM Data Flow (as per requirements)
    
    **1. Reference Data (Lookups)**
    - Services, Categories, CIs, Agents, Groups, Skills
    - Used for normalization and validation
    
    **2. Historical Facts**  
    - `incidents_resolved.csv` - Training corpus (300 rows)
    - Contains titles, descriptions, labels, resolutions
    
    **3. Live Work Queue**
    - `workload_queue.csv` - Items needing assignment now
    - Links to services, categories, required skills
    
    **4. Operational Context**
    - Agent capacity, performance history, schedules
    - Used for intelligent routing decisions
    
    **5. Knowledge Management**
    - Templates → AI-generated articles
    - Linked to incident categories and services
    """)
    
    # Create a simple flow diagram using text
    st.subheader("Processing Pipeline Flow")
    
    flow_steps = [
        "📥 **Input**: Text (incidents, workload)",
        "🔄 **Normalize**: Synonyms, categories", 
        "🎯 **UC-02**: Triage (priority, group)",
        "🔍 **UC-21**: Clusters → KB drafts",
        "👥 **UC-31**: Matching (skills + capacity + schedule + quality)",
        "📤 **Output**: Predictions, KB articles, routing decisions"
    ]
    
    for i, step in enumerate(flow_steps, 1):
        st.markdown(f"{i}. {step}")
        if i < len(flow_steps):
            st.markdown("   ⬇️")
    
    # Show expected outputs
    st.subheader("Expected Deliverable Outputs")
    
    outputs = [
        {
            "File": "triage_predictions.csv",
            "Use Case": "UC-02",
            "Purpose": "Incident priority and group predictions",
            "Status": "❌ Not implemented"
        },
        {
            "File": "kb_articles.csv (populated)",
            "Use Case": "UC-21", 
            "Purpose": "AI-generated knowledge base articles",
            "Status": "❌ Not implemented"
        },
        {
            "File": "routing_decisions.csv",
            "Use Case": "UC-31",
            "Purpose": "Agent assignment recommendations", 
            "Status": "❌ Not implemented"
        }
    ]
    
    outputs_df = pd.DataFrame(outputs)
    st.dataframe(outputs_df, use_container_width=True, hide_index=True)
