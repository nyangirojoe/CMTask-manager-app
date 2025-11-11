import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup - UPDATED SPREADSHEET NAME
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
SPREADSHEET_NAME = "CMTask-ManagerDB"  # Updated to match your spreadsheet

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
            
            # UPDATED: Now using CMTask-ManagerDB
            spreadsheet = gc.open("CMTask-ManagerDB")
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
            st.error(f"Spreadsheet 'CMTask-ManagerDB' not found. Please create it and share with your service account.")
            return []
        except Exception as e:
            st.error(f"Error loading tasks: {str(e)}")
            return []
    
    def save_tasks(self, tasks):
        try:
            gc = self.get_credentials()
            if not gc:
                return False
            
            # UPDATED: Now using CMTask-ManagerDB
            spreadsheet = gc.open("CMTask-ManagerDB")
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
    # Custom CSS for enhanced aesthetics
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2e86ab;
        border-bottom: 2px solid #2e86ab;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .task-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #2e86ab;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .category-badge {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
    }
    .stButton button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.set_page_config(page_title="Enhanced Task Manager", layout="wide", page_icon="📋")
    
    # Header with icon
    st.markdown('<h1 class="main-header">🚀 Enhanced Task Manager</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'task_manager' not in st.session_state:
        st.session_state.task_manager = GoogleSheetsManager()
    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = None
    if 'current_category' not in st.session_state:
        st.session_state.current_category = "All"
    
    task_manager = st.session_state.task_manager
    
    # Sidebar with enhanced design
    with st.sidebar:
        st.markdown("## 🎯 Quick Actions")
        
        # Quick add form in sidebar
        with st.expander("➕ Quick Add Task", expanded=False):
            quick_desc = st.text_input("Description", key="quick_desc")
            quick_cat = st.selectbox("Category", [cat for cat in CATEGORIES.keys() if cat != "All"], key="quick_cat")
            if st.button("Add Quick Task", use_container_width=True):
                if quick_desc.strip():
                    task_data = {
                        "description": quick_desc.strip(),
                        "building": BUILDINGS[0],
                        "tcd": "",
                        "comments": "",
                        "category": quick_cat,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "closed": quick_cat == "CT"
                    }
                    if task_manager.add_or_update_task(task_data):
                        st.success("Quick task added!")
                        st.rerun()
        
        st.markdown("---")
        st.markdown("## 📊 Live Statistics")
        
        # Enhanced statistics cards
        total_tasks = len(task_manager.tasks)
        completed_tasks = len([t for t in task_manager.tasks if t.get("closed", False)])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h3>📋 Total</h3>
                <h2>{total_tasks}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h3>✅ Completed</h3>
                <h2>{completed_tasks}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Category breakdown
        st.markdown("### 📈 By Category")
        category_counts = {cat: 0 for cat in CATEGORIES.keys() if cat != "All"}
        for task in task_manager.tasks:
            if task["category"] in category_counts:
                category_counts[task["category"]] += 1
        
        for cat, count in category_counts.items():
            if count > 0:
                color = CATEGORIES[cat]
                progress = count / max(total_tasks, 1)
                st.markdown(f"""
                <div style="margin: 5px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                        <span>
                            <span style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px;"></span>
                            {cat}
                        </span>
                        <span>{count}</span>
                    </div>
                    <div style="background: #e0e0e0; border-radius: 3px; height: 6px; margin-top: 2px;">
                        <div style="background-color: {color}; width: {progress*100}%; height: 100%; border-radius: 3px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.session_state.task_manager.tasks = st.session_state.task_manager.load_tasks()
            st.rerun()

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="section-header">✏️ Task Management</div>', unsafe_allow_html=True)
        
        # Enhanced task form
        with st.container():
            st.subheader("Add/Edit Task")
            
            form_col1, form_col2 = st.columns(2)
            
            with form_col1:
                description = st.text_input(
                    "**Description** 📝",
                    value=st.session_state.get('edit_description', ''),
                    placeholder="Enter task description...",
                    help="Required field"
                )
                building = st.selectbox(
                    "**Building** 🏢",
                    BUILDINGS,
                    index=BUILDINGS.index(st.session_state.get('edit_building', BUILDINGS[0])) 
                    if st.session_state.get('edit_building') in BUILDINGS else 0
                )
                tcd = st.text_input(
                    "**TCD** 📅",
                    value=st.session_state.get('edit_tcd', ''),
                    placeholder="Target completion date..."
                )
            
            with form_col2:
                comments = st.text_area(
                    "**Comments** 💬",
                    value=st.session_state.get('edit_comments', ''),
                    placeholder="Additional notes or comments...",
                    height=100
                )
                category = st.selectbox(
                    "**Category** 🏷️",
                    [cat for cat in CATEGORIES.keys() if cat != "All"],
                    index=list(CATEGORIES.keys()).index(st.session_state.get('edit_category', 'OT')) 
                    if st.session_state.get('edit_category') in CATEGORIES else 8
                )
            
            # Action buttons with icons and colors
            button_col1, button_col2, button_col3, button_col4 = st.columns(4)
            
            with button_col1:
                button_label = "🔄 Update Task" if st.session_state.selected_index is not None else "🚀 Add Task"
                button_type = "primary" if st.session_state.selected_index is None else "secondary"
                if st.button(button_label, use_container_width=True, type=button_type):
                    if not description.strip():
                        st.error("📝 Please enter a description!")
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
                            st.success("✅ Task saved successfully!")
                            clear_edit_state()
                            st.rerun()
            
            with button_col2:
                if st.session_state.selected_index is not None:
                    if st.button("❌ Cancel", use_container_width=True):
                        clear_edit_state()
                        st.rerun()
            
            with button_col3:
                if st.session_state.selected_index is not None:
                    if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                        if task_manager.delete_task(st.session_state.selected_index):
                            st.success("🗑️ Task deleted successfully!")
                            clear_edit_state()
                            st.rerun()
            
            with button_col4:
                if st.button("🧹 Clear Form", use_container_width=True):
                    clear_edit_state()
                    st.rerun()

    with col2:
        st.markdown('<div class="section-header">🔍 Task View</div>', unsafe_allow_html=True)
        
        # Category filter with style
        current_category = st.selectbox(
            "**Filter by Category**",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(st.session_state.current_category),
            key="category_filter"
        )
        st.session_state.current_category = current_category
        
        # Quick stats
        filtered_count = len([t for t in task_manager.tasks 
                            if st.session_state.current_category == "All" or t["category"] == st.session_state.current_category])
        
        st.metric(
            label="Tasks Showing",
            value=filtered_count,
            delta=f"of {len(task_manager.tasks)} total"
        )

    # Enhanced task display
    st.markdown('<div class="section-header">📋 Task List</div>', unsafe_allow_html=True)
    
    filtered_tasks = [
        task for task in task_manager.tasks 
        if st.session_state.current_category == "All" or task["category"] == st.session_state.current_category
    ]
    
    if filtered_tasks:
        for i, task in enumerate(filtered_tasks):
            color = CATEGORIES.get(task["category"], "#FFFFFF")
            is_closed = task.get("closed", False)
            
            with st.container():
                st.markdown(f"""
                <div class="task-card" style="border-left-color: {color}; {'opacity: 0.7;' if is_closed else ''}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0; {'text-decoration: line-through;' if is_closed else ''}">
                                {task['description']}
                                {' ✅' if is_closed else ''}
                            </h4>
                            <p style="margin: 5px 0; color: #666;">
                                🏢 {task['building']} 
                                {f"• 📅 {task['tcd']}" if task.get('tcd') else ""}
                                {f"<br>💬 {task['comments']}" if task.get('comments') else ""}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <span class="category-badge" style="background-color: {color}; color: {'#000' if color != '#ffff99' else '#000'};">
                                {task['category']}
                            </span>
                            <p style="margin: 5px 0; font-size: 0.8rem; color: #888;">
                                {task.get('last_updated', '')}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Edit button
                col1, col2 = st.columns([6, 1])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{i}"):
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
    else:
        st.info("🎉 No tasks found for the selected category. Add your first task above!")

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