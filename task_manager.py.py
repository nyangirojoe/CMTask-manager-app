import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
SPREADSHEET_NAME = "CMTask-ManagerDB"

CATEGORIES = {
    "APV": "#90ee90", "UAPV": "#d2b48c", "EV": "#ffb6c1", "KPI": "#d3d3d3",
    "NTC": "#ee82ee", "ACT": "#ffa500", "NTU": "#d8bfd8", "OT": "#ffff99",
    "PRJ": "#87ceeb", "CT": "#ff4c4c", "All": "#f0f0f0"
}

BUILDINGS = ["OH", "OHWE", "OHNE", "ASH", "LC", "LSH", "SAB", "WH", "KIS", "APTS1", "APAB", "APSV", "AAE", "ETS1", "ETS2", "ETS3", "OHAC", "NHAC", "ODCR", "CAU", "CPG", "PTZ2", "AA", "EC", "SC", "NHQ", "NEC", "SCU", "RO"]

class GoogleSheetsManager:
    def __init__(self):
        self.tasks = self.load_tasks()
    
    def get_credentials(self):
        try:
            if 'google_credentials' in st.secrets:
                creds_dict = dict(st.secrets['google_credentials'])
                creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
                return gspread.authorize(creds)
            else:
                st.error("Google credentials not found in secrets")
                return None
        except Exception as e:
            st.error(f"Error getting credentials: {e}")
            return None
    
    def load_tasks(self):
        try:
            gc = self.get_credentials()
            if not gc:
                return []
            
            spreadsheet = gc.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            records = worksheet.get_all_records()
            
            formatted_records = []
            for record in records:
                if any(record.values()):
                    formatted_record = {
                        "description": record.get("description", ""),
                        "building": record.get("building", ""),
                        "tcd": record.get("tcd", ""),
                        "comments": record.get("comments", ""),
                        "category": record.get("category", "OT"),
                        "last_updated": record.get("last_updated", ""),
                        "closed": record.get("closed", False)
                    }
                    formatted_records.append(formatted_record)
            
            return formatted_records
            
        except gspread.SpreadsheetNotFound:
            st.error(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")
            return []
        except Exception as e:
            st.error(f"Error loading tasks: {str(e)}")
            return []
    
    def save_tasks(self, tasks):
        try:
            gc = self.get_credentials()
            if not gc:
                return False
            
            spreadsheet = gc.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            
            worksheet.clear()
            
            if tasks:
                headers = ["description", "building", "tcd", "comments", "category", "last_updated", "closed"]
                worksheet.append_row(headers)
                
                for task in tasks:
                    row = [
                        task.get("description", ""),
                        task.get("building", ""),
                        task.get("tcd", ""),
                        task.get("comments", ""),
                        task.get("category", "OT"),
                        task.get("last_updated", ""),
                        task.get("closed", False)
                    ]
                    worksheet.append_row(row)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving tasks: {str(e)}")
            return False
    
    def add_or_update_task(self, task_data, selected_index=None):
        try:
            if selected_index is not None:
                self.tasks[selected_index] = task_data
            else:
                self.tasks.append(task_data)
            return self.save_tasks(self.tasks)
        except Exception as e:
            st.error(f"Error adding/updating task: {str(e)}")
            return False
    
    def delete_task(self, index):
        try:
            if 0 <= index < len(self.tasks):
                del self.tasks[index]
                return self.save_tasks(self.tasks)
            return False
        except Exception as e:
            st.error(f"Error deleting task: {str(e)}")
            return False

def main():
    # Enhanced CSS for better aesthetics while keeping same layout
    st.markdown("""
    <style>
    /* Main header styling */
    .main-header {
        font-size: 2.2rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 700;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        color: #2e86ab;
        border-left: 4px solid #2e86ab;
        padding-left: 1rem;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
    }
    
    /* Enhanced buttons */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    }
    
    /* Improved input fields */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        border-radius: 6px;
        border: 1px solid #ddd;
    }
    
    .stTextInput input:focus, .stSelectbox div:focus, .stTextArea textarea:focus {
        border-color: #2e86ab;
        box-shadow: 0 0 0 2px rgba(46, 134, 171, 0.2);
    }
    
    /* Task row styling */
    .task-row {
        background: white;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border-radius: 8px;
        border-left: 4px solid;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .task-row:hover {
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Statistics in sidebar */
    .stat-item {
        background: white;
        padding: 0.8rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 3px solid #2e86ab;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Success/Error messages */
    .stAlert {
        border-radius: 8px;
    }
    
    /* Container spacing */
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.set_page_config(page_title="Enhanced Task Manager", layout="wide")
    
    # Enhanced header
    st.markdown('<h1 class="main-header">📋 Enhanced Task Manager</h1>', unsafe_allow_html=True)
    
    # Initialize session state (same functionality)
    if 'task_manager' not in st.session_state:
        st.session_state.task_manager = GoogleSheetsManager()
    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = None
    if 'current_category' not in st.session_state:
        st.session_state.current_category = "All"
    
    task_manager = st.session_state.task_manager
    
    # Sidebar with enhanced aesthetics
    with st.sidebar:
        st.markdown('<div class="section-header">🔍 View Category</div>', unsafe_allow_html=True)
        st.session_state.current_category = st.selectbox(
            "Select Category:",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(st.session_state.current_category),
            label_visibility="collapsed"
        )
        
        st.markdown('<div class="section-header">📊 Statistics</div>', unsafe_allow_html=True)
        
        # Enhanced statistics display
        category_counts = {cat: 0 for cat in CATEGORIES.keys() if cat != "All"}
        for task in task_manager.tasks:
            if task["category"] in category_counts:
                category_counts[task["category"]] += 1
        
        for cat, count in category_counts.items():
            color = CATEGORIES[cat]
            if count > 0:
                st.markdown(f"""
                <div class="stat-item">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 500;">{cat}</span>
                        <span style="background-color: {color}; color: {'#000' if color not in ['#ff4c4c', '#764ba2'] else '#fff'}; 
                              padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
                            {count}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Total count with better styling
        st.markdown(f"""
        <div class="stat-item" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: bold;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>Total Tasks</span>
                <span style="background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 15px;">
                    {len(task_manager.tasks)}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.task_manager.tasks = st.session_state.task_manager.load_tasks()
            st.rerun()

    # Main content - SAME FUNCTIONALITY, BETTER STYLING
    
    # Task Entry Form (same structure, better styling)
    st.markdown('<div class="section-header">✏️ Task Entry Form</div>', unsafe_allow_html=True)
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_input(
                "Description*",
                value=st.session_state.get('edit_description', ''),
                placeholder="Enter task description"
            )
            building = st.selectbox(
                "Building",
                BUILDINGS,
                index=BUILDINGS.index(st.session_state.get('edit_building', BUILDINGS[0])) 
                if st.session_state.get('edit_building') in BUILDINGS else 0
            )
        
        with col2:
            tcd = st.text_input(
                "TCD",
                value=st.session_state.get('edit_tcd', ''),
                placeholder="Target completion date"
            )
            comments = st.text_input(
                "Comments",
                value=st.session_state.get('edit_comments', ''),
                placeholder="Additional comments"
            )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        category = st.selectbox(
            "Category",
            [cat for cat in CATEGORIES.keys() if cat != "All"],
            index=list(CATEGORIES.keys()).index(st.session_state.get('edit_category', 'OT')) 
            if st.session_state.get('edit_category') in CATEGORIES else 8
        )
    
    with col2:
        button_label = "✅ Update Task" if st.session_state.selected_index is not None else "➕ Add Task"
        if st.button(button_label, use_container_width=True):
            if not description.strip():
                st.error("Please enter a description.")
            else:
                task_data = {
                    "description": description.strip(),
                    "building": building,
                    "tcd": tcd,
                    "comments": comments,
                    "category": category,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "closed": category == "CT"
                }
                
                if task_manager.add_or_update_task(task_data, st.session_state.selected_index):
                    st.success("Task saved successfully!")
                    clear_edit_state()
                    st.rerun()
    
    with col3:
        col3a, col3b = st.columns(2)
        with col3a:
            if st.session_state.selected_index is not None:
                if st.button("🗑️ Delete", use_container_width=True):
                    if task_manager.delete_task(st.session_state.selected_index):
                        st.success("Task deleted successfully!")
                        clear_edit_state()
                        st.rerun()
        with col3b:
            if st.button("🧹 Clear", use_container_width=True):
                clear_edit_state()
                st.rerun()

    # Task List Display (same functionality, better styling)
    st.markdown('<div class="section-header">📋 Task List</div>', unsafe_allow_html=True)
    
    filtered_tasks = [
        task for task in task_manager.tasks 
        if st.session_state.current_category == "All" or task["category"] == st.session_state.current_category
    ]
    
    if filtered_tasks:
        # Display tasks in enhanced rows
        for i, task in enumerate(filtered_tasks):
            color = CATEGORIES.get(task["category"], "#FFFFFF")
            
            # Create enhanced task row
            st.markdown(f"""
            <div class="task-row" style="border-left-color: {color}">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="flex: 1;">
                        <div style="font-weight: 500; font-size: 1rem;">{task['description']}</div>
                        <div style="color: #666; font-size: 0.9rem; margin-top: 0.2rem;">
                            🏢 {task['building']} • {task.get('tcd', '')} • {task.get('comments', '')}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="background-color: {color}; color: {'#000' if color not in ['#ff4c4c', '#764ba2'] else '#fff'}; 
                             padding: 4px 12px; border-radius: 15px; font-size: 0.8rem; font-weight: bold; display: inline-block;">
                            {task['category']}
                        </div>
                        <div style="color: #888; font-size: 0.8rem; margin-top: 0.2rem;">
                            {task.get('last_updated', '')}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Edit button (same functionality)
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("Edit", key=f"edit_{i}"):
                    actual_index = None
                    for j, t in enumerate(task_manager.tasks):
                        if (t["description"] == task["description"] and 
                            t["building"] == task["building"] and 
                            t["category"] == task["category"]):
                            actual_index = j
                            break
                    
                    if actual_index is not None:
                        set_edit_state(task, actual_index)
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("No tasks found for the selected category.")

def clear_edit_state():
    st.session_state.selected_index = None
    st.session_state.edit_description = ''
    st.session_state.edit_building = BUILDINGS[0]
    st.session_state.edit_tcd = ''
    st.session_state.edit_comments = ''
    st.session_state.edit_category = 'OT'

def set_edit_state(task, index):
    st.session_state.selected_index = index
    st.session_state.edit_description = task["description"]
    st.session_state.edit_building = task["building"]
    st.session_state.edit_tcd = task.get("tcd", "")
    st.session_state.edit_comments = task.get("comments", "")
    st.session_state.edit_category = task["category"]

if __name__ == "__main__":
    main()