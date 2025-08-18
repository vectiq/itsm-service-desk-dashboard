import streamlit as st
import os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ITSM AI Demo", page_icon="🧩", layout="wide")

st.title("🎫 ITSM Service Desk Dashboard")
st.markdown("""
Welcome to the ITSM Service Desk Dashboard! This application provides comprehensive views of your ITSM data:
- **📋 Incidents Dashboard**: Complete incident management and analytics
- **📚 Knowledge Base**: KB articles, templates, and documentation
- **📊 Service Analytics**: Service performance and operational insights

Explore your incident data, knowledge base, and service metrics below.
""")

# Data directory - Update this path to point to your CSV files
HARDCODED_DATA_DIR = "/Users/dannardi/Downloads/ITSMF/AI_ITSM_Dummy_Data_Populated"
# Example paths:
# HARDCODED_DATA_DIR = "/path/to/your/csv/files"
# HARDCODED_DATA_DIR = "./data"
# HARDCODED_DATA_DIR = os.path.join(os.getcwd(), "data")

if "data_dir" not in st.session_state:
    st.session_state["data_dir"] = HARDCODED_DATA_DIR
if "dfs" not in st.session_state:
    st.session_state["dfs"] = {}

# Auto-load all CSV files on startup
if not st.session_state["dfs"] and os.path.isdir(HARDCODED_DATA_DIR):
    dfs = {}
    csv_files = [f for f in os.listdir(HARDCODED_DATA_DIR) if f.endswith('.csv')]

    for f in csv_files:
        p = os.path.join(HARDCODED_DATA_DIR, f)
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
            dfs[f] = df
        except Exception as e:
            try:
                df = pd.read_csv(p)
                dfs[f] = df
            except Exception:
                st.warning(f"Could not load {f}: {str(e)}")

    st.session_state["data_dir"] = HARDCODED_DATA_DIR
    st.session_state["dfs"] = dfs

# Show current data status
if st.session_state["dfs"]:
    st.success(f"✅ Data loaded from: `{st.session_state['data_dir']}`")
else:
    st.warning("⚠️ No data loaded")

# Optional manual data loading section
with st.expander("🔧 Manual Data Loading (Optional)", expanded=False):
    st.write("The application automatically loads data from the configured path. Use this section only if you need to load data from a different location.")

    data_dir = st.text_input("Path to your CSV folder", value=st.session_state["data_dir"] or "", help="Folder containing the CSVs")
    if st.button("Load CSVs"):
        if not os.path.isdir(data_dir):
            st.error("Folder not found")
        else:
            required = [
                "incidents_resolved.csv",
                "workload_queue.csv",
                "agent_skills.csv",
                "agent_capacity_snapshots.csv",
                "agent_performance_history.csv",
                "schedules.csv",
                "kb_templates.csv",
            ]
            dfs = {}
            missing = []
            for f in required:
                p = os.path.join(data_dir, f)
                if os.path.exists(p):
                    try:
                        df = pd.read_csv(p, encoding="utf-8-sig")
                    except Exception:
                        df = pd.read_csv(p)
                    dfs[f] = df
                else:
                    missing.append(f)
            st.session_state["data_dir"] = data_dir
            st.session_state["dfs"] = dfs
            if missing:
                st.warning("Missing files: " + ", ".join(missing))
            else:
                st.success("CSV files loaded")

st.subheader("📊 Service Desk Overview")
if st.session_state["dfs"]:
    # Show key metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    incidents = st.session_state["dfs"].get("incidents_resolved.csv", pd.DataFrame())
    workload = st.session_state["dfs"].get("workload_queue.csv", pd.DataFrame())
    kb_articles = st.session_state["dfs"].get("kb_articles.csv", pd.DataFrame())
    kb_templates = st.session_state["dfs"].get("kb_templates.csv", pd.DataFrame())
    services = st.session_state["dfs"].get("services_catalog.csv", pd.DataFrame())

    with col1:
        if not incidents.empty:
            st.metric("🎫 Resolved Incidents", f"{len(incidents):,}")
        else:
            st.metric("🎫 Resolved Incidents", "No data")

    with col2:
        if not workload.empty:
            st.metric("⏳ Current Queue", f"{len(workload):,}")
        else:
            st.metric("⏳ Current Queue", "No data")

    with col3:
        total_kb = 0
        if not kb_articles.empty:
            total_kb += len(kb_articles)
        if not kb_templates.empty:
            total_kb += len(kb_templates)
        st.metric("📚 KB Items", f"{total_kb:,}")

    with col4:
        if not services.empty:
            st.metric("🔧 Services", f"{len(services):,}")
        else:
            st.metric("🔧 Services", "No data")

    with col5:
        if not incidents.empty and 'true_priority' in incidents.columns:
            high_priority = len(incidents[incidents['true_priority'].isin(['P1', 'P2'])])
            st.metric("🚨 High Priority", f"{high_priority:,}")
        else:
            st.metric("🚨 High Priority", "No data")

    # Quick data preview
    st.subheader("📋 Quick Data Preview")
    cols = st.columns(2)
    for i, (name, df) in enumerate(st.session_state["dfs"].items()):
        with cols[i % 2]:
            with st.expander(f"📄 {name.replace('.csv', '').replace('_', ' ').title()} ({len(df)} rows)"):
                st.dataframe(df.head(5), use_container_width=True)
                if len(df) > 5:
                    st.caption(f"Showing first 5 of {len(df)} rows")
else:
    st.info("⚠️ No data loaded. Please check the data directory path.")

    # Show expected data structure
    with st.expander("📋 Available Data Files", expanded=True):
        key_files = {
            "incidents_resolved.csv": "Historical incident data with resolutions",
            "workload_queue.csv": "Current open incidents/requests",
            "kb_articles.csv": "Knowledge base articles",
            "kb_templates.csv": "Knowledge base templates",
            "services_catalog.csv": "Service catalog and definitions",
            "category_tree.csv": "Incident category hierarchy",
            "priority_matrix.csv": "Priority calculation matrix",
            "users_agents.csv": "User and agent information"
        }

        st.write("**Key ITSM Data Files:**")
        for file, description in key_files.items():
            st.write(f"• **{file}**: {description}")

        # Show all loaded files
        if st.session_state["dfs"]:
            st.write(f"\n**All Loaded Files ({len(st.session_state['dfs'])} total):**")
            for filename in sorted(st.session_state["dfs"].keys()):
                row_count = len(st.session_state["dfs"][filename])
                st.write(f"• {filename} ({row_count:,} rows)")
