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

# Auto-load all CSV files on startup with proper load order
if not st.session_state["dfs"] and os.path.isdir(HARDCODED_DATA_DIR):
    dfs = {}

    # Load order as specified in requirements (reference data first)
    load_order = [
        # Reference data (lookups)
        "dataset_catalog.csv",
        "services_catalog.csv",
        "category_tree.csv",
        "cmdb_ci.csv",
        "users_agents.csv",
        "assignment_groups.csv",
        "agent_group_membership.csv",
        "skills_catalog.csv",
        "agent_skills.csv",
        "synonyms_glossary.csv",
        "priority_matrix.csv",

        # Facts (historical data)
        "incidents_resolved.csv",

        # Live/demo inputs
        "workload_queue.csv",
        "agent_capacity_snapshots.csv",
        "agent_performance_history.csv",
        "schedules.csv",

        # Knowledge base
        "kb_templates.csv",
        "kb_articles.csv"
    ]

    # Load files in specified order, then load any remaining CSV files
    all_csv_files = [f for f in os.listdir(HARDCODED_DATA_DIR) if f.endswith('.csv')]

    # Load ordered files first
    for f in load_order:
        if f in all_csv_files:
            p = os.path.join(HARDCODED_DATA_DIR, f)
            try:
                df = pd.read_csv(p, encoding="utf-8-sig")
                dfs[f] = df
                all_csv_files.remove(f)  # Remove from remaining list
            except Exception as e:
                try:
                    df = pd.read_csv(p)
                    dfs[f] = df
                    all_csv_files.remove(f)
                except Exception:
                    st.warning(f"Could not load {f}: {str(e)}")

    # Load any remaining CSV files not in the ordered list
    for f in all_csv_files:
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

st.subheader("📊 ITSM Data Universe Overview")
if st.session_state["dfs"]:
    # Get all key datasets
    incidents = st.session_state["dfs"].get("incidents_resolved.csv", pd.DataFrame())
    workload = st.session_state["dfs"].get("workload_queue.csv", pd.DataFrame())
    services = st.session_state["dfs"].get("services_catalog.csv", pd.DataFrame())
    categories = st.session_state["dfs"].get("category_tree.csv", pd.DataFrame())
    agents = st.session_state["dfs"].get("users_agents.csv", pd.DataFrame())
    skills = st.session_state["dfs"].get("skills_catalog.csv", pd.DataFrame())
    agent_skills = st.session_state["dfs"].get("agent_skills.csv", pd.DataFrame())
    groups = st.session_state["dfs"].get("assignment_groups.csv", pd.DataFrame())
    cmdb = st.session_state["dfs"].get("cmdb_ci.csv", pd.DataFrame())
    kb_templates = st.session_state["dfs"].get("kb_templates.csv", pd.DataFrame())
    kb_articles = st.session_state["dfs"].get("kb_articles.csv", pd.DataFrame())

    # Core metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("🎫 Resolved Incidents", f"{len(incidents):,}" if not incidents.empty else "0")

    with col2:
        st.metric("⏳ Current Queue", f"{len(workload):,}" if not workload.empty else "0")

    with col3:
        st.metric("🔧 Services", f"{len(services):,}" if not services.empty else "0")

    with col4:
        st.metric("📂 Categories", f"{len(categories):,}" if not categories.empty else "0")

    with col5:
        st.metric("👥 Agents", f"{len(agents):,}" if not agents.empty else "0")

    with col6:
        st.metric("🎯 Skills", f"{len(skills):,}" if not skills.empty else "0")

    # Additional metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("👥 Groups", f"{len(groups):,}" if not groups.empty else "0")

    with col2:
        st.metric("💻 CIs", f"{len(cmdb):,}" if not cmdb.empty else "0")

    with col3:
        total_kb = len(kb_articles) + len(kb_templates) if not kb_articles.empty or not kb_templates.empty else 0
        st.metric("📚 KB Items", f"{total_kb:,}")

    with col4:
        if not incidents.empty and 'true_priority' in incidents.columns:
            high_priority = len(incidents[incidents['true_priority'].isin(['P1', 'P2'])])
            st.metric("🚨 High Priority", f"{high_priority:,}")
        else:
            st.metric("🚨 High Priority", "0")

    with col5:
        if not agent_skills.empty:
            total_skill_assignments = len(agent_skills)
            st.metric("🔗 Skill Assignments", f"{total_skill_assignments:,}")
        else:
            st.metric("🔗 Skill Assignments", "0")

    with col6:
        # Data completeness score
        expected_files = ["services_catalog.csv", "category_tree.csv", "incidents_resolved.csv",
                         "workload_queue.csv", "users_agents.csv", "skills_catalog.csv"]
        loaded_files = [f for f in expected_files if f in st.session_state["dfs"] and not st.session_state["dfs"][f].empty]
        completeness = int((len(loaded_files) / len(expected_files)) * 100)
        st.metric("📊 Data Completeness", f"{completeness}%")

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
    with st.expander("📋 ITSM Data Universe Files", expanded=True):

        # Organize files by category as per requirements
        file_categories = {
            "📋 Reference Data (Lookups)": {
                "dataset_catalog.csv": "Data catalog index",
                "services_catalog.csv": "Service catalog and definitions",
                "category_tree.csv": "Incident category hierarchy",
                "cmdb_ci.csv": "Configuration items database",
                "users_agents.csv": "User and agent information",
                "assignment_groups.csv": "Support group definitions",
                "agent_group_membership.csv": "Agent-to-group assignments",
                "skills_catalog.csv": "Available skills catalog",
                "agent_skills.csv": "Agent skill assignments",
                "synonyms_glossary.csv": "Text normalization dictionary",
                "priority_matrix.csv": "Priority calculation matrix"
            },
            "📊 Historical Facts": {
                "incidents_resolved.csv": "Historical incident corpus (~300 rows)"
            },
            "⚡ Live/Demo Data": {
                "workload_queue.csv": "Current open items needing assignment",
                "agent_capacity_snapshots.csv": "Agent workload capacity",
                "agent_performance_history.csv": "Agent performance metrics",
                "schedules.csv": "Agent availability schedules"
            },
            "📚 Knowledge Base": {
                "kb_templates.csv": "KB article templates/scaffolds",
                "kb_articles.csv": "Knowledge base articles (target for AI)"
            }
        }

        for category, files in file_categories.items():
            st.write(f"**{category}:**")
            for file, description in files.items():
                if file in st.session_state.get("dfs", {}):
                    row_count = len(st.session_state["dfs"][file])
                    st.write(f"• ✅ **{file}**: {description} ({row_count:,} rows)")
                else:
                    st.write(f"• ❌ **{file}**: {description} (not loaded)")
            st.write("")

        # Show any additional loaded files
        if st.session_state.get("dfs"):
            all_expected = set()
            for files in file_categories.values():
                all_expected.update(files.keys())

            additional_files = [f for f in st.session_state["dfs"].keys() if f not in all_expected]
            if additional_files:
                st.write("**🔍 Additional Files:**")
                for filename in sorted(additional_files):
                    row_count = len(st.session_state["dfs"][filename])
                    st.write(f"• **{filename}**: ({row_count:,} rows)")
