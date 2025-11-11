import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURATION ---
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]
SPREADSHEET_NAME = "CMTask-ManagerDB"

# Define categories and colors
CATEGORIES = {
    "APV": "#90ee90", "UAPV": "#d2b48c", "EV": "#ffb6c1", "KPI": "#d3d3d3",
    "NTC": "#ee82ee", "ACT": "#ffa500", "NTU": "#d8bfd8", "OT": "#ffff99",
    "PRJ": "#87ceeb", "CT": "#ff4c4c", "All": "#f0f0f0"
}

BUILDINGS = [
    "OH", "OHWE", "OHNE", "ASH", "LC", "LSH", "SAB", "WH", "KIS", "APTS1", "APAB", "APSV", "AAE",
    "ETS1", "ETS2", "ETS3", "OHAC", "NHAC", "ODCR", "CAU", "CPG", "PTZ2", "AA", "EC", "SC",
    "NHQ", "NEC", "SCU", "RO"
]

# --- GOOGLE SHEETS MANAGER ---
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
                st.error("Google credentials not found in Streamlit Secrets.")
                return None
        except Exception as e:
            st.error(f"Error loading credentials: {e}")
            return None

    def load_tasks(self):
        try:
            gc = self.get_credentials()
            if not gc:
                return []
            sh = gc.open(SPREADSHEET_NAME)
            ws = sh.sheet1
            records = ws.get_all_records()
            formatted_records = [
                {
                    "description": rec.get("description", ""),
                    "building": rec.get("building", ""),
                    "tcd": rec.get("tcd", ""),
                    "comments": rec.get("comments", ""),
                    "category": rec.get("category", "OT"),
                    "last_updated": rec.get("last_updated", ""),
                    "closed": rec.get("closed", False)
                }
                for rec in records if any(rec.values())
            ]
            return formatted_records
        except gspread.SpreadsheetNotFound:
            st.error(f"Spreadsheet '{SPREADSHEET_NAME}' not found.")
            return []
        except Exception as e:
            st.error(f"Error loading tasks: {e}")
            return []

    def save_tasks(self, tasks):
        try:
            gc = self.get_credentials()
            if not gc:
                return False
            sh = gc.open(SPREADSHEET_NAME)
            ws = sh.sheet1
            ws.clear()
            if tasks:
                headers = ["description", "building", "tcd", "comments", "category", "last_updated", "closed"]
                ws.append_row(headers)
                for t in tasks:
                    ws.append_row([
                        t.get("description", ""),
                        t.get("building", ""),
                        t.get("tcd", ""),
                        t.get("comments", ""),
                        t.get("category", "OT"),
                        t.get("last_updated", ""),
                        t.get("closed", False)
                    ])
            return True
        except Exception as e:
            st.error(f"Error saving tasks: {e}")
            return False

    def add_or_update_task(self, task_data, idx=None):
        try:
            if idx is not None:
                self.tasks[idx] = task_data
            else:
                self.tasks.append(task_data)
            return self.save_tasks(self.tasks)
        except Exception as e:
            st.error(f"Error updating task: {e}")
            return False

    def delete_task(self, idx):
        try:
            if 0 <= idx < len(self.tasks):
                del self.tasks[idx]
                return self.save_tasks(self.tasks)
            return False
        except Exception as e:
            st.error(f"Error deleting task: {e}")
            return False

