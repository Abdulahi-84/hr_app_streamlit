import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64

# --- Configuration & Paths ---
# For deployment, assume images are in the same directory as the app
LOGO_FILE_NAME = "polaris_digitech_logo.png"
LOGO_PATH = LOGO_FILE_NAME # Now directly refers to the file in the same directory

# --- Define Approval Route Emails (For Simulated Notifications) ---
APPROVAL_EMAILS = {
    "Admin Manager": "abdul_bolaji@yahoo.com",
    "Finance Manager": "finance.manager@example.com",
    "HR Manager": "hr.manager@example.com",
    "Managing Director": "md@example.com"
}

# --- Beneficiaries Data ---
# Data extracted from image_210a65.png
BENEFICIARIES_DATA = {
    "Bestway Engineering Services Ltd": {"Account Name": "Benjamin", "Account No": "1234567890", "Bank": "GTB"},
    "Alpha Link Technical Services": {"Account Name": "Oladele", "Account No": "2345678900", "Bank": "Access Bank"},
    "AFLAC COM SPECs": {"Account Name": "Fasco", "Account No": "1234567890", "Bank": "Opay"},
    "Emmafem Resources Nig. Ent.": {"Account Name": "Radius", "Account No": "2345678901", "Bank": "UBA"},
    "Neptune Global Services": {"Account Name": "Folashade", "Account No": "12345678911", "Bank": "Union Bank"},
    "Other (Manually Enter Details)": {"Account Name": "", "Account No": "", "Bank": ""} # Option for manual entry
}
# Get beneficiary names for the selectbox
BENEFICIARY_NAMES = list(BENEFICIARIES_DATA.keys())

# --- Data Loading/Saving Functions ---
def load_data(filename, default_value=None):
    if default_value is None:
        default_value = []
    try:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, "r") as file:
                return json.load(file)
        return default_value
    except json.JSONDecodeError:
        st.warning(f"Error decoding JSON from {filename}. File might be corrupted or empty. Resetting data.")
        return default_value
    except FileNotFoundError:
        return default_value

