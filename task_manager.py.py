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
SPREADSHEET_NAME = "TaskManagerDB"

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
            # For Streamlit Cloud, use secrets.toml
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
            
            # Open the spreadsheet
            spreadsheet = gc.open(SPREADSHEET_NAME)
            worksheet = spreadsheet.sheet1
            
            # Get all records
            records = worksheet.get_all_records()
            
            # Convert empty strings to None and ensure proper structure
            formatted_records = []
            for record in records:
                if any(record.values()):  # Only add non-empty records
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
            st.error(f"Spreadsheet '{SPREADSHEET_NAME}' not found. Please create it and share with your service account.")
            return []
        except gspread.exceptions.APIError as e:
            st.error(f"Google Sheets API error: {e}")
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
            
            # Clear existing data
            worksheet.clear()
            
            if tasks:
                # Create headers
                headers = ["description", "building", "tcd", "comments", "category", "last_updated", "closed"]
                worksheet.append_row(headers)
                
                # Add data rows
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
    st.set_page_config(page_title="Enhanced Task Manager", layout="wide")
    st.title("📋 Enhanced Task Manager - Cloud Sync")
    
    # Initialize session state
    if 'task_manager' not in st.session_state:
        st.session_state.task_manager = GoogleSheetsManager()
    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = None
    if 'current_category' not in st.session_state:
        st.session_state.current_category = "All"
    
    task_manager = st.session_state.task_manager
    
    # Debug info (remove in production)
    with st.sidebar:
        st.header("Debug Info")
        st.write(f"Tasks loaded: {len(task_manager.tasks)}")
        if st.button("Reload Data"):
            st.session_state.task_manager.tasks = st.session_state.task_manager.load_tasks()
            st.rerun()
    
    # Sidebar for filters
    with st.sidebar:
        st.header("Filters & Stats")
        st.session_state.current_category = st.selectbox(
            "View Category:",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(st.session_state.current_category)
        )
        
        # Category statistics
        st.subheader("Task Statistics")
        category_counts = {cat: 0 for cat in CATEGORIES.keys() if cat != "All"}
        for task in task_manager.tasks:
            if task["category"] in category_counts:
                category_counts[task["category"]] += 1
        
        for cat, count in category_counts.items():
            color = CATEGORIES[cat]
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>{cat}: {count}</span>", 
                       unsafe_allow_html=True)
        
        st.markdown(f"**Total Tasks: {len(task_manager.tasks)}**")

    # Main content area
    st.header("Task Form")
    
    # Input fields
    col1, col2 = st.columns(2)
    
    with col1:
        description = st.text_input("Description*", 
                                  value=st.session_state.get('edit_description', ''))
        building = st.selectbox("Building", BUILDINGS, 
                              index=BUILDINGS.index(st.session_state.get('edit_building', BUILDINGS[0])) 
                              if st.session_state.get('edit_building') in BUILDINGS else 0)
        tcd = st.text_input("TCD", value=st.session_state.get('edit_tcd', ''))
    
    with col2:
        comments = st.text_input("Comments", value=st.session_state.get('edit_comments', ''))
        category = st.selectbox("Category", 
                              [cat for cat in CATEGORIES.keys() if cat != "All"],
                              index=list(CATEGORIES.keys()).index(st.session_state.get('edit_category', 'OT')) 
                              if st.session_state.get('edit_category') in CATEGORIES else 8)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
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
                    st.success("Task saved successfully! Synced to cloud.")
                    clear_edit_state()
                    st.rerun()
                else:
                    st.error("Error saving task to cloud.")
    
    with col2:
        if st.session_state.selected_index is not None:
            if st.button("❌ Cancel Edit", use_container_width=True):
                clear_edit_state()
                st.rerun()
    
    with col3:
        if st.session_state.selected_index is not None:
            if st.button("🗑️ Delete Selected Task", use_container_width=True):
                if task_manager.delete_task(st.session_state.selected_index):
                    st.success("Task deleted successfully! Synced to cloud.")
                    clear_edit_state()
                    st.rerun()
                else:
                    st.error("Error deleting task from cloud.")
    
    # Clear form button
    if st.button("🧹 Clear Form", use_container_width=True):
        clear_edit_state()
        st.rerun()
    
    # Display tasks
    st.header("Task List")
    
    # Filter tasks based on current category
    filtered_tasks = [
        task for task in task_manager.tasks 
        if st.session_state.current_category == "All" or task["category"] == st.session_state.current_category
    ]
    
    if filtered_tasks:
        for i, task in enumerate(filtered_tasks):
            task_key = f"{task['description']}_{task['building']}_{task['category']}"
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([0.5, 2, 1, 1, 2, 1, 1.5])
            
            with col1:
                if st.button("📝", key=f"edit_{task_key}"):
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
            
            with col2:
                st.write(task["description"])
            
            with col3:
                st.write(task["building"])
            
            with col4:
                st.write(task.get("tcd", "") or "-")
            
            with col5:
                st.write(task.get("comments", "") or "-")
            
            with col6:
                color = CATEGORIES.get(task["category"], "#FFFFFF")
                st.markdown(
                    f"<span style='background-color: {color}; padding: 2px 8px; border-radius: 4px;'>{task['category']}</span>",
                    unsafe_allow_html=True
                )
            
            with col7:
                st.write(task.get("last_updated", ""))
            
            st.divider()
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