import streamlit as st
import pandas as pd
import os

def ensure_data_loaded():
    """
    Ensure ITSM data is loaded in session state.
    This function can be called from any page to guarantee data availability.
    """
    # Data directory - Using relative path to dummydata folder in repository
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dummydata")
    
    # Check if data is already loaded
    if "dfs" not in st.session_state or not st.session_state["dfs"]:
        with st.spinner("Loading ITSM data..."):
            st.session_state["dfs"] = load_data(data_dir)
            st.session_state["data_dir"] = data_dir
    
    return st.session_state["dfs"]

def load_data(data_dir):
    """Load all CSV files from the data directory with proper ordering"""
    if not os.path.isdir(data_dir):
        st.error(f"Data directory not found: {data_dir}")
        return {}
    
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
    try:
        all_csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    except Exception as e:
        st.error(f"Could not read data directory: {str(e)}")
        return {}
    
    # Load ordered files first
    for f in load_order:
        if f in all_csv_files:
            p = os.path.join(data_dir, f)
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
        p = os.path.join(data_dir, f)
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
            dfs[f] = df
        except Exception as e:
            try:
                df = pd.read_csv(p)
                dfs[f] = df
            except Exception:
                st.warning(f"Could not load {f}: {str(e)}")
    
    return dfs

def get_data():
    """
    Get the loaded ITSM data. 
    Returns the dfs dictionary or empty dict if not loaded.
    """
    return st.session_state.get("dfs", {})

def get_data_dir():
    """
    Get the data directory path.
    """
    return st.session_state.get("data_dir", "")