def save_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def save_uploaded_file(uploaded_file, destination_folder="uploaded_documents"):
    if uploaded_file is not None:
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        
        file_path = os.path.join(destination_folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# --- Session State Initialization ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'leave_requests' not in st.session_state:
    st.session_state.leave_requests = load_data("leave_requests.json", [])
if 'opex_capex_requests' not in st.session_state:
    st.session_state.opex_capex_requests = load_data("opex_capex_requests.json", [])
if 'user_profile' not in st.session_state:
    default_profile = {
        "name": "",
        "education_background": "",
        "professional_experience": "",
        "address": "",
        "phone_number": "",
        "email_address": "",
        "department": "Admin",
        "training_attended": []
    }
    st.session_state.user_profile = load_data("user_profile.json", default_profile)
if 'performance_goals' not in st.session_state:
    st.session_state.performance_goals = load_data("performance_goals.json", [])
if 'current_page' not in st.session_state:
    st.session_state.current_page = "login"
if 'edit_goal_index' not in st.session_state:
    st.session_state.edit_goal_index = None # To track which goal is being edited

# --- Common UI Elements ---
def display_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.error(f"Company logo not found at: {LOGO_PATH}")
        st.warning(f"Please ensure '{LOGO_FILE_NAME}' is in '{ICON_BASE_DIR}'.")

# Removed display_sidebar_icon as we're using Font Awesome directly now.


# --- Login Form ---
def login_form():
    st.title("Polaris Digitech Staff Portal - Login")
    username = st.text_input("User ID", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if username == "abdul_bolaji@yahoo.com" and password == "Polaris123":
            st.session_state.logged_in = True
            st.session_state.username = "ABDULLAHI IBRAHIM" # Matches the username in the profile image
            if not st.session_state.user_profile.get("name"):
                st.session_state.user_profile["name"] = st.session_state.username
            if not st.session_state.user_profile.get("email_address"):
                st.session_state.user_profile["email_address"] = username
            save_data(st.session_state.user_profile, "user_profile.json")
            st.success("Logged in successfully!")
            st.session_state.current_page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- Dashboard Display (UI Interactive) ---
def display_dashboard():
    col_logo, col_spacer, col_user_image = st.columns([0.2, 0.6, 0.2])

    with col_logo:
        display_logo()

    st.title("POLARIS DIGITECH STAFF PORTAL - Dashboard")
    st.markdown(f"## Welcome, {st.session_state.username}")
    st.write(f"Your ID: GID/00152")
    st.write(f"Work Anniversary: September 01")

    st.markdown("---")

    with st.expander("My Profile Details (Click to expand/collapse)", expanded=True):
        with st.form("profile_edit_form_dashboard"):
            st.subheader("Personal Details")
            name = st.text_input("Full Name", value=st.session_state.user_profile.get("name", ""), key="profile_name")
            address = st.text_input("Address", value=st.session_state.user_profile.get("address", ""), key="profile_address")
            phone = st.text_input("Phone Number", value=st.session_state.user_profile.get("phone_number", ""), key="profile_phone")
            email = st.text_input("Email Address", value=st.session_state.user_profile.get("email_address", ""), disabled=True, help="Email is usually linked to login and cannot be changed here.", key="profile_email")
            
            department_options = ["Admin", "Finance", "HR", "IT", "Marketing", "Operations", "Sales", "Other"]
            current_dept = st.session_state.user_profile.get("department", "Admin")
            current_dept_index = department_options.index(current_dept) if current_dept in department_options else 0
            department = st.selectbox("Department", options=department_options, index=current_dept_index, key="profile_department")

            st.subheader("Professional Background")
            education = st.text_area("Education Background", value=st.session_state.user_profile.get("education_background", ""), height=100, key="profile_education")
            experience = st.text_area("Professional Experience", value=st.session_state.user_profile.get("professional_experience", ""), height=150, key="profile_experience")

            save_profile_button = st.form_submit_button("Save Profile Details")

            if save_profile_button:
                st.session_state.user_profile.update({
                    "name": name,
                    "education_background": education,
                    "professional_experience": experience,
                    "address": address,
                    "phone_number": phone,
                    "email_address": email,
                    "department": department
                })
                save_data(st.session_state.user_profile, "user_profile.json")
                st.success("Profile details saved successfully!")
                st.rerun()

        st.markdown("---")
        st.subheader("Training Attended")
        with st.form("new_training_form_dashboard"):
            new_training_name = st.text_input("New Training Name", key="new_training_name_input_dash")
            new_training_date = st.date_input("Training Date", key="new_training_date_input_dash", value=datetime.now())
            
            add_training_button = st.form_submit_button("Add Training Record")

            if add_training_button:
                if new_training_name:
                    training_record = {"name": new_training_name, "date": str(new_training_date)}
                    st.session_state.user_profile["training_attended"].append(training_record)
                    save_data(st.session_state.user_profile, "user_profile.json")
                    st.success(f"Added training: {new_training_name}")
                    st.rerun()
                else:
                    st.error("Training name cannot be empty.")

        current_trainings = st.session_state.user_profile.get("training_attended", [])
        if current_trainings:
            st.write("---")
            st.markdown("#### Existing Training Records:")
            training_container = st.container()
            with training_container:
                for i, training in enumerate(current_trainings):
                    col_tr1, col_tr2, col_tr3 = st.columns([0.6, 0.3, 0.1])
                    with col_tr1:
                        st.write(f"- **{training.get('name', 'N/A')}**")
                    with col_tr2:
                        st.write(f"({training.get('date', 'N/A')})")
                    with col_tr3:
                        if st.button("x", key=f"delete_training_{i}_btn_dash"):
                            st.session_state.user_profile["training_attended"].pop(i)
                            save_data(st.session_state.user_profile, "user_profile.json")
                            st.info("Training record deleted.")
                            st.rerun()
        else:
            st.info("No training records added yet.")

    st.markdown("---")

    st.subheader("Company Overview KPIs")
    
    total_employees = 150
    total_leave_requests_month = len([req for req in st.session_state.leave_requests 
                                      if datetime.strptime(req['start_date'], '%Y-%m-%d').month == datetime.now().month])
    open_goals = len([goal for goal in st.session_state.performance_goals if goal['status'] in ["Not Started", "In Progress", "On Hold"]])
    pending_opex_capex = len([req for req in st.session_state.opex_capex_requests if req['status_md'] == "Pending"])


    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        st.metric(label="Total Employees", value=total_employees)
    with col_kpi2:
        st.metric(label="Leave Requests This Month", value=total_leave_requests_month)
    with col_kpi3:
        st.metric(label="Open Goals", value=open_goals)
    with col_kpi4:
        st.metric(label="Pending Opex/Capex", value=pending_opex_capex)

    st.markdown("---")

    st.subheader("HR Data Visualizations")

    with st.expander("Filter Leave Request Data"):
        col_leave_filter1, col_leave_filter2 = st.columns(2)
        with col_leave_filter1:
            leave_start_date_filter = st.date_input("Leave Start Date (Filter)", value=datetime.now() - timedelta(days=90), key="leave_start_date_filter")
        with col_leave_filter2:
            leave_end_date_filter = st.date_input("Leave End Date (Filter)", value=datetime.now(), key="leave_end_date_filter")
        
        filtered_leave_requests = [
            req for req in st.session_state.leave_requests
            if leave_start_date_filter <= datetime.strptime(req['start_date'], '%Y-%m-%d').date() <= leave_end_date_filter
        ]
    
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### Leave Type Distribution")
        if filtered_leave_requests:
            df_leave = pd.DataFrame(filtered_leave_requests)
            leave_counts = df_leave['leave_type'].value_counts().reset_index()
            leave_counts.columns = ['Leave Type', 'Count']
            fig_pie = px.pie(leave_counts, values='Count', names='Leave Type', 
                             title='Breakdown of Leave Requests by Type (Filtered)',
                             hole=0.3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No leave requests to display chart for the selected period.")

    with col_chart2:
        st.markdown("#### Performance Goal Status")
        goal_status_filter = st.multiselect(
            "Filter Goal Status",
            options=["Not Started", "In Progress", "On Hold", "Complete"],
            default=["Not Started", "In Progress", "On Hold", "Complete"],
            key="goal_status_multiselect"
        )
        
        filtered_performance_goals = [
            goal for goal in st.session_state.performance_goals
            if goal['status'] in goal_status_filter
        ]

        if filtered_performance_goals:
            df_goals = pd.DataFrame(filtered_performance_goals)
            goal_status_counts = df_goals['status'].value_counts().reset_index()
            goal_status_counts.columns = ['Status', 'Count']
            fig_bar = px.bar(goal_status_counts, x='Status', y='Count', 
                             title='Current Performance Goal Status (Filtered)',
                             color='Status',
                             color_discrete_map={
                                 "Not Started": "lightgray",
                                 "In Progress": "skyblue",
                                 "On Hold": "orange",
                                 "Complete": "lightgreen"
                             })
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No performance goals to display chart for the selected status.")

    st.markdown("---")

    st.subheader("Leave Information")
    col_leave1, col_leave2 = st.columns(2)

    with col_leave1:
        st.markdown("### Available Leave Days")
        st.metric(label="Exam Leave", value="20 of 20 day(s)")
        st.metric(label="Compassionate Leave", value="3 of 3 day(s)")
        st.metric(label="Annual Leave", value="3 of 3 day(s)")
        st.metric(label="Annual Leave (Testing)", value="2 of 6 day(s)")
        st.link_button("View all", url="#")

    with col_leave2:
        st.markdown("### View Employee(s) on Leave in your Department")
        st.info("No employee is on leave today / this month")

    st.markdown("---")

    st.subheader("Quick Actions")
    col_quick_actions = st.columns(3)
    with col_quick_actions[0]:
        if st.button("Apply for Leave", key="apply_leave_dashboard_bottom"):
            st.session_state.current_page = "leave_request"
            st.rerun()
    with col_quick_actions[1]:
        if st.button("Submit Opex/Capex", key="submit_opex_dashboard_bottom"):
            st.session_state.current_page = "opex_capex_form"
            st.rerun()
    with col_quick_actions[2]:
        if st.button("Set Goals", key="set_goals_dashboard_bottom"):
            st.session_state.current_page = "performance_goal_setting"
            st.rerun()

    st.markdown("---")

    st.subheader("Recent Announcements")
    st.write("No recent announcements.")

    st.subheader("Employee Directory")
    employee_data = [
        {"ID": "GID/00152", "Name": "ABDULLAHI IBRAHIM", "Department": st.session_state.user_profile.get('department', 'N/A'), "Role": "HR Assistant"},
        {"ID": "GID/00153", "Name": "Alice Smith", "Department": "Finance", "Role": "Accountant"},
        {"ID": "GID/00154", "Name": "Bob Johnson", "Department": "IT", "Role": "Software Engineer"},
        {"ID": "GID/00155", "Name": "Carol White", "Department": "Marketing", "Role": "Marketing Specialist"},
    ]
    df_employees = pd.DataFrame(employee_data)

    employee_search_query = st.text_input("Search Employee by Name or Department", key="employee_search_bar")
    
    if employee_search_query:
        df_employees_filtered = df_employees[
            df_employees.apply(lambda row: employee_search_query.lower() in str(row).lower(), axis=1)
        ]
        if not df_employees_filtered.empty:
            st.dataframe(df_employees_filtered, use_container_width=True)
        else:
            st.info("No employees match your search query.")
    else:
        st.dataframe(df_employees, use_container_width=True)

# --- PDF Generation Function for Leave Requests ---
def generate_leave_pdf(leave_request_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Polaris Digitech - Leave Application", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Phone: {user_profile.get('phone_number', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Leave Request Details:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    for key, value in leave_request_data.items():
        if key in ["start_date", "end_date", "submission_date"] and value:
            try:
                value = datetime.strptime(value, '%Y-%m-%d').strftime('%B %d, %Y')
            except ValueError:
                pass
        
        display_key = key.replace('_', ' ').title()
        
        pdf.cell(0, 7, f"{display_key}: {value}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    return bytes(pdf.output(dest='S'))

def generate_opex_capex_pdf(request_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Polaris Digitech - {request_data.get('requisition_type', 'N/A')} Requisition", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Phone: {user_profile.get('phone_number', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Requisition Details:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Exclude certain keys that are handled separately or not needed in the main list
    exclude_keys = [
        "status_admin", "status_finance", "status_hr", "status_md", 
        "uploaded_document_path", "amount_requested" # 'amount_requested' is now derived from segments
    ]
    
    # Manually add the itemized costs first for clarity
    pdf.cell(0, 7, f"Title: {request_data.get('title', 'N/A')}", ln=True)
    pdf.multi_cell(0, 7, f"Details: {request_data.get('details', 'N/A')}")
    pdf.cell(0, 7, f"Beneficiary: {request_data.get('beneficiaries', 'N/A')}", ln=True)
    
    pdf.ln(2)
    pdf.set_font("Arial", 'BU', 10) # Underlined and Bold
    pdf.cell(0, 7, "Cost Breakdown:", ln=True)
    pdf.set_font("Arial", '', 10) # Back to normal font
    pdf.cell(0, 7, f"Materials Cost: {request_data.get('materials_cost', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Labour/Services Cost: {request_data.get('labour_cost', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Withholding Tax (%): {request_data.get('wht_percentage', 'None')}", ln=True)
    pdf.cell(0, 7, f"Withholding Tax Amount: {request_data.get('wht_amount', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Net Labour/Services Cost: {request_data.get('net_labour_cost', 0.0):,.2f} NGN", ln=True)
    pdf.set_font("Arial", 'B', 10) # Bold for total
    pdf.cell(0, 7, f"Total Net Amount Requested: {request_data.get('net_amount_requested', 0.0):,.2f} NGN", ln=True)
    pdf.set_font("Arial", '', 10) # Back to normal font
    
    pdf.cell(0, 7, f"Amount Budgeted: {request_data.get('amount_budgeted', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Budget Balance: {request_data.get('budget_balance', 0.0):,.2f} NGN", ln=True)
    pdf.ln(2) # Little space

    pdf.set_font("Arial", 'BU', 10) # Underlined and Bold
    pdf.cell(0, 7, "Account Details:", ln=True)
    pdf.set_font("Arial", '', 10) # Back to normal font
    pdf.cell(0, 7, f"Account Name: {request_data.get('account_name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Account No: {request_data.get('account_no', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Bank: {request_data.get('bank', 'N/A')}", ln=True)
    pdf.ln(2)

    # Any other keys not handled above
    for key, value in request_data.items():
        if key not in exclude_keys and key not in [
            "materials_cost", "labour_cost", "wht_percentage", 
            "wht_amount", "net_labour_cost", "net_amount_requested", 
            "amount_budgeted", "budget_balance", "title", "details", 
            "beneficiaries", "account_name", "account_no", "bank", "requisition_type"
        ]: # Ensure we don't duplicate already printed fields
            if key == "submitted_date" and value:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d').strftime('%B %d, %Y')
                except ValueError:
                    pass
            
            display_key = key.replace('_', ' ').title()
            pdf.cell(0, 7, f"{display_key}: {value}", ln=True)

    uploaded_doc_path = request_data.get("uploaded_document_path")
    if uploaded_doc_path and os.path.exists(uploaded_doc_path):
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Attached Document:", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"- {os.path.basename(uploaded_doc_path)}", ln=True)
    else:
        pdf.cell(0, 7, "No document attached.", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Approval Status:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Admin Manager: {request_data.get('status_admin', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"Finance Manager: {request_data.get('status_finance', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"HR Manager: {request_data.get('status_hr', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"Managing Director: {request_data.get('status_md', 'Pending')}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    return bytes(pdf.output(dest='S'))

def generate_appraisal_pdf(appraisal_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Polaris Digitech - Performance Appraisal", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Appraisal Period: " + appraisal_data.get('appraisal_period', 'N/A'), ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Performance Goals:", ln=True)
    pdf.ln(2)

    total_weighted_self_score = 0
    total_weighted_supervisor_score = 0
    total_weight = 0

    for i, goal in enumerate(appraisal_data.get('goals', [])):
        pdf.set_font("Arial", 'B', 10)
        # Use multi_cell for goal description as it can be long
        pdf.multi_cell(0, 7, f"Goal {i+1}: {goal.get('s_n_goals', 'N/A')}") 
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 7, f"  Weight: {goal.get('weight_self_rating', 0)}%", ln=True)
        pdf.cell(0, 7, f"  Self-Appraisal Score (0-5): {goal.get('self_appraisal_score', 'N/A')}", ln=True)
        # Use multi_cell for employee remark as it can be multi-line
        pdf.multi_cell(0, 7, f"  Employee Remark: {goal.get('employee_remark', 'N/A')}")
        
        # Changed from multi_cell to cell for these lines. Removed leading spaces in f-string to give more space.
        pdf.cell(0, 7, f"Supervisor's Score (0-5): {goal.get('line_managers_rating', 'N/A')}", ln=True) 
        pdf.multi_cell(0, 7, f"Supervisor's Comment: {goal.get('supervisor_comment', 'N/A')}") # Supervisor comment can be long

        pdf.ln(2)

        # Calculate weighted scores (assuming scores are 0-5 and need scaling for percentage)
        weight = goal.get('weight_self_rating', 0)
        self_score = goal.get('self_appraisal_score', 0)
        supervisor_score = goal.get('line_managers_rating', 0) # Use 0 if not present for calculation

        # Scale 0-5 score to 0-100 for weighted calculation if desired, or keep as is
        # For overall score, let's keep 0-5 scale and calculate directly
        total_weighted_self_score += (weight / 100) * self_score
        total_weighted_supervisor_score += (weight / 100) * supervisor_score
        total_weight += weight

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Summary Scores:", ln=True)
    pdf.set_font("Arial", '', 10)

    if total_weight > 0:
        overall_self_score_scaled = (total_weighted_self_score / total_weight) * 100 if total_weight > 0 else 0
        overall_supervisor_score_scaled = (total_weighted_supervisor_score / total_weight) * 100 if total_weight > 0 else 0

        # Calculate overall 0-5 score for the PDF summary
        overall_self_score_0_5 = (overall_self_score_scaled / 100) * 5
        overall_supervisor_score_0_5 = (overall_supervisor_score_scaled / 100) * 5

        pdf.cell(0, 7, f"Overall Self-Appraisal Score (0-5): {overall_self_score_0_5:,.2f}", ln=True)
        pdf.cell(0, 7, f"Overall Supervisor's Score (0-5): {overall_supervisor_score_0_5:,.2f}", ln=True)
    else:
        pdf.cell(0, 7, "No weighted goals to calculate overall scores.", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Overall Supervisor's Comment:", ln=True) # New
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, appraisal_data.get('overall_supervisor_comment', 'N/A')) # New

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Recommendation:", ln=True) # New
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, appraisal_data.get('recommendation', 'N/A')) # New


    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    return bytes(pdf.output(dest='S'))


# --- Leave Request Form ---
def leave_request_form():
    st.title("Leave Request Form")

    with st.form("leave_form"):
        title = st.text_input("Request Title")
        details = st.text_area("Details", help="You can use Markdown for **bold**, *italics*, `code`, and basic tables.\n\nExample table:\n```\n| Header 1 | Header 2 |\n|----------|----------|\n| Item 1   | Value 1  |\n```")
        entitled_leave = st.number_input("Annual Leave Days Entitled", min_value=0, value=20)
        reliever = st.text_input("Name of Reliever Officer")
        leave_type = st.selectbox("Leave Type", ["Annual Leave", "Casual Leave", "Exam Leave", "Maternity Leave", "Bereavement Leave", "Sick Leave"])
        start_date = st.date_input("Start Date", datetime.now())
        end_date = st.date_input("End Date", datetime.now() + timedelta(days=7))

        submitted = st.form_submit_button("Calculate and Submit Leave Request")

        if submitted:
            if not all([title, details, reliever, leave_type, start_date, end_date]):
                st.error("All fields must be filled out.")
            else:
                leave_days_taken = (end_date - start_date).days + 1
                leave_remaining = entitled_leave - leave_days_taken

                if leave_remaining < 0:
                    st.warning(f"You are requesting {leave_days_taken} days, but only have {entitled_leave} days entitled. This would result in {abs(leave_remaining)} days negative leave.")

                leave_request = {
                    "title": title,
                    "details": details,
                    "entitled_leave": entitled_leave,
                    "reliever": reliever,
                    "leave_type": leave_type,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "leave_taken": leave_days_taken,
                    "leave_remaining": leave_remaining,
                    "submission_date": str(datetime.now().date())
                }
                st.session_state.leave_requests.append(leave_request)
                save_data(st.session_state.leave_requests, "leave_requests.json")
                st.success("Your leave request has been submitted for approval.")
                st.session_state.current_page = "view_leave_applications"
                st.rerun()

    if st.button("Back to Dashboard", key="back_from_leave_form"):
        st.session_state.current_page = "dashboard"
        st.rerun()

# --- View Leave Applications Page ---
def view_leave_applications():
    st.title("My Leave Applications")

    if not st.session_state.leave_requests:
        st.info("You have not submitted any leave applications yet.")
        if st.button("Apply for Leave Now"):
            st.session_state.current_page = "leave_request"
            st.rerun()
    else:
        st.write("Here are your submitted leave applications:")
        
        for i, lr in enumerate(st.session_state.leave_requests):
            st.markdown(f"### Application {i+1}: {lr.get('title', 'Leave Request')}")
            st.write(f"**Type:** {lr.get('leave_type', 'N/A')}")
            st.write(f"**Period:** {lr.get('start_date', 'N/A')} to {lr.get('end_date', 'N/A')} ({lr.get('leave_taken', 'N/A')} days)")
            st.write(f"**Reliever:** {lr.get('reliever', 'N/A')}")
            st.markdown(f"**Details:**")
            st.markdown(lr.get('details', 'N/A'))
            st.write(f"**Submitted On:** {lr.get('submission_date', 'N/A')}")

            pdf_bytes = generate_leave_pdf(lr, st.session_state.user_profile)
            st.download_button(
                label=f"Download Application {i+1} as PDF",
                data=pdf_bytes,
                file_name=f"Leave_Application_{i+1}_{lr.get('start_date', 'N/A')}.pdf",
                mime="application/pdf",
                key=f"download_leave_pdf_{i}"
            )
            st.markdown("---")
    
    if st.button("Back to Dashboard", key="back_from_view_applications"):
        st.session_state.current_page = "dashboard"
        st.rerun()

# --- Opex/Capex Request Form ---
def opex_capex_form():
    st.title("Opex/Capex Requisition Form")

    with st.form("opex_capex_form"):
        st.subheader("Requisition Details")
        requisition_type = st.radio("Requisition Type", ["Opex", "Capex"], horizontal=True, key="opex_capex_type")
        title = st.text_input("Title", help="Brief summary of the request.")
        details = st.text_area("Details", help="Kindly approve a sum of =N= 50,000 being payment to fix the faulty door in HR office.\n\nYou can use Markdown for **bold**, *italics*, `code`, and basic tables.\n\nExample table:\n```\n| Item | Cost |\n|------|------|\n| Repair | 50000 |\n```")
        
        selected_beneficiary = st.selectbox(
            "Beneficiaries",
            options=BENEFICIARY_NAMES,
            key="beneficiary_select",
            help="Select a vendor from the list or choose 'Other' to manually enter details."
        )

        st.subheader("Financial Details")
        col_budget1, col_budget2 = st.columns(2)
        with col_budget1:
            amount_budgeted = st.number_input("Amount Budgeted (NGN)", min_value=0.0, format="%.2f", key="amount_budgeted_input_new")
        with col_budget2:
            st.write(" ") # Placeholder for alignment

        st.markdown("---")
        st.subheader("Amount Requested Breakdown")

        materials_cost = st.number_input("1. Materials Cost (NGN)", min_value=0.0, value=0.0, format="%.2f", key="materials_cost_input")
        labour_cost = st.number_input("2. Labour Cost/Services Charge/Professional Fee (NGN)", min_value=0.0, value=0.0, format="%.2f", key="labour_cost_input")
        
        wht_percentage_str = st.selectbox(
            "3. Withholding Tax (WHT) Option",
            options=["None", "5%", "10%", "15%"],
            key="wht_option_select",
            help="WHT is applied only to Labour Cost/Services Charge/Professional Fee."
        )

        wht_percentage = 0.0
        if wht_percentage_str != "None":
            wht_percentage = float(wht_percentage_str.replace('%', '')) / 100

        wht_amount = labour_cost * wht_percentage
        net_labour_cost = labour_cost - wht_amount
        net_amount_requested = materials_cost + net_labour_cost

        st.markdown(f"**Withholding Tax Amount:** {wht_amount:,.2f} NGN")
        st.markdown(f"**Net Labour/Services Cost:** {net_labour_cost:,.2f} NGN")
        st.markdown(f"**Net Amount Requested (Materials + Net Labour):** {net_amount_requested:,.2f} NGN")

        # Display Budget Balance based on the new Net Amount Requested
        budget_balance = amount_budgeted - net_amount_requested
        st.text_input("Budget Balance (NGN)", value=f"{budget_balance:,.2f}", disabled=True, help="Amount Budgeted - Net Amount Requested", key="budget_balance_display_new")

        st.subheader("Account Details")
        col_acc1, col_acc2, col_acc3 = st.columns(3)
        
        is_disabled = (selected_beneficiary != "Other (Manually Enter Details)")
        
        default_account_name = BENEFICIARIES_DATA[selected_beneficiary]["Account Name"]
        default_account_no = BENEFICIARIES_DATA[selected_beneficiary]["Account No"]
        default_bank = BENEFICIARIES_DATA[selected_beneficiary]["Bank"]

        with col_acc1:
            account_name = st.text_input("Account Name", value=default_account_name, disabled=is_disabled, key="account_name_input_new")
        with col_acc2:
            account_no = st.text_input("Account No", value=default_account_no, disabled=is_disabled, key="account_no_input_new")
        with col_acc3:
            bank = st.text_input("Bank", value=default_bank, disabled=is_disabled, key="bank_input_new")
        
        st.subheader("Attachments")
        uploaded_file = st.file_uploader("Upload supporting document (PDF, Image, etc.)", type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx"], key="opex_capex_file_uploader_new")
        
        uploaded_document_path = None
        if uploaded_file:
            st.info(f"File uploaded: {uploaded_file.name}")

        st.subheader("Approval Status (Read-only on submission)")
        st.info("Approval fields will be managed by managers after submission and are not editable here.")
        st.text_input("Admin Manager", value="Pending", disabled=True, key="admin_approval_status_new")
        st.text_input("Finance Manager", value="Pending", disabled=True, key="finance_approval_status_new")
        st.text_input("HR Manager", value="Pending", disabled=True, key="hr_approval_status_new")
        st.text_input("Managing Director", value="Pending", disabled=True, key="md_approval_status_new")

        submitted = st.form_submit_button("Submit Opex/Capex Request")

        if submitted:
            # Validate input fields
            if not all([title, details, selected_beneficiary, account_name, account_no, bank, amount_budgeted is not None, 
                        materials_cost is not None, labour_cost is not None]):
                st.error("Please fill in all required fields (Title, Details, Beneficiaries, Account Name, Account No, Bank, Amount Budgeted, Materials Cost, Labour Cost).")
            else:
                if uploaded_file:
                    uploaded_document_path = save_uploaded_file(uploaded_file, "uploaded_documents")
                
                opex_capex_request = {
                    "requisition_type": requisition_type,
                    "title": title,
                    "details": details,
                    "beneficiaries": selected_beneficiary,
                    "materials_cost": materials_cost,
                    "labour_cost": labour_cost,
                    "wht_percentage": wht_percentage_str,
                    "wht_amount": wht_amount,
                    "net_labour_cost": net_labour_cost,
                    "net_amount_requested": net_amount_requested,
                    "amount_budgeted": amount_budgeted,
                    "budget_balance": budget_balance,
                    "account_name": account_name,
                    "account_no": account_no,
                    "bank": bank,
                    "uploaded_document_path": uploaded_document_path,
                    "status_admin": "Pending",
                    "status_finance": "Pending",
                    "status_hr": "Pending",
                    "status_md": "Pending",
                    "submitted_date": str(datetime.now().date())
                }
                st.session_state.opex_capex_requests.append(opex_capex_request)
                save_data(st.session_state.opex_capex_requests, "opex_capex_requests.json")
                
                st.success("Opex/Capex request submitted successfully!")
                
                # --- Simulated Email Notification ---
                st.info("Simulating Email Notifications:")
                request_summary = f"A new {requisition_type} request titled '{title}' for {net_amount_requested:,.2f} NGN has been submitted by {st.session_state.username} ({st.session_state.user_profile.get('department', 'N/A')})."
                
                st.write(f"Email would be sent to Admin Manager ({APPROVAL_EMAILS['Admin Manager']}): {request_summary}")
                st.write(f"Email would be sent to Finance Manager ({APPROVAL_EMAILS['Finance Manager']}): {request_summary}")
                st.write(f"Email would be sent to HR Manager ({APPROVAL_EMAILS['HR Manager']}): {request_summary}")
                st.write(f"Email would be sent to Managing Director ({APPROVAL_EMAILS['Managing Director']}): {request_summary}")
                # --- End Simulated Email Notification ---

                st.session_state.current_page = "view_opex_capex_applications"
                st.rerun()

    if st.button("Back to Dashboard", key="back_from_opex_capex_form"):
        st.session_state.current_page = "dashboard"
        st.rerun()

# --- View Opex/Capex Applications Page ---
def view_opex_capex_applications():
    st.title("My Opex/Capex Requisitions")

    if not st.session_state.opex_capex_requests:
        st.info("You have not submitted any Opex/Capex requisitions yet.")
        if st.button("Submit Opex/Capex Now"):
            st.session_state.current_page = "opex_capex_form"
            st.rerun()
    else:
        st.write("Here are your submitted Opex/Capex requisitions:")
        
        for i, oc_req in enumerate(st.session_state.opex_capex_requests):
            st.markdown(f"### Requisition {i+1}: {oc_req.get('title', 'Opex/Capex Request')}")
            st.write(f"**Type:** {oc_req.get('requisition_type', 'N/A')}")
            st.write(f"**Beneficiary:** {oc_req.get('beneficiaries', 'N/A')}")
            st.write(f"**Account Name:** {oc_req.get('account_name', 'N/A')}")
            st.write(f"**Account No:** {oc_req.get('account_no', 'N/A')}")
            st.write(f"**Bank:** {oc_req.get('bank', 'N/A')}")
            
            st.markdown("#### Cost Breakdown:")
            st.write(f"- Materials Cost: {oc_req.get('materials_cost', 0.0):,.2f} NGN")
            st.write(f"- Labour Cost/Services Charge/Professional Fee: {oc_req.get('labour_cost', 0.0):,.2f} NGN")
            st.write(f"- Withholding Tax ({oc_req.get('wht_percentage', 'None')}): {oc_req.get('wht_amount', 0.0):,.2f} NGN")
            st.write(f"- Net Labour/Services Cost: {oc_req.get('net_labour_cost', 0.0):,.2f} NGN")
            st.write(f"**Total Net Amount Requested:** {oc_req.get('net_amount_requested', 0.0):,.2f} NGN")
            
            st.write(f"**Amount Budgeted:** {oc_req.get('amount_budgeted', 0.0):,.2f} NGN")
            st.write(f"**Budget Balance:** {oc_req.get('budget_balance', 0.0):,.2f} NGN")
            
            st.markdown(f"**Details:**")
            st.markdown(oc_req.get('details', 'N/A'))
            st.write(f"**Submitted On:** {oc_req.get('submitted_date', 'N/A')}")
            
            uploaded_doc_path = oc_req.get("uploaded_document_path")
            if uploaded_doc_path and os.path.exists(uploaded_doc_path):
                with open(uploaded_doc_path, "rb") as file:
                    st.download_button(
                        label=f"Download Attached Document: {os.path.basename(uploaded_doc_path)}",
                        data=file,
                        file_name=os.path.basename(uploaded_doc_path),
                        mime="application/octet-stream",
                        key=f"download_attachment_{i}"
                    )
            else:
                st.info("No supporting document attached.")

            st.markdown("**Approval Status:**")
            st.write(f"- Admin: {oc_req.get('status_admin', 'Pending')}")
            st.write(f"- Finance: {oc_req.get('status_finance', 'Pending')}")
            st.write(f"- HR: {oc_req.get('status_hr', 'Pending')}")
            st.write(f"- MD: {oc_req.get('status_md', 'Pending')}")

            pdf_bytes = generate_opex_capex_pdf(oc_req, st.session_state.user_profile)
            st.download_button(
                label=f"Download Requisition {i+1} as PDF",
                data=pdf_bytes,
                file_name=f"Opex_Capex_Requisition_{i+1}_{oc_req.get('submitted_date', 'N/A')}.pdf",
                mime="application/pdf",
                key=f"download_opex_capex_pdf_{i}"
            )
            st.markdown("---")
            
    if st.button("Back to Dashboard", key="back_from_view_opex_capex_applications"):
        st.session_state.current_page = "dashboard"
        st.rerun()


# --- Performance - Goal Setting ---
def performance_goal_setting():
    st.title("Performance - KPI Goal Setting")
    st.write("This section allows you to set, edit, and delete your performance objectives and assign weights to each.")

    st.subheader("Current Goals")
    if st.session_state.performance_goals:
        # Display goals with Edit/Delete options
        for i, goal in enumerate(st.session_state.performance_goals):
            st.markdown(f"---")
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            with col1:
                st.markdown(f"**Goal {i+1}:** {goal.get('s_n_goals', 'N/A')}")
                st.write(f"**Weight:** {goal.get('weight_self_rating', 0)}%")
                st.write(f"**Status:** {goal.get('status', 'N/A')}")
                st.write(f"**Collaborating Department:** {goal.get('collaborating_department', 'N/A')}")
                st.write(f"**Period:** {goal.get('start_date', 'N/A')} to {goal.get('end_date', 'N/A')} ({goal.get('duration', 'N/A')})")
                st.write(f"**Employee Remark:** {goal.get('employee_remark', 'N/A')}")
            with col2:
                if st.button("Edit", key=f"edit_goal_{i}"):
                    st.session_state.edit_goal_index = i
                    st.rerun()
            with col3:
                if st.button("Delete", key=f"delete_goal_{i}"):
                    st.session_state.performance_goals.pop(i)
                    save_data(st.session_state.performance_goals, "performance_goals.json")
                    st.success("Goal deleted successfully!")
                    st.session_state.edit_goal_index = None # Reset edit state
                    st.rerun()
    else:
        st.info("No performance goals set yet. Use the form below to add new goals.")

    st.markdown("---")
    
    # Add/Edit Goal Form
    current_goal = {}
    form_title = "Add New Goal"
    if st.session_state.edit_goal_index is not None:
        form_title = "Edit Existing Goal"
        current_goal = st.session_state.performance_goals[st.session_state.edit_goal_index]

    st.subheader(form_title)
    with st.form("goal_form", clear_on_submit=True):
        s_n_goals = st.text_area("KPI / Goal Description", value=current_goal.get('s_n_goals', ''), height=100, key="goal_description_input")
        collaborating_department = st.text_input("Collaborating Department", value=current_goal.get('collaborating_department', ''), key="goal_collab_dept_input")
        status_options = ["Not Started", "In Progress", "On Hold", "Complete"]
        status = st.selectbox("Status", status_options, index=status_options.index(current_goal.get('status', 'Not Started')), key="goal_status_select")
        employee_remark = st.text_area("Employee Remark/Update", value=current_goal.get('employee_remark', ''), help="Your notes on progress or challenges.", key="goal_employee_remark_input")
        
        col_dates = st.columns(2)
        with col_dates[0]:
            # Convert string date back to datetime.date object for date_input
            default_start_date = datetime.strptime(current_goal['start_date'], '%Y-%m-%d').date() if 'start_date' in current_goal else datetime.now().date()
            start_date = st.date_input("Start Date", value=default_start_date, key="goal_start_date_input_form")
        with col_dates[1]:
            default_end_date = datetime.strptime(current_goal['end_date'], '%Y-%m-%d').date() if 'end_date' in current_goal else datetime.now().date() + timedelta(days=90)
            end_date = st.date_input("End Date", value=default_end_date, key="goal_end_date_input_form")
        
        duration_days = (end_date - start_date).days
        if duration_days > 0:
            duration_text = f"{duration_days} day(s)"
            if duration_days >= 30:
                duration_text = f"{duration_days // 30} month(s) approx."
        else:
            duration_text = "0 day(s)"
        st.text_input("Calculated Duration", value=duration_text, disabled=True, key="goal_duration_display_form")

        # Weight input and validation
        current_total_weight = sum(g['weight_self_rating'] for g in st.session_state.performance_goals if g != current_goal)
        initial_weight = current_goal.get('weight_self_rating', 0)
        
        weight = st.slider("Weight (0-100%)", min_value=0, max_value=100, value=initial_weight, step=1, help="The importance of this goal relative to others (total should not exceed 100%).", key="goal_weight_slider_form")
        
        # Display current total weight
        st.info(f"Current sum of weights (excluding this goal): {current_total_weight}%")

        submit_button_label = "Add Goal" if st.session_state.edit_goal_index is None else "Update Goal"
        submitted = st.form_submit_button(submit_button_label)

        if submitted:
            if not s_n_goals:
                st.error("Goal description is required.")
            elif current_total_weight + weight > 100 and st.session_state.edit_goal_index is None:
                st.error(f"Total weight for all goals cannot exceed 100%. Current total with new goal: {current_total_weight + weight}%.")
            elif current_total_weight + weight > 100 and st.session_state.edit_goal_index is not None:
                # If editing, ensure the new weight doesn't make total > 100 (excluding old value of this goal)
                temp_goals = st.session_state.performance_goals[:]
                temp_goals[st.session_state.edit_goal_index]['weight_self_rating'] = weight
                if sum(g['weight_self_rating'] for g in temp_goals) > 100:
                     st.error(f"Total weight for all goals cannot exceed 100%. Current total: {sum(g['weight_self_rating'] for g in temp_goals)}%.")
                else:
                    new_goal_data = {
                        "s_n_goals": s_n_goals,
                        "collaborating_department": collaborating_department,
                        "status": status,
                        "employee_remark": employee_remark,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "duration": duration_text,
                        "weight_self_rating": weight,
                        "self_appraisal_score": current_goal.get('self_appraisal_score', 0),
                        "line_managers_rating": current_goal.get('line_managers_rating', 0),
                        "supervisor_comment": current_goal.get('supervisor_comment', '') # Keep existing supervisor comment
                    }
                    st.session_state.performance_goals[st.session_state.edit_goal_index] = new_goal_data
                    save_data(st.session_state.performance_goals, "performance_goals.json")
                    st.success("Goal updated successfully!")
                    st.session_state.edit_goal_index = None # Reset edit state
                    st.rerun()
            else:
                new_goal_data = {
                    "s_n_goals": s_n_goals,
                    "collaborating_department": collaborating_department,
                    "status": status,
                    "employee_remark": employee_remark,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "duration": duration_text,
                    "weight_self_rating": weight,
                    "self_appraisal_score": 0, # Initialized for appraisal (0-5 scale)
                    "line_managers_rating": 0, # Initialized for appraisal (0-5 scale)
                    "supervisor_comment": "" # Initialized for supervisor comment
                }
                if st.session_state.edit_goal_index is None:
                    st.session_state.performance_goals.append(new_goal_data)
                    st.success("New goal added successfully!")
                else:
                    st.session_state.performance_goals[st.session_state.edit_goal_index] = new_goal_data
                    st.success("Goal updated successfully!")
                
                save_data(st.session_state.performance_goals, "performance_goals.json")
                st.session_state.edit_goal_index = None # Reset edit state
                st.rerun()

    if st.session_state.edit_goal_index is not None:
        if st.button("Cancel Edit", key="cancel_edit_goal"):
            st.session_state.edit_goal_index = None
            st.rerun()

    if st.button("Back to Dashboard", key="back_from_goals"):
        st.session_state.current_page = "dashboard"
        st.session_state.edit_goal_index = None # Ensure edit state is reset
        st.rerun()


# --- Performance Appraisal ---
def performance_appraisal():
    st.title("Performance Appraisal")
    st.write("Review your performance goals and provide your self-appraisal score.")

    if not st.session_state.performance_goals:
        st.info("No performance goals have been set. Please set goals first in the 'KPI Goal Setting' section.")
        if st.button("Go to KPI Goal Setting"):
            st.session_state.current_page = "performance_goal_setting"
            st.rerun()
        return

    st.subheader("Your Performance Goals for Appraisal")

    # Appraisal Period (can be dynamic, for now fixed for demonstration)
    appraisal_period = st.text_input("Appraisal Period", value=f"Q2 {datetime.now().year}", help="Specify the period this appraisal covers.", key="appraisal_period_input")

    updated_goals = []
    total_weighted_self_score = 0 # sum of (weight * self_score)
    total_weighted_supervisor_score = 0 # sum of (weight * supervisor_score)
    total_weight = 0

    with st.form("appraisal_form"):
        for i, goal in enumerate(st.session_state.performance_goals):
            st.markdown(f"---")
            st.markdown(f"**Goal {i+1}:** {goal.get('s_n_goals', 'N/A')}")
            st.write(f"**Weight:** {goal.get('weight_self_rating', 0)}%")
            st.write(f"**Status:** {goal.get('status', 'N/A')}")
            st.write(f"**Duration:** {goal.get('duration', 'N/A')}")
            st.markdown(f"**Employee Remark:** {goal.get('employee_remark', 'N/A')}")

            # Self-Appraisal Score Input (Editable by Employee, 0-5 scale)
            self_score = st.slider(
                f"Self-Appraisal Score for Goal {i+1} (0-5)",
                min_value=0.0, max_value=5.0,
                value=float(goal.get('self_appraisal_score', 0)), # Cast to float for slider
                step=0.5,
                key=f"self_appraisal_score_{i}"
            )

            # Supervisor's Score (Read-Only, 0-5 scale)
            supervisor_score = st.number_input(
                f"Supervisor's Score for Goal {i+1} (0-5)",
                min_value=0.0, max_value=5.0,
                value=float(goal.get('line_managers_rating', 0)), # Cast to float for number_input
                step=0.5,
                disabled=True, # Supervisor's score is not editable by employee
                key=f"supervisor_score_{i}"
            )
            
            # Supervisor's Comment on each goal (Read-Only)
            st.text_area(
                f"Supervisor's Comment on Goal {i+1}",
                value=goal.get('supervisor_comment', 'No comment yet from supervisor.'),
                height=70,
                disabled=True,
                key=f"supervisor_comment_{i}"
            )
            
            # Update the goal with new self-appraisal score
            goal['self_appraisal_score'] = self_score
            updated_goals.append(goal)

            # Accumulate scores for overall calculation
            weight = goal.get('weight_self_rating', 0)
            total_weighted_self_score += (weight / 100) * self_score
            total_weighted_supervisor_score += (weight / 100) * supervisor_score
            total_weight += weight # Sum of weights for normalization


        st.markdown("---")
        st.subheader("Overall Appraisal Summary")
        
        overall_self_score = 0
        overall_supervisor_score = 0

        # Ensure total_weight is not zero to avoid division by zero errors
        if total_weight > 0:
            overall_self_score = total_weighted_self_score / (total_weight / 100)
            overall_supervisor_score = total_weighted_supervisor_score / (total_weight / 100)
            
            st.metric("Overall Self-Appraisal Score (0-5)", f"{overall_self_score:,.2f}")
            st.metric("Overall Supervisor's Score (0-5)", f"{overall_supervisor_score:,.2f}") # This will be 0 if no supervisor input
        else:
            st.info("Set weights for your goals to see overall scores.")

        # Overall Supervisor's Comment (Read-only)
        overall_supervisor_comment_from_file = load_data("current_appraisal.json", {}).get("overall_supervisor_comment", "No overall comment yet from supervisor.")
        st.text_area(
            "Overall Supervisor's Comment",
            value=overall_supervisor_comment_from_file,
            height=100,
            disabled=True,
            key="overall_supervisor_comment_display"
        )

        # Overall Appraisal Rating (Based on Supervisor's Score)
        st.markdown("#### Overall Appraisal Rating")
        appraisal_rating = "N/A"
        if overall_supervisor_score >= 4.5:
            appraisal_rating = "Outstanding (5)"
        elif overall_supervisor_score >= 3.5:
            appraisal_rating = "Exceed Expectation (4)"
        elif overall_supervisor_score >= 2.5:
            appraisal_rating = "Meet Expectation (3)"
        elif overall_supervisor_score >= 1.5:
            appraisal_rating = "Needs Improvement (2)"
        elif overall_supervisor_score > 0: # Anything above 0 but less than 1.5
            appraisal_rating = "Unsatisfactory (1)"
        else:
            appraisal_rating = "Not yet rated by supervisor"
        
        st.info(f"**Rating:** {appraisal_rating}")

        # Recommendation (Read-only)
        recommendation_from_file = load_data("current_appraisal.json", {}).get("recommendation", "No recommendation yet from supervisor.")
        st.text_area(
            "Recommendation",
            value=recommendation_from_file,
            height=70,
            disabled=True,
            key="recommendation_display"
        )

        submit_appraisal = st.form_submit_button("Submit Self-Appraisal")

        if submit_appraisal:
            st.session_state.performance_goals = updated_goals
            save_data(st.session_state.performance_goals, "performance_goals.json")
            
            appraisal_record = {
                "appraisal_period": appraisal_period,
                "goals": updated_goals,
                "overall_self_score": overall_self_score,
                "overall_supervisor_score": overall_supervisor_score, # This remains what was in file, or 0
                "appraisal_date": str(datetime.now().date()),
                "overall_supervisor_comment": overall_supervisor_comment_from_file, # Retain from file
                "recommendation": recommendation_from_file # Retain from file
            }
            # For simplicity, we'll overwrite a single appraisal record,
            # or you could append to a list of past appraisals.
            # For now, saving as a general "current_appraisal.json"
            save_data(appraisal_record, "current_appraisal.json") 
            st.success("Self-appraisal submitted successfully!")
            st.rerun()

    # Display an option to download the current appraisal if data exists
    if os.path.exists("current_appraisal.json") and os.path.getsize("current_appraisal.json") > 0:
        current_appraisal_data = load_data("current_appraisal.json", {})
        if current_appraisal_data:
            st.markdown("---")
            st.subheader("Download Current Appraisal")
            pdf_bytes = generate_appraisal_pdf(current_appraisal_data, st.session_state.user_profile)
            st.download_button(
                label="Download Current Appraisal as PDF",
                data=pdf_bytes,
                file_name=f"Performance_Appraisal_{current_appraisal_data.get('appraisal_period', 'Current')}.pdf",
                mime="application/pdf",
                key="download_appraisal_pdf"
            )

    if st.button("Back to Dashboard", key="back_from_appraisal"):
        st.session_state.current_page = "dashboard"
        st.rerun()


# --- Main Application Logic ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Polaris HR Portal")

# Inject Font Awesome CSS
st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """,
    unsafe_allow_html=True
)

if not st.session_state.logged_in:
    login_form()
else:
    with st.sidebar:
        st.title("Navigation")
        
        if st.button("Dashboard", key="sidebar_dashboard_main"):
            st.session_state.current_page = "dashboard"
            st.rerun()

        st.subheader("Requests")
        # Replaced display_sidebar_icon with Font Awesome icon
        st.markdown('<i class="fas fa-file-alt fa-lg" style="color: #4CAF50; margin-right: 10px;"></i>', unsafe_allow_html=True)
        if st.button("Apply for Leave", key="sidebar_apply_leave"):
            st.session_state.current_page = "leave_request"
            st.rerun()
        if st.button("View Leave Applications", key="sidebar_view_leave_applications"):
            st.session_state.current_page = "view_leave_applications"
            st.rerun()
        if st.button("Opex/Capex Requisition", key="sidebar_opex_capex"):
            st.session_state.current_page = "opex_capex_form"
            st.rerun()
        if st.button("View Opex/Capex Requisitions", key="sidebar_view_opex_capex_applications"):
            st.session_state.current_page = "view_opex_capex_applications"
            st.rerun()
        st.write("Other Request types coming soon...")

        st.subheader("Performance")
        # Replaced display_sidebar_icon with Font Awesome icon
        st.markdown('<i class="fas fa-chart-line fa-lg" style="color: #007BFF; margin-right: 10px;"></i>', unsafe_allow_html=True)
        # Updated buttons as requested
        if st.button("KPI Goals Setting", key="sidebar_kpi_goal_setting"):
            st.session_state.current_page = "performance_goal_setting"
            st.session_state.edit_goal_index = None # Reset edit state when navigating
            st.rerun()
        if st.button("View KPI Goals", key="sidebar_view_kpi_goals"):
            st.session_state.current_page = "performance_goal_setting" # This page already lists goals
            st.session_state.edit_goal_index = None # Reset edit state when navigating
            st.rerun()
        if st.button("Appraisal", key="sidebar_appraisal"):
            st.session_state.current_page = "performance_appraisal"
            st.session_state.edit_goal_index = None # Reset edit state when navigating
            st.rerun()
        if st.button("View Appraisal", key="sidebar_view_appraisal"):
            st.session_state.current_page = "performance_appraisal" # This page already shows the appraisal
            st.session_state.edit_goal_index = None # Reset edit state when navigating
            st.rerun()
        st.write("Performance Appraisal History coming soon...")

        st.subheader("Payroll")
        # Replaced display_sidebar_icon with Font Awesome icon
        st.markdown('<i class="fas fa-money-bill-alt fa-lg" style="color: #FFC107; margin-right: 10px;"></i>', unsafe_allow_html=True)
        if st.button("View Payslips", key="sidebar_view_payslips"):
            st.info("View Payslips page coming soon!")
        st.write("Payroll History & Tax Details coming soon...")

        st.subheader("More")
        # Replaced display_sidebar_icon with Font Awesome icon
        st.markdown('<i class="fas fa-ellipsis-h fa-lg" style="color: #6F42C1; margin-right: 10px;"></i>', unsafe_allow_html=True)
        if st.button("Staff Profile", key="sidebar_staff_profile"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        st.write("CV Details, Certificates, Workshops Attended coming soon...")
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.current_page = "login"
            st.session_state.leave_requests = load_data("leave_requests.json", [])
            st.session_state.opex_capex_requests = load_data("opex_capex_requests.json", [])
            st.session_state.user_profile = load_data("user_profile.json", default_profile)
            st.session_state.performance_goals = load_data("performance_goals.json", [])
            st.session_state.edit_goal_index = None
            # Also reset appraisal data if you want it fresh on logout
            if os.path.exists("current_appraisal.json"):
                os.remove("current_appraisal.json") 
            st.rerun()

    if st.session_state.current_page == "dashboard":
        display_dashboard()
    elif st.session_state.current_page == "leave_request":
        leave_request_form()
    elif st.session_state.current_page == "view_leave_applications":
        view_leave_applications()
    elif st.session_state.current_page == "opex_capex_form":
        opex_capex_form()
    elif st.session_state.current_page == "view_opex_capex_applications":
        view_opex_capex_applications()
    elif st.session_state.current_page == "performance_goal_setting":
        performance_goal_setting()
    elif st.session_state.current_page == "performance_appraisal": # New page handler
        performance_appraisal()
