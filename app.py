import streamlit as st
import sqlite3
import pandas as pd
import calendar

from pathlib import Path
from datetime import date


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Smart Roster Management System",
    page_icon="📅",
    layout="wide"
)


# ==================================================
# MODERN INTERFACE STYLING
# ==================================================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f5f7fb 0%, #edf2fa 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #101a35 0%, #1d2b53 100%); }
    [data-testid="stSidebar"] * { color: #f5f7ff !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        background: rgba(255,255,255,.07); border-radius: 10px; padding: 7px 10px; margin: 3px 0;
    }
    [data-testid="stMetric"] { background: white; border: 1px solid #e4e9f2;
        padding: 17px 18px; border-radius: 15px; box-shadow: 0 5px 18px rgba(28,45,85,.06); }
    [data-testid="stMetricValue"] { color: #17264a; }
    div[data-testid="stForm"] { background: white; padding: 18px; border-radius: 14px; }
    div.stButton > button, div.stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] > button { border-radius: 10px; font-weight: 650; }
    h1, h2, h3 { color: #17264a; }
    .hero-card { padding: 25px 28px; border-radius: 18px; color: white;
        background: linear-gradient(115deg, #17264a 0%, #354fa0 60%, #7454c8 100%);
        margin-bottom: 18px; box-shadow: 0 10px 28px rgba(31,49,100,.16); }
    .hero-card h2 { color: white; margin: 0 0 7px 0; }
    .hero-card p { color: #e6eaff; margin: 0; }
    .small-note { color: #64748b; font-size:  .88rem; }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 2. DATABASE SETUP
# ==================================================

DATABASE_FOLDER = Path("database")
DATABASE_FOLDER.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_FOLDER / "roster.db"


def get_database_connection():
    return sqlite3.connect(DATABASE_PATH)


def create_tables():
    conn = get_database_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            email TEXT,
            pod_id INTEGER,
            availability TEXT DEFAULT 'Available'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pods (
            pod_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pod_name TEXT NOT NULL,
            pod_lead TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processes (
            process_id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            brand_id INTEGER,
            process_id INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            leave_date TEXT,
            leave_type TEXT
        )
    """)

    # Store public holidays.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT NOT NULL UNIQUE,
            holiday_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roster (
            roster_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            roster_date TEXT,
            status TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity_history (
            activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_time TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            activity_type TEXT NOT NULL,
            activity_details TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# ==================================================
# 3. DATABASE HELPER FUNCTIONS
# ==================================================

def get_record_count(table_name):
    allowed_tables = [
        "employees", "brands", "pods", "processes",
        "assignments", "leaves", "holidays", "roster"
    ]

    if table_name not in allowed_tables:
        return 0

    conn = get_database_connection()
    result = conn.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()
    conn.close()
    return result[0]


def get_employees():
    conn = get_database_connection()
    df = pd.read_sql_query("""
        SELECT employees.employee_id, employees.employee_name,
               employees.email, pods.pod_name, employees.availability
        FROM employees
        LEFT JOIN pods ON employees.pod_id = pods.pod_id
        ORDER BY employees.employee_id
    """, conn)
    conn.close()
    return df


def get_pods():
    conn = get_database_connection()
    df = pd.read_sql_query(
        "SELECT * FROM pods ORDER BY pod_id", conn
    )
    conn.close()
    return df


def get_brands():
    conn = get_database_connection()
    df = pd.read_sql_query(
        "SELECT * FROM brands ORDER BY brand_id", conn
    )
    conn.close()
    return df


def get_processes():
    conn = get_database_connection()
    df = pd.read_sql_query(
        "SELECT * FROM processes ORDER BY process_id", conn
    )
    conn.close()
    return df


def log_activity(activity_type, activity_details):
    """Save an important application action in the activity history."""
    conn = get_database_connection()
    conn.execute(
        "INSERT INTO activity_history (activity_type, activity_details) VALUES (?, ?)",
        (str(activity_type), str(activity_details))
    )
    conn.commit()
    conn.close()


def get_employee_status_for_date(employee_id, selected_date):
    """Use a generated roster status when present; otherwise check known restrictions."""
    date_text = selected_date.strftime("%Y-%m-%d")
    conn = get_database_connection()
    saved = conn.execute(
        "SELECT status FROM roster WHERE employee_id = ? AND roster_date = ? ORDER BY roster_id DESC LIMIT 1",
        (employee_id, date_text)
    ).fetchone()
    if saved:
        conn.close()
        return saved[0]
    leave = conn.execute(
        "SELECT leave_id FROM leaves WHERE employee_id = ? AND leave_date = ?",
        (employee_id, date_text)
    ).fetchone()
    holiday = conn.execute(
        "SELECT holiday_id FROM holidays WHERE holiday_date = ?", (date_text,)
    ).fetchone()
    employee = conn.execute(
        "SELECT availability FROM employees WHERE employee_id = ?", (employee_id,)
    ).fetchone()
    conn.close()
    if leave:
        return "Leave"
    if holiday:
        return "Public Holiday"
    if not employee or employee[0] == "Unavailable":
        return "Unavailable"
    return "Not Generated"


def get_assignments_detail():
    conn = get_database_connection()
    df = pd.read_sql_query("""
        SELECT a.employee_id, e.employee_name, b.brand_id, b.brand_name,
               p.process_id, p.process_name, e.pod_id, pods.pod_name
        FROM assignments a
        JOIN employees e ON a.employee_id = e.employee_id
        JOIN brands b ON a.brand_id = b.brand_id
        JOIN processes p ON a.process_id = p.process_id
        LEFT JOIN pods ON e.pod_id = pods.pod_id
        ORDER BY b.brand_name, p.process_name, e.employee_name
    """, conn)
    conn.close()
    return df


# ==================================================
# 4. APPLICATION HEADER
# ==================================================

st.markdown("<div class='hero-card'><h2>SMART ROSTER INTELLIGENCE</h2><p>Workforce operations • Scheduling • Availability insights • Conflict monitoring</p></div>", unsafe_allow_html=True)


# ==================================================
# 5. SIDEBAR NAVIGATION
# ==================================================

st.sidebar.title("Navigation")

selected_page = st.sidebar.radio(
    "Select a section",
    [
        "Dashboard",
        "Employees",
        "Brands",
        "Processes",
        "Pods",
        "Assignments",
        "Sample Data",
        "Roster",
        "Leave Management",
        "Public Holidays",
        "Roster Conflicts"
    
    ]
)


# ==================================================
# 6. DASHBOARD
# ==================================================

if selected_page == "Dashboard":
    st.header("📊 Workforce Command Centre")
    st.caption("A live overview of your people, assignments and scheduling data.")

    employees_total = get_record_count("employees")
    brands_total = get_record_count("brands")
    pods_total = get_record_count("pods")
    processes_total = get_record_count("processes")
    assignments_total = get_record_count("assignments")
    roster_total = get_record_count("roster")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Employees", employees_total, help="Employees registered in the system")
    k2.metric("Brands", brands_total)
    k3.metric("Pods", pods_total)
    k4.metric("Processes", processes_total)
    k5.metric("Assignments", assignments_total)

    st.divider()
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("📈 Workforce distribution")
        employee_df = get_employees()
        if not employee_df.empty:
            pod_counts = employee_df["pod_name"].fillna("Not Assigned").value_counts().rename_axis("Pod").reset_index(name="Employees")
            st.bar_chart(pod_counts.set_index("Pod"))
        else:
            st.info("Add employees to see workforce distribution.")
    with right:
        st.subheader("🧭 System readiness")
        readiness = [
            ("Employee records", employees_total), ("Brand records", brands_total),
            ("Process records", processes_total), ("Assignments", assignments_total),
            ("Generated roster rows", roster_total)
        ]
        for label, value in readiness:
            st.write(f"**{label}** · {value}")
            st.progress(min(value / max(employees_total, 1), 1.0) if label == "Generated roster rows" else (1.0 if value else 0.0))

    st.divider()
    st.subheader("⚡ Quick actions")
    q1, q2, q3, q4 = st.columns(4)
    q1.info("👥 **People**\n\nManage employees and pods.")
    q2.info("🔗 **Assignments**\n\nConnect employees to brands and processes.")
    q3.info("📅 **Roster**\n\nGenerate monthly schedules.")
    q4.info("🧠 **Intelligence**\n\nExplore staffing and workload insights.")
    st.caption("Tip: Generate a monthly roster first to unlock date-specific heatmap and workload insights.")


# ==================================================
# 7. EMPLOYEE MANAGEMENT
# ==================================================

elif selected_page == "Employees":
    st.header("👥 Employee Management")

    tab1, tab2, tab3 = st.tabs([
        "Add Employee", "View Employees", "Edit / Delete Employee"
    ])

    with tab1:
        st.subheader("Add New Employee")
        pod_df = get_pods()
        pod_options = {
            row["pod_name"]: row["pod_id"]
            for _, row in pod_df.iterrows()
        }

        with st.form("add_employee_form"):
            employee_name = st.text_input("Employee Name")
            email = st.text_input("Email Address")
            selected_pod = st.selectbox(
                "Select Pod",
                ["Not Assigned"] + list(pod_options.keys())
            )
            availability = st.selectbox(
                "Availability", ["Available", "Unavailable"]
            )
            submitted = st.form_submit_button("Add Employee")

            if submitted:
                if not employee_name.strip():
                    st.error("Please enter employee name.")
                else:
                    conn = get_database_connection()
                    conn.execute("""
                        INSERT INTO employees
                        (employee_name, email, pod_id, availability)
                        VALUES (?, ?, ?, ?)
                    """, (
                        employee_name.strip(),
                        email.strip(),
                        pod_options.get(selected_pod),
                        availability
                    ))
                    conn.commit()
                    conn.close()
                    st.success("Employee added successfully!")
                    st.rerun()

    with tab2:
        st.subheader("Employee List")
        employee_df = get_employees()
        if employee_df.empty:
            st.info("No employees found.")
        else:
            st.dataframe(
                employee_df, use_container_width=True, hide_index=True
            )

    with tab3:
        conn = get_database_connection()
        employee_options = conn.execute("""
            SELECT employee_id, employee_name
            FROM employees ORDER BY employee_name
        """).fetchall()
        conn.close()

        if not employee_options:
            st.info("No employees available.")
        else:
            employee_dict = {
                f"{name} (ID: {emp_id})": emp_id
                for emp_id, name in employee_options
            }
            selected_employee = st.selectbox(
                "Select Employee", list(employee_dict.keys())
            )
            employee_id = employee_dict[selected_employee]

            conn = get_database_connection()
            employee = conn.execute("""
                SELECT employee_name, email, pod_id, availability
                FROM employees WHERE employee_id = ?
            """, (employee_id,)).fetchone()
            conn.close()

            pod_df = get_pods()
            pod_options = {
                row["pod_name"]: row["pod_id"]
                for _, row in pod_df.iterrows()
            }
            current_pod = "Not Assigned"
            for name, pod_id in pod_options.items():
                if pod_id == employee[2]:
                    current_pod = name

            pod_names = ["Not Assigned"] + list(pod_options.keys())
            availability_options = ["Available", "Unavailable"]
            current_availability = (
                employee[3]
                if employee[3] in availability_options
                else "Available"
            )

            with st.form("edit_employee_form"):
                new_name = st.text_input("Employee Name", value=employee[0])
                new_email = st.text_input("Email", value=employee[1] or "")
                new_pod = st.selectbox(
                    "Pod", pod_names, index=pod_names.index(current_pod)
                )
                new_availability = st.selectbox(
                    "Availability",
                    availability_options,
                    index=availability_options.index(current_availability)
                )
                update_employee = st.form_submit_button("Update Employee")

                if update_employee:
                    if not new_name.strip():
                        st.error("Employee name cannot be empty.")
                    else:
                        conn = get_database_connection()
                        conn.execute("""
                            UPDATE employees
                            SET employee_name = ?, email = ?,
                                pod_id = ?, availability = ?
                            WHERE employee_id = ?
                        """, (
                            new_name.strip(), new_email.strip(),
                            pod_options.get(new_pod),
                            new_availability, employee_id
                        ))
                        conn.commit()
                        conn.close()
                        st.success("Employee updated successfully!")
                        st.rerun()

            if st.button("Delete Employee", key="delete_employee"):
                conn = get_database_connection()
                conn.execute(
                    "DELETE FROM assignments WHERE employee_id = ?",
                    (employee_id,)
                )
                conn.execute(
                    "DELETE FROM leaves WHERE employee_id = ?",
                    (employee_id,)
                )
                conn.execute(
                    "DELETE FROM roster WHERE employee_id = ?",
                    (employee_id,)
                )
                conn.execute(
                    "DELETE FROM employees WHERE employee_id = ?",
                    (employee_id,)
                )
                conn.commit()
                conn.close()
                st.success("Employee deleted successfully!")
                st.rerun()


# ==================================================
# 8. BRAND MANAGEMENT
# ==================================================

elif selected_page == "Brands":
    st.header("🏢 Brand Management")
    tab1, tab2, tab3 = st.tabs([
        "Add Brand", "View Brands", "Edit / Delete Brand"
    ])

    with tab1:
        with st.form("add_brand_form"):
            brand_name = st.text_input("Brand Name")
            submitted = st.form_submit_button("Add Brand")
            if submitted:
                if not brand_name.strip():
                    st.error("Please enter a brand name.")
                else:
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT brand_id FROM brands
                        WHERE LOWER(brand_name) = LOWER(?)
                    """, (brand_name.strip(),)).fetchone()

                    if existing:
                        st.warning("This brand already exists.")
                    else:
                        conn.execute(
                            "INSERT INTO brands (brand_name) VALUES (?)",
                            (brand_name.strip(),)
                        )
                        conn.commit()
                        st.success("Brand added successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        brand_df = get_brands()
        if brand_df.empty:
            st.info("No brands found.")
        else:
            st.dataframe(brand_df, use_container_width=True, hide_index=True)

    with tab3:
        brand_df = get_brands()
        if brand_df.empty:
            st.info("No brands available.")
        else:
            brand_dict = {
                f"{row['brand_name']} (ID: {row['brand_id']})":
                row["brand_id"] for _, row in brand_df.iterrows()
            }
            selected_brand = st.selectbox(
                "Select Brand", list(brand_dict.keys())
            )
            brand_id = brand_dict[selected_brand]
            current_brand = brand_df[
                brand_df["brand_id"] == brand_id
            ]["brand_name"].iloc[0]

            with st.form("edit_brand_form"):
                new_brand_name = st.text_input(
                    "Brand Name", value=current_brand
                )
                update_brand = st.form_submit_button("Update Brand")

                if update_brand:
                    conn = get_database_connection()
                    duplicate = conn.execute("""
                        SELECT brand_id FROM brands
                        WHERE LOWER(brand_name) = LOWER(?)
                        AND brand_id != ?
                    """, (new_brand_name.strip(), brand_id)).fetchone()

                    if not new_brand_name.strip():
                        st.error("Brand name cannot be empty.")
                    elif duplicate:
                        st.error("This brand already exists.")
                    else:
                        conn.execute("""
                            UPDATE brands SET brand_name = ?
                            WHERE brand_id = ?
                        """, (new_brand_name.strip(), brand_id))
                        conn.commit()
                        st.success("Brand updated successfully!")
                        st.rerun()
                    conn.close()

            if st.button("Delete Brand", key="delete_brand"):
                conn = get_database_connection()
                assigned = conn.execute("""
                    SELECT assignment_id FROM assignments WHERE brand_id = ?
                """, (brand_id,)).fetchone()

                if assigned:
                    st.error(
                        "Cannot delete this brand because it is used "
                        "in an assignment."
                    )
                else:
                    conn.execute(
                        "DELETE FROM brands WHERE brand_id = ?", (brand_id,)
                    )
                    conn.commit()
                    st.success("Brand deleted successfully!")
                    st.rerun()
                conn.close()


# ==================================================
# 9. PROCESS MANAGEMENT
# ==================================================

elif selected_page == "Processes":
    st.header("⚙️ Process Management")
    tab1, tab2, tab3 = st.tabs([
        "Add Process", "View Processes", "Edit / Delete Process"
    ])

    with tab1:
        with st.form("add_process_form"):
            process_name = st.text_input("Process Name")
            submitted = st.form_submit_button("Add Process")
            if submitted:
                if not process_name.strip():
                    st.error("Please enter a process name.")
                else:
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT process_id FROM processes
                        WHERE LOWER(process_name) = LOWER(?)
                    """, (process_name.strip(),)).fetchone()
                    if existing:
                        st.warning("This process already exists.")
                    else:
                        conn.execute(
                            "INSERT INTO processes (process_name) VALUES (?)",
                            (process_name.strip(),)
                        )
                        conn.commit()
                        st.success("Process added successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        process_df = get_processes()
        if process_df.empty:
            st.info("No processes found.")
        else:
            st.dataframe(
                process_df, use_container_width=True, hide_index=True
            )

    with tab3:
        process_df = get_processes()
        if process_df.empty:
            st.info("No processes available.")
        else:
            process_dict = {
                f"{row['process_name']} (ID: {row['process_id']})":
                row["process_id"] for _, row in process_df.iterrows()
            }
            selected_process = st.selectbox(
                "Select Process", list(process_dict.keys())
            )
            process_id = process_dict[selected_process]
            current_process = process_df[
                process_df["process_id"] == process_id
            ]["process_name"].iloc[0]

            with st.form("edit_process_form"):
                new_process_name = st.text_input(
                    "Process Name", value=current_process
                )
                update_process = st.form_submit_button("Update Process")
                if update_process:
                    conn = get_database_connection()
                    duplicate = conn.execute("""
                        SELECT process_id FROM processes
                        WHERE LOWER(process_name) = LOWER(?)
                        AND process_id != ?
                    """, (new_process_name.strip(), process_id)).fetchone()

                    if not new_process_name.strip():
                        st.error("Process name cannot be empty.")
                    elif duplicate:
                        st.error("This process already exists.")
                    else:
                        conn.execute("""
                            UPDATE processes SET process_name = ?
                            WHERE process_id = ?
                        """, (new_process_name.strip(), process_id))
                        conn.commit()
                        st.success("Process updated successfully!")
                        st.rerun()
                    conn.close()

            if st.button("Delete Process", key="delete_process"):
                conn = get_database_connection()
                assigned = conn.execute("""
                    SELECT assignment_id FROM assignments WHERE process_id = ?
                """, (process_id,)).fetchone()
                if assigned:
                    st.error(
                        "Cannot delete this process because it is used "
                        "in an assignment."
                    )
                else:
                    conn.execute(
                        "DELETE FROM processes WHERE process_id = ?",
                        (process_id,)
                    )
                    conn.commit()
                    st.success("Process deleted successfully!")
                    st.rerun()
                conn.close()


# ==================================================
# 10. POD MANAGEMENT
# ==================================================

elif selected_page == "Pods":
    st.header("👨‍💼 Pod Management")
    tab1, tab2, tab3 = st.tabs([
        "Add Pod", "View Pods", "Edit / Delete Pod"
    ])

    with tab1:
        with st.form("add_pod_form"):
            pod_name = st.text_input("Pod Name")
            pod_lead = st.text_input("Pod Lead")
            submitted = st.form_submit_button("Add Pod")
            if submitted:
                if not pod_name.strip():
                    st.error("Please enter a pod name.")
                else:
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT pod_id FROM pods
                        WHERE LOWER(pod_name) = LOWER(?)
                    """, (pod_name.strip(),)).fetchone()
                    if existing:
                        st.warning("This pod already exists.")
                    else:
                        conn.execute("""
                            INSERT INTO pods (pod_name, pod_lead)
                            VALUES (?, ?)
                        """, (pod_name.strip(), pod_lead.strip()))
                        conn.commit()
                        st.success("Pod added successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        conn = get_database_connection()
        pod_df = pd.read_sql_query("""
            SELECT pods.pod_id, pods.pod_name, pods.pod_lead,
                   COUNT(employees.employee_id) AS employee_count
            FROM pods
            LEFT JOIN employees ON pods.pod_id = employees.pod_id
            GROUP BY pods.pod_id
            ORDER BY pods.pod_id
        """, conn)
        conn.close()
        if pod_df.empty:
            st.info("No pods found.")
        else:
            st.dataframe(pod_df, use_container_width=True, hide_index=True)

    with tab3:
        pod_df = get_pods()
        if pod_df.empty:
            st.info("No pods available.")
        else:
            pod_dict = {
                f"{row['pod_name']} (ID: {row['pod_id']})":
                row["pod_id"] for _, row in pod_df.iterrows()
            }
            selected_pod = st.selectbox("Select Pod", list(pod_dict.keys()))
            pod_id = pod_dict[selected_pod]
            current_pod = pod_df[pod_df["pod_id"] == pod_id].iloc[0]

            with st.form("edit_pod_form"):
                new_pod_name = st.text_input(
                    "Pod Name", value=current_pod["pod_name"]
                )
                new_pod_lead = st.text_input(
                    "Pod Lead", value=current_pod["pod_lead"] or ""
                )
                update_pod = st.form_submit_button("Update Pod")
                if update_pod:
                    conn = get_database_connection()
                    duplicate = conn.execute("""
                        SELECT pod_id FROM pods
                        WHERE LOWER(pod_name) = LOWER(?)
                        AND pod_id != ?
                    """, (new_pod_name.strip(), pod_id)).fetchone()
                    if not new_pod_name.strip():
                        st.error("Pod name cannot be empty.")
                    elif duplicate:
                        st.error("This pod already exists.")
                    else:
                        conn.execute("""
                            UPDATE pods SET pod_name = ?, pod_lead = ?
                            WHERE pod_id = ?
                        """, (new_pod_name.strip(), new_pod_lead.strip(), pod_id))
                        conn.commit()
                        st.success("Pod updated successfully!")
                        st.rerun()
                    conn.close()

            if st.button("Delete Pod", key="delete_pod"):
                conn = get_database_connection()
                assigned = conn.execute("""
                    SELECT employee_id FROM employees WHERE pod_id = ?
                """, (pod_id,)).fetchone()
                if assigned:
                    st.error(
                        "Cannot delete this pod because employees "
                        "are assigned to it."
                    )
                else:
                    conn.execute(
                        "DELETE FROM pods WHERE pod_id = ?", (pod_id,)
                    )
                    conn.commit()
                    st.success("Pod deleted successfully!")
                    st.rerun()
                conn.close()


# ==================================================
# 11. EMPLOYEE - BRAND ASSIGNMENTS
# ==================================================

elif selected_page == "Assignments":
    st.header("🔗 Employee - Brand Assignments")
    tab1, tab2 = st.tabs(["Create Assignment", "View Assignments"])

    with tab1:
        conn = get_database_connection()
        employees = conn.execute("""
            SELECT employee_id, employee_name FROM employees
            ORDER BY employee_name
        """).fetchall()
        brands = conn.execute("""
            SELECT brand_id, brand_name FROM brands ORDER BY brand_name
        """).fetchall()
        processes = conn.execute("""
            SELECT process_id, process_name FROM processes
            ORDER BY process_name
        """).fetchall()
        conn.close()

        if not employees:
            st.warning("Please add employees first.")
        elif not brands:
            st.warning("Please add brands first.")
        elif not processes:
            st.warning("Please add processes first.")
        else:
            employee_options = {name: emp_id for emp_id, name in employees}
            brand_options = {name: brand_id for brand_id, name in brands}
            process_options = {
                name: process_id for process_id, name in processes
            }

            with st.form("assignment_form"):
                selected_employee = st.selectbox(
                    "Select Employee", list(employee_options.keys())
                )
                selected_brand = st.selectbox(
                    "Select Brand", list(brand_options.keys())
                )
                selected_process = st.selectbox(
                    "Select Process", list(process_options.keys())
                )
                submitted = st.form_submit_button("Create Assignment")

                if submitted:
                    employee_id = employee_options[selected_employee]
                    brand_id = brand_options[selected_brand]
                    process_id = process_options[selected_process]
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT assignment_id FROM assignments
                        WHERE employee_id = ? AND brand_id = ?
                        AND process_id = ?
                    """, (employee_id, brand_id, process_id)).fetchone()

                    if existing:
                        st.warning("This assignment already exists.")
                    else:
                        conn.execute("""
                            INSERT INTO assignments
                            (employee_id, brand_id, process_id)
                            VALUES (?, ?, ?)
                        """, (employee_id, brand_id, process_id))
                        conn.commit()
                        st.success("Assignment created successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        conn = get_database_connection()
        assignment_df = pd.read_sql_query("""
            SELECT assignments.assignment_id, employees.employee_name,
                   brands.brand_name, processes.process_name
            FROM assignments
            LEFT JOIN employees
                ON assignments.employee_id = employees.employee_id
            LEFT JOIN brands
                ON assignments.brand_id = brands.brand_id
            LEFT JOIN processes
                ON assignments.process_id = processes.process_id
            ORDER BY assignments.assignment_id
        """, conn)
        conn.close()

        if assignment_df.empty:
            st.info("No assignments found.")
        else:
            st.dataframe(
                assignment_df, use_container_width=True, hide_index=True
            )
            assignment_options = {
                f"ID {row['assignment_id']} - "
                f"{row['employee_name']} / {row['brand_name']}":
                row["assignment_id"]
                for _, row in assignment_df.iterrows()
            }
            selected_assignment = st.selectbox(
                "Select Assignment to Delete",
                list(assignment_options.keys())
            )
            if st.button("Delete Assignment"):
                conn = get_database_connection()
                conn.execute(
                    "DELETE FROM assignments WHERE assignment_id = ?",
                    (assignment_options[selected_assignment],)
                )
                conn.commit()
                conn.close()
                st.success("Assignment deleted successfully!")
                st.rerun()


# ==================================================
# 12. SAMPLE DATA GENERATION
# ==================================================

elif selected_page == "Sample Data":
    st.header("📊 Sample Data Generation")
    st.write(
        "Generate fictional employee records and assignments "
        "to test the application."
    )
    st.info(
        "Sample data will be added to your existing database. "
        "Your current records will not be deleted."
    )

    col1, col2 = st.columns(2)
    col1.metric("Current Employees", get_record_count("employees"))
    col2.metric("Current Assignments", get_record_count("assignments"))

    st.divider()

    if st.button("🚀 Generate Sample Dataset", use_container_width=True):
        conn = get_database_connection()
        cursor = conn.cursor()

        pod_ids = [
            row[0] for row in cursor.execute(
                "SELECT pod_id FROM pods"
            ).fetchall()
        ]
        brand_ids = [
            row[0] for row in cursor.execute(
                "SELECT brand_id FROM brands"
            ).fetchall()
        ]
        process_ids = [
            row[0] for row in cursor.execute(
                "SELECT process_id FROM processes"
            ).fetchall()
        ]

        if not pod_ids:
            st.error("Please create at least one pod first.")
        elif not brand_ids:
            st.error("Please create at least one brand first.")
        elif not process_ids:
            st.error("Please create at least one process first.")
        else:
            sample_employees = [
                ("Rahul Sharma", "rahul@gmail.com"),
                ("Priya Patel", "priya@gmail.com"),
                ("Amit Kumar", "amit@gmail.com"),
                ("Sneha Reddy", "sneha@gmail.com"),
                ("Arjun Mehta", "arjun@gmail.com"),
                ("Neha Singh", "neha@gmail.com"),
                ("Karan Shah", "karan@gmail.com"),
                ("Ananya Das", "ananya@gmail.com"),
                ("Rohit Verma", "rohit@gmail.com"),
                ("Pooja Nair", "pooja@gmail.com"),
                ("Vikram Rao", "vikram@gmail.com"),
                ("Isha Gupta", "isha@gmail.com"),
                ("Aditya Joshi", "aditya@gmail.com"),
                ("Meera Iyer", "meera@gmail.com"),
                ("Sanjay Kumar", "sanjay@gmail.com"),
                ("Kavya Menon", "kavya@gmail.com"),
                ("Nikhil Jain", "nikhil@gmail.com"),
                ("Riya Kapoor", "riya@gmail.com"),
                ("Varun Malhotra", "varun@gmail.com"),
                ("Divya Shetty", "divya@gmail.com"),
                ("Manish Yadav", "manish@gmail.com"),
                ("Aisha Khan", "aisha@gmail.com"),
                ("Suresh Pillai", "suresh@gmail.com"),
                ("Tanya Bose", "tanya@gmail.com"),
                ("Deepak Mishra", "deepak@gmail.com"),
                ("Simran Kaur", "simran@gmail.com"),
                ("Akash Sinha", "akash@gmail.com"),
                ("Nisha Thomas", "nisha@gmail.com"),
                ("Harish Bhat", "harish@gmail.com"),
                ("Swati Roy", "swati@gmail.com")
            ]

            added_employees = 0
            added_assignments = 0

            for index, (employee_name, email) in enumerate(sample_employees):
                existing = cursor.execute("""
                    SELECT employee_id FROM employees
                    WHERE LOWER(email) = LOWER(?)
                """, (email,)).fetchone()

                if existing:
                    employee_id = existing[0]
                else:
                    pod_id = pod_ids[index % len(pod_ids)]
                    cursor.execute("""
                        INSERT INTO employees
                        (employee_name, email, pod_id, availability)
                        VALUES (?, ?, ?, ?)
                    """, (employee_name, email, pod_id, "Available"))
                    employee_id = cursor.lastrowid
                    added_employees += 1

                for assignment_number in range(2):
                    brand_id = brand_ids[
                        (index + assignment_number) % len(brand_ids)
                    ]
                    process_id = process_ids[
                        (index + assignment_number) % len(process_ids)
                    ]
                    existing_assignment = cursor.execute("""
                        SELECT assignment_id FROM assignments
                        WHERE employee_id = ? AND brand_id = ?
                        AND process_id = ?
                    """, (employee_id, brand_id, process_id)).fetchone()

                    if not existing_assignment:
                        cursor.execute("""
                            INSERT INTO assignments
                            (employee_id, brand_id, process_id)
                            VALUES (?, ?, ?)
                        """, (employee_id, brand_id, process_id))
                        added_assignments += 1

            conn.commit()
            conn.close()
            st.success("Sample dataset generated successfully!")
            st.write(f"New employees added: {added_employees}")
            st.write(f"New assignments added: {added_assignments}")
            st.rerun()

    st.divider()
    st.subheader("Current Database Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("Employees", get_record_count("employees"))
    col2.metric("Brands", get_record_count("brands"))
    col3.metric("Assignments", get_record_count("assignments"))


# ==================================================
# 13. AUTOMATIC MONTHLY ROSTER GENERATION
# ==================================================

elif selected_page == "Roster":
    st.header("📅 Automatic Monthly Roster Generator")
    st.write(
        "Generate monthly employee schedules with "
        "automatically rotating weekly offs."
    )
    st.info(
        "Public holidays, employee leaves and unavailable status "
        "are included when the roster is generated."
    )

    st.subheader("1. Select Month")
    selected_month = st.date_input(
        "Choose any date from the month",
        value=date.today(),
        key="roster_month"
    )
    year = selected_month.year
    month = selected_month.month
    month_key = selected_month.strftime("%Y-%m")
    total_days = calendar.monthrange(year, month)[1]
    first_day = date(year, month, 1)

    st.write(
        f"Selected Month: **{calendar.month_name[month]} {year}**"
    )
    st.write(f"Total Days: **{total_days}**")
    st.divider()

    conn = get_database_connection()
    employees = conn.execute("""
        SELECT employee_id, employee_name, availability
        FROM employees ORDER BY employee_id
    """).fetchall()
    conn.close()

    if not employees:
        st.warning("Please add employees before generating a roster.")
    else:
        st.subheader("2. Generate Monthly Roster")
        st.write(f"Employees available: **{len(employees)}**")

        if st.button("🚀 Generate Monthly Roster", use_container_width=True):
            conn = get_database_connection()
            cursor = conn.cursor()

            leave_records = cursor.execute("""
                SELECT employee_id, leave_date FROM leaves
                WHERE substr(leave_date, 1, 7) = ?
            """, (month_key,)).fetchall()
            leave_dates = {
                (employee_id, leave_date)
                for employee_id, leave_date in leave_records
            }

            holiday_records = cursor.execute("""
                SELECT holiday_date FROM holidays
                WHERE substr(holiday_date, 1, 7) = ?
            """, (month_key,)).fetchall()
            holiday_dates = {row[0] for row in holiday_records}

            # Regenerate only the selected month's roster.
            cursor.execute("""
                DELETE FROM roster
                WHERE substr(roster_date, 1, 7) = ?
            """, (month_key,))

            roster_records = []

            for employee_index, employee in enumerate(employees):
                employee_id = employee[0]
                availability = employee[2]

                for day_number in range(1, total_days + 1):
                    current_day = date(year, month, day_number)
                    current_date = current_day.strftime("%Y-%m-%d")

                    # Priority: leave, public holiday, unavailable, weekly off.
                    if (employee_id, current_date) in leave_dates:
                        status = "Leave"
                    elif current_date in holiday_dates:
                        status = "Public Holiday"
                    elif availability == "Unavailable":
                        status = "Unavailable"
                    else:
                        week_index = (
                            (current_day - first_day).days
                            + first_day.weekday()
                        ) // 7
                        off_weekday = (employee_index + week_index) % 7

                        if current_day.weekday() == off_weekday:
                            status = "Weekly Off"
                        else:
                            status = "Working"

                    roster_records.append((
                        employee_id, current_date, status
                    ))

            cursor.executemany("""
                INSERT INTO roster (employee_id, roster_date, status)
                VALUES (?, ?, ?)
            """, roster_records)

            conn.commit()
            conn.close()
            log_activity("Roster Generated", f"Generated roster for {calendar.month_name[month]} {year} with {len(employees)} employees.")
            st.success("Monthly roster generated successfully!")
            st.rerun()

    st.divider()
    st.subheader("3. Generated Employee Schedule")

    conn = get_database_connection()
    roster_df = pd.read_sql_query("""
        SELECT employees.employee_name, roster.roster_date, roster.status
        FROM roster
        INNER JOIN employees
            ON roster.employee_id = employees.employee_id
        WHERE substr(roster.roster_date, 1, 7) = ?
        ORDER BY roster.roster_date, employees.employee_name
    """, conn, params=(month_key,))
    conn.close()

    if roster_df.empty:
        st.info(
            "No roster found for this month. "
            "Click Generate Monthly Roster to create one."
        )
    else:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", len(roster_df))
        col2.metric(
            "Working Days",
            len(roster_df[roster_df["status"] == "Working"])
        )
        col3.metric(
            "Weekly Offs",
            len(roster_df[roster_df["status"] == "Weekly Off"])
        )
        col4.metric(
            "Leaves",
            len(roster_df[roster_df["status"] == "Leave"])
        )

        holiday_count = len(
            roster_df[roster_df["status"] == "Public Holiday"]
        )
        st.metric("Public Holiday Records", holiday_count)

        st.subheader("Monthly Employee Schedule")
        st.dataframe(
            roster_df, use_container_width=True, hide_index=True
        )

        csv_data = roster_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Monthly Roster",
            data=csv_data,
            file_name=f"roster_{month_key}.csv",
            mime="text/csv"
        )


# ==================================================
# 14. LEAVE MANAGEMENT
# ==================================================

elif selected_page == "Leave Management":
    st.header("🏖️ Employee Leave Management")
    tab1, tab2 = st.tabs(["Add Leave", "View Leaves"])

    with tab1:
        conn = get_database_connection()
        employees = conn.execute("""
            SELECT employee_id, employee_name FROM employees
            ORDER BY employee_name
        """).fetchall()
        conn.close()

        if not employees:
            st.warning("Please add employees first.")
        else:
            employee_options = {
                name: employee_id for employee_id, name in employees
            }

            with st.form("add_leave_form"):
                selected_employee = st.selectbox(
                    "Select Employee", list(employee_options.keys())
                )
                leave_date = st.date_input("Leave Date", value=date.today())
                leave_type = st.selectbox(
                    "Leave Type",
                    ["Casual Leave", "Sick Leave", "Emergency Leave", "Other"]
                )
                submitted = st.form_submit_button("Add Leave")

                if submitted:
                    employee_id = employee_options[selected_employee]
                    date_string = leave_date.strftime("%Y-%m-%d")
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT leave_id FROM leaves
                        WHERE employee_id = ? AND leave_date = ?
                    """, (employee_id, date_string)).fetchone()

                    if existing:
                        st.warning(
                            "Leave is already registered for this employee "
                            "and date."
                        )
                    else:
                        conn.execute("""
                            INSERT INTO leaves
                            (employee_id, leave_date, leave_type)
                            VALUES (?, ?, ?)
                        """, (employee_id, date_string, leave_type))
                        conn.commit()
                        log_activity("Leave Added", f"Leave registered for {selected_employee} on {date_string} ({leave_type}).")
                        st.success("Leave added successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        conn = get_database_connection()
        leave_df = pd.read_sql_query("""
            SELECT leaves.leave_id, employees.employee_name,
                   leaves.leave_date, leaves.leave_type
            FROM leaves
            LEFT JOIN employees ON leaves.employee_id = employees.employee_id
            ORDER BY leaves.leave_date
        """, conn)
        conn.close()

        if leave_df.empty:
            st.info("No leave records found.")
        else:
            st.dataframe(leave_df, use_container_width=True, hide_index=True)
            leave_options = {
                f"{row['employee_name']} - {row['leave_date']} - "
                f"{row['leave_type']}": row["leave_id"]
                for _, row in leave_df.iterrows()
            }
            selected_leave = st.selectbox(
                "Select Leave to Delete", list(leave_options.keys())
            )
            if st.button("Delete Leave"):
                conn = get_database_connection()
                conn.execute(
                    "DELETE FROM leaves WHERE leave_id = ?",
                    (leave_options[selected_leave],)
                )
                conn.commit()
                conn.close()
                st.success("Leave deleted successfully!")
                st.rerun()


# ==================================================
# 15. PUBLIC HOLIDAY MANAGEMENT
# ==================================================

elif selected_page == "Public Holidays":
    st.header("🎉 Public Holiday Management")
    st.write(
        "Add company or public holidays. These dates will be marked "
        "as Public Holiday in the monthly roster."
    )

    tab1, tab2 = st.tabs(["Add Holiday", "View / Delete Holidays"])

    with tab1:
        with st.form("add_holiday_form"):
            holiday_name = st.text_input("Holiday Name")
            holiday_date = st.date_input(
                "Holiday Date", value=date.today(), key="holiday_date"
            )
            submitted = st.form_submit_button("Add Public Holiday")

            if submitted:
                if not holiday_name.strip():
                    st.error("Please enter a holiday name.")
                else:
                    date_string = holiday_date.strftime("%Y-%m-%d")
                    conn = get_database_connection()
                    existing = conn.execute("""
                        SELECT holiday_id FROM holidays
                        WHERE holiday_date = ?
                    """, (date_string,)).fetchone()

                    if existing:
                        st.warning(
                            "A holiday is already registered for this date."
                        )
                    else:
                        conn.execute("""
                            INSERT INTO holidays (holiday_date, holiday_name)
                            VALUES (?, ?)
                        """, (date_string, holiday_name.strip()))
                        conn.commit()
                        log_activity("Holiday Added", f"Added {holiday_name.strip()} on {date_string}.")
                        st.success("Public holiday added successfully!")
                        st.rerun()
                    conn.close()

    with tab2:
        conn = get_database_connection()
        holiday_df = pd.read_sql_query("""
            SELECT holiday_id, holiday_date, holiday_name
            FROM holidays
            ORDER BY holiday_date
        """, conn)
        conn.close()

        if holiday_df.empty:
            st.info("No public holidays added yet.")
        else:
            st.dataframe(
                holiday_df, use_container_width=True, hide_index=True
            )
            holiday_options = {
                f"{row['holiday_date']} - {row['holiday_name']}":
                row["holiday_id"]
                for _, row in holiday_df.iterrows()
            }
            selected_holiday = st.selectbox(
                "Select Holiday to Delete", list(holiday_options.keys())
            )

            if st.button("Delete Public Holiday"):
                conn = get_database_connection()
                conn.execute(
                    "DELETE FROM holidays WHERE holiday_id = ?",
                    (holiday_options[selected_holiday],)
                )
                conn.commit()
                conn.close()
                st.success("Public holiday deleted successfully!")
                st.rerun()


# ==================================================
# 16. ROSTER CONFLICT DETECTION
# ==================================================

elif selected_page == "Roster Conflicts":
    st.header("⚠️ Roster Conflict Detection")

    st.write(
        "Check employee schedules for conflicts with "
        "leaves, public holidays and duplicate records."
    )

    conn = get_database_connection()

    # Find employees marked as working on leave or holiday dates.
    conflict_df = pd.read_sql_query("""
        SELECT
            employees.employee_id,
            employees.employee_name,
            roster.roster_date,
            roster.status,
            CASE
                WHEN leaves.leave_id IS NOT NULL
                    THEN 'Working on an approved leave date'
                WHEN holidays.holiday_id IS NOT NULL
                    THEN 'Working on a public holiday'
            END AS conflict_reason
        FROM roster
        INNER JOIN employees
            ON roster.employee_id = employees.employee_id
        LEFT JOIN leaves
            ON roster.employee_id = leaves.employee_id
            AND roster.roster_date = leaves.leave_date
        LEFT JOIN holidays
            ON roster.roster_date = holidays.holiday_date
        WHERE roster.status = 'Working'
            AND (
                leaves.leave_id IS NOT NULL
                OR holidays.holiday_id IS NOT NULL
            )
        ORDER BY roster.roster_date
    """, conn)

    # Find duplicate roster rows for the same employee and date.
    duplicate_df = pd.read_sql_query("""
        SELECT
            employees.employee_name,
            roster.roster_date,
            COUNT(*) AS duplicate_count
        FROM roster
        INNER JOIN employees
            ON roster.employee_id = employees.employee_id
        GROUP BY roster.employee_id, roster.roster_date
        HAVING COUNT(*) > 1
        ORDER BY roster.roster_date
    """, conn)

    conn.close()

    conflict_count = len(conflict_df)
    duplicate_count = len(duplicate_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Leave / Holiday Conflicts", conflict_count)
    col2.metric("Duplicate Records", duplicate_count)
    col3.metric("Total Issues", conflict_count + duplicate_count)

    st.divider()
    st.subheader("1. Leave and Holiday Conflicts")

    if conflict_df.empty:
        st.success("No leave or holiday conflicts found!")
    else:
        st.error("Scheduling conflicts were found.")
        st.dataframe(
            conflict_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("2. Duplicate Roster Records")

    if duplicate_df.empty:
        st.success("No duplicate roster records found!")
    else:
        st.warning("Duplicate schedule records were found.")
        st.dataframe(
            duplicate_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    if conflict_count == 0 and duplicate_count == 0:
        st.success("Roster health check completed successfully!")


# ==================================================
# 17. STAFFING HEATMAP
# ==================================================

elif selected_page == "Staffing Heatmap":
    st.header("🟩 Smart Staffing Heatmap")
    st.write("See how many assigned employees are marked as working for each brand and process on each date.")
    selected_month_heat = st.date_input("Select month", value=date.today(), key="heatmap_month")
    month_key_heat = selected_month_heat.strftime("%Y-%m")
    assignments_df = get_assignments_detail()
    conn = get_database_connection()
    roster_heat = pd.read_sql_query("""
        SELECT r.employee_id, r.roster_date, r.status
        FROM roster r WHERE substr(r.roster_date, 1, 7) = ?
    """, conn, params=(month_key_heat,))
    conn.close()
    if assignments_df.empty:
        st.warning("Create employee-brand-process assignments first.")
    elif roster_heat.empty:
        st.info("No roster exists for this month. Open the Roster page and generate it first.")
    else:
        working = roster_heat[roster_heat["status"] == "Working"]
        joined = assignments_df.merge(working, on="employee_id", how="inner")
        joined["day"] = pd.to_datetime(joined["roster_date"]).dt.strftime("%d %b")
        joined["Coverage"] = joined["brand_name"] + " / " + joined["process_name"]
        counts = joined.groupby(["Coverage", "day"])["employee_id"].nunique().unstack(fill_value=0)
        all_days = pd.date_range(f"{month_key_heat}-01", periods=calendar.monthrange(selected_month_heat.year, selected_month_heat.month)[1])
        day_labels = [d.strftime("%d %b") for d in all_days]
        counts = counts.reindex(columns=day_labels, fill_value=0)
        st.caption("Interpretation: 0 = no assigned employee working; 1 = one assigned employee working; 2+ = multiple assigned employees working. These are indicators, not configurable minimum-staffing rules.")
        st.markdown("🟥 **0 staff** &nbsp;&nbsp; 🟨 **1 staff** &nbsp;&nbsp; 🟩 **2 or more staff**", unsafe_allow_html=True)
        def heat_style(value):
            if value == 0:
                return "background-color: #fee2e2; color: #991b1b; text-align: center"
            if value == 1:
                return "background-color: #fef3c7; color: #92400e; text-align: center"
            return "background-color: #dcfce7; color: #166534; text-align: center"
        st.dataframe(counts.style.applymap(heat_style), use_container_width=True, height=520)
        gap_total = int((counts == 0).sum().sum())
        single_total = int((counts == 1).sum().sum())
        a, b, c = st.columns(3)
        a.metric("Brand/process combinations", len(counts))
        b.metric("Zero-coverage dates", gap_total)
        c.metric("Single-person dates", single_total)
        if gap_total:
            st.warning("Some brand/process combinations have no assigned employee marked Working on certain dates. Review assignments, leave and weekly-off patterns.")
        else:
            st.success("Every listed brand/process combination has at least one assigned employee marked Working on every date in this generated roster.")


# ==================================================
# 18. WHAT-IF SIMULATOR
# ==================================================

elif selected_page == "What-If Simulator":
    st.header("🧪 What-If Availability Simulator")
    st.write("Temporarily remove one employee from a selected date and inspect the brand/process assignments that may be affected. This simulation does not change your saved roster.")
    employees_sim = get_employees()
    assignments_sim = get_assignments_detail()
    if employees_sim.empty:
        st.info("Add employees before using the simulator.")
    else:
        emp_lookup = {f"{r.employee_name} (ID {r.employee_id})": int(r.employee_id) for r in employees_sim.itertuples()}
        c1, c2 = st.columns(2)
        with c1:
            chosen_employee_label = st.selectbox("Employee unavailable", list(emp_lookup.keys()))
            chosen_employee_id = emp_lookup[chosen_employee_label]
        with c2:
            scenario_date = st.date_input("Date of unavailability", value=date.today(), key="scenario_date")
        employee_status = get_employee_status_for_date(chosen_employee_id, scenario_date)
        st.info(f"Current saved status for this date: **{employee_status}**. If the month has no generated roster, the simulator uses known leave, holiday and employee availability records.")
        affected = assignments_sim[assignments_sim["employee_id"] == chosen_employee_id].copy() if not assignments_sim.empty else pd.DataFrame()
        if affected.empty:
            st.warning("This employee has no brand/process assignments, so no assigned coverage can be assessed.")
        else:
            st.subheader("Potential impact")
            impact_rows = []
            for row in affected.itertuples():
                same = assignments_sim[(assignments_sim["brand_id"] == row.brand_id) & (assignments_sim["process_id"] == row.process_id)]
                others = []
                for candidate in same.itertuples():
                    if candidate.employee_id == chosen_employee_id:
                        continue
                    status = get_employee_status_for_date(int(candidate.employee_id), scenario_date)
                    if status == "Working" or status == "Not Generated":
                        others.append(candidate.employee_name)
                impact_rows.append({
                    "Brand": row.brand_name, "Process": row.process_name,
                    "Other assigned employees": ", ".join(sorted(set(others))) or "None",
                    "Coverage after removal": "Backup available" if others else "Potential coverage gap",
                    "Backup count": len(set(others))
                })
            impact_df = pd.DataFrame(impact_rows).drop_duplicates(subset=["Brand", "Process"])
            st.dataframe(impact_df, use_container_width=True, hide_index=True)
            gaps = impact_df[impact_df["Backup count"] == 0]
            if not gaps.empty:
                st.error(f"{len(gaps)} brand/process assignment(s) may have no backup if this employee becomes unavailable.")
                st.write("Suggested action: review cross-training, assign a qualified backup, or discuss a schedule change before approving the absence.")
            else:
                st.success("Other assigned employees are listed for all affected brand/process combinations. Confirm their skills and actual availability before making a change.")
            st.caption("Simulation only: no employee status, leave record or roster row has been modified.")


# ==================================================
# 19. WORKLOAD INTELLIGENCE
# ==================================================

elif selected_page == "Workload Intelligence":
    st.header("⚖️ Employee Workload Intelligence")
    st.write("Compare working days in the generated monthly roster and see how many brand/process assignments each employee owns.")
    workload_month = st.date_input("Select month", value=date.today(), key="workload_month")
    workload_key = workload_month.strftime("%Y-%m")
    conn = get_database_connection()
    work_df = pd.read_sql_query("""
        SELECT e.employee_id, e.employee_name, COALESCE(p.pod_name, 'Not Assigned') AS pod_name,
               SUM(CASE WHEN r.status = 'Working' THEN 1 ELSE 0 END) AS working_days,
               SUM(CASE WHEN r.status = 'Weekly Off' THEN 1 ELSE 0 END) AS weekly_offs,
               SUM(CASE WHEN r.status = 'Leave' THEN 1 ELSE 0 END) AS leave_days
        FROM employees e LEFT JOIN pods p ON e.pod_id = p.pod_id
        LEFT JOIN roster r ON e.employee_id = r.employee_id AND substr(r.roster_date, 1, 7) = ?
        GROUP BY e.employee_id, e.employee_name, p.pod_name
        ORDER BY working_days DESC, e.employee_name
    """, conn, params=(workload_key,))
    assign_counts = pd.read_sql_query("SELECT employee_id, COUNT(*) AS assignment_count FROM assignments GROUP BY employee_id", conn)
    conn.close()
    if work_df.empty:
        st.info("No employees found.")
    else:
        work_df = work_df.merge(assign_counts, on="employee_id", how="left")
        work_df["assignment_count"] = work_df["assignment_count"].fillna(0).astype(int)
        if int(work_df["working_days"].sum()) == 0:
            st.info("No generated roster records found for this month. Generate a roster to view workload statistics.")
        else:
            avg_days = float(work_df["working_days"].mean())
            busiest = work_df.iloc[0]
            a, b, c = st.columns(3)
            a.metric("Average working days", f"{avg_days:.1f}")
            b.metric("Highest working days", int(work_df["working_days"].max()))
            c.metric("Employees in report", len(work_df))
            st.subheader("Working days by employee")
            st.bar_chart(work_df.set_index("employee_name")[["working_days"]])
            st.subheader("Workload detail")
            st.dataframe(work_df.rename(columns={
                "employee_id": "Employee ID", "employee_name": "Employee",
                "pod_name": "Pod", "working_days": "Working Days",
                "weekly_offs": "Weekly Offs", "leave_days": "Leave Days",
                "assignment_count": "Brand/Process Assignments"
            }), use_container_width=True, hide_index=True)
            high = work_df[work_df["working_days"] > avg_days + 2]
            low = work_df[work_df["working_days"] < avg_days - 2]
            if not high.empty:
                st.warning("Higher-than-average roster workload: " + ", ".join(high["employee_name"].tolist()))
            if not low.empty:
                st.info("Lower-than-average roster workload: " + ", ".join(low["employee_name"].tolist()))
            st.caption("This is a comparison of generated Working statuses, not a measure of task difficulty, hours or productivity.")


# ==================================================
# 20. ACTIVITY HISTORY
# ==================================================

elif selected_page == "Activity History":
    st.header("🕘 Activity History")
    st.write("A simple audit trail of key actions recorded by the application.")
    conn = get_database_connection()
    history_df = pd.read_sql_query("""
        SELECT activity_time AS Time, activity_type AS Activity, activity_details AS Details
        FROM activity_history ORDER BY activity_id DESC LIMIT 250
    """, conn)
    conn.close()
    if history_df.empty:
        st.info("No activity has been recorded yet. Roster generation, leave additions and holiday additions are currently tracked.")
    else:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download activity history", history_df.to_csv(index=False).encode("utf-8"), file_name="roster_activity_history.csv", mime="text/csv")
    st.caption("The history currently records roster generation, leave additions and public-holiday additions. It is not yet a complete audit log of every edit or deletion.")


# ==================================================
# 16. FOOTER
# ==================================================

st.divider()
st.caption(
    "Smart Roster Intelligence | Workforce Scheduling & Operations Analytics"
)