# --- HELPER FUNCTIONS ---
def clear_form():
    st.session_state.form_description = ''
    st.session_state.form_building = BUILDINGS[0]
    st.session_state.form_tcd = ''
    st.session_state.form_comments = ''
    st.session_state.form_category = 'OT'
    st.session_state.edit_mode = False
    st.session_state.selected_task = None

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Beldiev Original Board Operators", layout="wide")

    # Custom CSS styling
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            color: #2F3E46;
        }
        .stApp {
            background-color: #F8FAFB;
        }
        h1, h2, h3 {
            color: #1C3D5A;
            font-weight: 600;
        }
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            padding: 0.5em 1em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session
    if 'task_manager' not in st.session_state:
        st.session_state.task_manager = GoogleSheetsManager()
    if 'selected_task' not in st.session_state:
        st.session_state.selected_task = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'form_description' not in st.session_state:
        clear_form()
    if 'current_category' not in st.session_state:
        st.session_state.current_category = "All"

    tm = st.session_state.task_manager

    st.title("🧠 Beldiev Original Board Operators")
    st.caption("Efficient, synchronized task management for operations teams")

    # Sidebar
    with st.sidebar:
        st.subheader("📂 Filter by Category")
        st.session_state.current_category = st.selectbox(
            "Category View",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(st.session_state.current_category)
        )

        st.divider()
        st.subheader("📊 Statistics")
        cat_counts = {k: 0 for k in CATEGORIES if k != "All"}
        for t in tm.tasks:
            if t["category"] in cat_counts:
                cat_counts[t["category"]] += 1
        for cat, cnt in cat_counts.items():
            color = CATEGORIES[cat]
            st.markdown(f"<span style='color:{color};font-weight:600'>{cat}: {cnt}</span>", unsafe_allow_html=True)
        st.markdown(f"**Total Tasks: {len(tm.tasks)}**")

        if st.button("🔄 Refresh Data"):
            st.session_state.task_manager.tasks = tm.load_tasks()
            st.success("Data refreshed!")
            st.rerun()

    # --- TASK FORM ---
    st.header("📝 Task Entry / Edit Form")
    col1, col2 = st.columns(2)

    with col1:
        description = st.text_input("Task Description*", st.session_state.form_description)
        building = st.selectbox("Building", BUILDINGS, index=BUILDINGS.index(st.session_state.form_building))
        tcd = st.text_input("TCD", st.session_state.form_tcd)

    with col2:
        comments = st.text_input("Comments", st.session_state.form_comments)
        category = st.selectbox("Category", [c for c in CATEGORIES if c != "All"],
                                index=list(CATEGORIES.keys()).index(st.session_state.form_category))

    # Buttons: Add, Update, Delete
    colA, colB, colC, colD = st.columns(4)
    with colA:
        if st.session_state.edit_mode:
            if st.button("💾 Update Task", use_container_width=True):
                if not description.strip():
                    st.error("Description required.")
                else:
                    task = {
                        "description": description.strip(),
                        "building": building,
                        "tcd": tcd,
                        "comments": comments,
                        "category": category,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "closed": category == "CT"
                    }
                    idx = st.session_state.selected_task
                    if idx is not None and tm.add_or_update_task(task, idx):
                        st.success("Task updated successfully!")
                        clear_form()
                        st.rerun()
        else:
            if st.button("➕ Add Task", use_container_width=True):
                if not description.strip():
                    st.error("Description required.")
                else:
                    task = {
                        "description": description.strip(),
                        "building": building,
                        "tcd": tcd,
                        "comments": comments,
                        "category": category,
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "closed": category == "CT"
                    }
                    if tm.add_or_update_task(task):
                        st.success("Task added successfully!")
                        clear_form()
                        st.rerun()
    with colB:
        if st.session_state.edit_mode:
            if st.button("🗑️ Delete Task", use_container_width=True):
                idx = st.session_state.selected_task
                if idx is not None and tm.delete_task(idx):
                    st.success("Task deleted!")
                    clear_form()
                    st.rerun()
    with colC:
        if st.session_state.edit_mode:
            if st.button("❌ Cancel Edit", use_container_width=True):
                clear_form()
                st.rerun()
    with colD:
        if st.button("🧹 Clear Form", use_container_width=True):
            clear_form()
            st.rerun()

    # --- TASK LIST ---
    st.header("📋 Current Task List")
    filtered = [
        t for t in tm.tasks if st.session_state.current_category == "All"
        or t["category"] == st.session_state.current_category
    ]
    if not filtered:
        st.info("No tasks found.")
        return

    for i, t in enumerate(filtered):
        color = CATEGORIES.get(t["category"], "#f0f0f0")
        with st.container():
            cols = st.columns([0.4, 2, 1, 1, 2, 1, 1.3])
            with cols[0]:
                if st.button("✏️", key=f"edit_{i}"):
                    st.session_state.edit_mode = True
                    st.session_state.selected_task = i
                    st.session_state.form_description = t["description"]
                    st.session_state.form_building = t["building"]
                    st.session_state.form_tcd = t["tcd"]
                    st.session_state.form_comments = t["comments"]
                    st.session_state.form_category = t["category"]
                    st.rerun()
            with cols[1]:
                st.markdown(f"<b>{t['description']}</b>", unsafe_allow_html=True)
            with cols[2]:
                st.write(t["building"])
            with cols[3]:
                st.write(t["tcd"] or "-")
            with cols[4]:
                st.write(t["comments"] or "-")
            with cols[5]:
                st.markdown(f"<span style='background:{color};padding:3px 10px;border-radius:4px;'>{t['category']}</span>", unsafe_allow_html=True)
            with cols[6]:
                st.write(t["last_updated"])
        st.divider()

# --- RUN APP ---
if __name__ == "__main__":
    main()
