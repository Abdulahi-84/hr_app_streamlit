import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
from fpdf import FPDF # Correct import for fpdf
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
if 'current_appraisal' not in st.session_state:
    st.session_state.current_appraisal = load_data("current_appraisal.json", {
        "appraisal_period": "",
        "goals": [],
        "overall_supervisor_comment": "",
        "recommendation": ""
    })

# --- Common UI Elements ---
def display_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=150)
    else:
        st.error(f"Company logo not found at: {LOGO_PATH}")
        st.warning(f"Please ensure '{LOGO_FILE_NAME}' is in the same directory as the app.")

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
    pdf.set_font("Helvetica", size=12)

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Polaris Digitech - Leave Application", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Helvetica", '', 12) 
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Phone: {user_profile.get('phone_number', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Leave Request Details:", ln=True)
    pdf.set_font("Helvetica", '', 10)
    
    for key, value in leave_request_data.items():
        if key in ["start_date", "end_date", "submission_date"] and value:
            try:
                value = datetime.strptime(value, '%Y-%m-%d').strftime('%B %d, %Y')
            except ValueError:
                pass
            
        display_key = key.replace('_', ' ').title()
        
        pdf.cell(0, 7, f"{display_key}: {value}", ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", 'I', 9) 
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    return bytes(pdf.output(dest='S'))

def generate_opex_capex_pdf(request_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12) 

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Helvetica", 'B', 16) 
    pdf.cell(0, 10, f"Polaris Digitech - {request_data.get('requisition_type', 'N/A')} Requisition", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Phone: {user_profile.get('phone_number', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Requisition Details:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    
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
    pdf.set_font("Helvetica", 'BU', 10) 
    pdf.cell(0, 7, "Cost Breakdown:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    pdf.cell(0, 7, f"Materials Cost: {request_data.get('materials_cost', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Labour/Services Cost: {request_data.get('labour_cost', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Withholding Tax (%): {request_data.get('wht_percentage', 'None')}", ln=True)
    pdf.cell(0, 7, f"Withholding Tax Amount: {request_data.get('wht_amount', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Net Labour/Services Cost: {request_data.get('net_labour_cost', 0.0):,.2f} NGN", ln=True)
    pdf.set_font("Helvetica", 'B', 10) 
    pdf.cell(0, 7, f"Total Net Amount Requested: {request_data.get('net_amount_requested', 0.0):,.2f} NGN", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    
    pdf.cell(0, 7, f"Amount Budgeted: {request_data.get('amount_budgeted', 0.0):,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Budget Balance: {request_data.get('budget_balance', 0.0):,.2f} NGN", ln=True)
    pdf.ln(2) # Little space

    pdf.set_font("Helvetica", 'BU', 10) 
    pdf.cell(0, 7, "Account Details:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
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
        pdf.set_font("Helvetica", 'B', 12) 
        pdf.cell(0, 10, "Attached Document:", ln=True)
        pdf.set_font("Helvetica", '', 10) 
        pdf.cell(0, 7, f"- {os.path.basename(uploaded_doc_path)}", ln=True)
    else:
        pdf.cell(0, 7, "No document attached.", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Approval Status:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    pdf.cell(0, 7, f"Admin Manager: {request_data.get('status_admin', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"Finance Manager: {request_data.get('status_finance', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"HR Manager: {request_data.get('status_hr', 'Pending')}", ln=True)
    pdf.cell(0, 7, f"Managing Director: {request_data.get('status_md', 'Pending')}", ln=True)

    pdf.ln(10)
    pdf.set_font("Helvetica", 'I', 9) 
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    return bytes(pdf.output(dest='S'))

def generate_appraisal_pdf(appraisal_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12) 

    pdf.set_text_color(30, 144, 255)
    pdf.set_font("Helvetica", 'B', 16) 
    pdf.cell(0, 10, "Polaris Digitech - Performance Appraisal", align="C", ln=True)
    pdf.set_text_color(0, 0, 0)

    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Employee Details:", ln=True)
    pdf.set_font("Helvetica", '', 10) 
    pdf.cell(0, 7, f"Name: {user_profile.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Department: {user_profile.get('department', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Email: {user_profile.get('email_address', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Appraisal Period: " + appraisal_data.get('appraisal_period', 'N/A'), ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 11) 
    pdf.cell(0, 10, "Performance Goals:", ln=True)
    pdf.ln(2)

    total_weighted_self_score = 0
    total_weighted_supervisor_score = 0
    total_weight = 0

    for i, goal in enumerate(appraisal_data.get('goals', [])):
        pdf.set_font("Helvetica", 'B', 10) 
        # Use multi_cell for goal description as it can be long
        pdf.multi_cell(0, 7, f"Goal {i+1}: {goal.get('s_n_goals', 'N/A')}") 
        pdf.set_font("Helvetica", '', 10) 
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
    pdf.set_font("Helvetica", 'B', 12) 
    pdf.cell(0, 10, "Summary Scores:", ln=True)
    pdf.set_font("Helvetica", '', 10) 

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
    pdf.set_font("Helvetica", 'B', 11) 
    pdf.cell(0, 10, "Overall Supervisor's Comment:", ln=True) # New
    pdf.set_font("Helvetica", '', 10) 
    pdf.multi_cell(0, 7, appraisal_data.get('overall_supervisor_comment', 'N/A')) # New

    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 11) 
    pdf.cell(0, 10, "Recommendation:", ln=True) # New
    pdf.set_font("Helvetica", '', 10) 
    pdf.multi_cell(0, 7, appraisal_data.get('recommendation', 'N/A')) # New


    pdf.ln(10)
    pdf.set_font("Helvetica", 'I', 9) 
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
        title = st.text_input("Title", help="Brief summary of the request (e.g., 'Purchase of Office Supplies', 'Server Upgrade Project')")
        details = st.text_area("Detailed Justification & Description", height=150, help="Provide comprehensive details including necessity, expected benefits, and specifications.")
        
        st.subheader("Cost Breakdown")
        materials_cost = st.number_input("Cost of Materials/Goods (NGN)", min_value=0.0, format="%.2f", value=0.0)
        labour_cost = st.number_input("Cost of Labour/Services (NGN)", min_value=0.0, format="%.2f", value=0.0)
        
        # Calculate Amount Requested (before WHT)
        amount_requested_before_wht = materials_cost + labour_cost

        st.write(f"**Total Amount Requested (before WHT): {amount_requested_before_wht:,.2f} NGN**")

        wht_percentage_options = ["None", "5%", "10%"]
        wht_percentage_str = st.selectbox("Withholding Tax (WHT) Percentage on Services", options=wht_percentage_options, index=0)
        
        wht_amount = 0.0
        net_labour_cost = labour_cost

        if wht_percentage_str != "None":
            wht_rate = float(wht_percentage_str.strip('%')) / 100
            wht_amount = labour_cost * wht_rate
            net_labour_cost = labour_cost - wht_amount
            st.info(f"Calculated WHT Amount: {wht_amount:,.2f} NGN (Net Labour/Services Cost: {net_labour_cost:,.2f} NGN)")

        net_amount_requested = materials_cost + net_labour_cost
        st.markdown(f"### **Total Net Amount Requested: {net_amount_requested:,.2f} NGN**")

        amount_budgeted = st.number_input("Amount Budgeted for this (NGN)", min_value=0.0, format="%.2f", help="Enter the budgeted amount for this specific request if applicable.")
        budget_balance = amount_budgeted - net_amount_requested
        st.info(f"Calculated Budget Balance: {budget_balance:,.2f} NGN")

        st.subheader("Beneficiary Details")
        selected_beneficiary_name = st.selectbox("Select Beneficiary", BENEFICIARY_NAMES, key="beneficiary_select")

        account_name_default = BENEFICIARIES_DATA[selected_beneficiary_name]["Account Name"]
        account_no_default = BENEFICIARIES_DATA[selected_beneficiary_name]["Account No"]
        bank_default = BENEFICIARIES_DATA[selected_beneficiary_name]["Bank"]

        if selected_beneficiary_name == "Other (Manually Enter Details)":
            account_name = st.text_input("Account Name", value="", help="Enter the beneficiary's account name")
            account_no = st.text_input("Account Number", value="", help="Enter the beneficiary's account number")
            bank = st.text_input("Bank Name", value="", help="Enter the beneficiary's bank name")
        else:
            account_name = st.text_input("Account Name", value=account_name_default, disabled=True)
            account_no = st.text_input("Account Number", value=account_no_default, disabled=True)
            bank = st.text_input("Bank Name", value=bank_default, disabled=True)
        
        st.subheader("Supporting Documents")
        uploaded_file = st.file_uploader("Upload Supporting Document (e.g., Invoice, Quotation)", type=["pdf", "jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Submit Requisition")

        if submitted:
            if not all([title, details, selected_beneficiary_name, account_name, account_no, bank]):
                st.error("Please fill in all required requisition and beneficiary details.")
            elif net_amount_requested <= 0:
                st.error("Total Net Amount Requested must be greater than zero.")
            else:
                uploaded_doc_path = save_uploaded_file(uploaded_file)

                opex_capex_request = {
                    "requisition_type": requisition_type,
                    "title": title,
                    "details": details,
                    "materials_cost": materials_cost,
                    "labour_cost": labour_cost,
                    "wht_percentage": wht_percentage_str,
                    "wht_amount": wht_amount,
                    "net_labour_cost": net_labour_cost,
                    "net_amount_requested": net_amount_requested,
                    "amount_budgeted": amount_budgeted,
                    "budget_balance": budget_balance,
                    "beneficiaries": selected_beneficiary_name,
                    "account_name": account_name,
                    "account_no": account_no,
                    "bank": bank,
                    "uploaded_document_path": uploaded_doc_path,
                    "submitted_date": str(datetime.now().date()),
                    "status_admin": "Pending", # Initial status for Admin Manager
                    "status_finance": "Pending", # Initial status for Finance Manager
                    "status_hr": "Pending",     # Initial status for HR Manager
                    "status_md": "Pending"      # Initial status for Managing Director
                }
                st.session_state.opex_capex_requests.append(opex_capex_request)
                save_data(st.session_state.opex_capex_requests, "opex_capex_requests.json")
                st.success("Opex/Capex requisition submitted for approval.")
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
        if st.button("Submit a Requisition Now"):
            st.session_state.current_page = "opex_capex_form"
            st.rerun()
    else:
        st.write("Here are your submitted Opex/Capex requisitions:")
        
        # Optionally add filters for status or type
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"], key="opex_filter_status")
        filter_type = st.selectbox("Filter by Type", ["All", "Opex", "Capex"], key="opex_filter_type")

        filtered_requests = st.session_state.opex_capex_requests
        if filter_status != "All":
            # For Opex/Capex, "Pending" usually refers to the final MD status
            filtered_requests = [req for req in filtered_requests if req['status_md'] == filter_status]
        if filter_type != "All":
            filtered_requests = [req for req in filtered_requests if req['requisition_type'] == filter_type]

        if not filtered_requests:
            st.info("No requisitions match your filter criteria.")
        else:
            for i, req in enumerate(filtered_requests):
                st.markdown(f"### Requisition {i+1}: {req.get('title', 'N/A')} ({req.get('requisition_type', 'N/A')})")
                st.write(f"**Submitted On:** {req.get('submitted_date', 'N/A')}")
                st.write(f"**Net Amount Requested:** {req.get('net_amount_requested', 0.0):,.2f} NGN")
                st.write(f"**Beneficiary:** {req.get('beneficiaries', 'N/A')}")
                
                st.markdown("##### Current Approval Status:")
                st.write(f"- Admin Manager: **{req.get('status_admin', 'Pending')}**")
                st.write(f"- Finance Manager: **{req.get('status_finance', 'Pending')}**")
                st.write(f"- HR Manager: **{req.get('status_hr', 'Pending')}**")
                st.write(f"- Managing Director: **{req.get('status_md', 'Pending')}**")
                
                with st.expander(f"View Details for Requisition {i+1}"):
                    st.write(f"**Details:**")
                    st.markdown(req.get('details', 'N/A'))
                    st.write(f"**Materials Cost:** {req.get('materials_cost', 0.0):,.2f} NGN")
                    st.write(f"**Labour/Services Cost:** {req.get('labour_cost', 0.0):,.2f} NGN")
                    st.write(f"**WHT Percentage:** {req.get('wht_percentage', 'None')}")
                    st.write(f"**WHT Amount:** {req.get('wht_amount', 0.0):,.2f} NGN")
                    st.write(f"**Net Labour/Services Cost:** {req.get('net_labour_cost', 0.0):,.2f} NGN")
                    st.write(f"**Amount Budgeted:** {req.get('amount_budgeted', 0.0):,.2f} NGN")
                    st.write(f"**Budget Balance:** {req.get('budget_balance', 0.0):,.2f} NGN")
                    st.write(f"**Account Name:** {req.get('account_name', 'N/A')}")
                    st.write(f"**Account Number:** {req.get('account_no', 'N/A')}")
                    st.write(f"**Bank:** {req.get('bank', 'N/A')}")

                    uploaded_doc_path = req.get("uploaded_document_path")
                    if uploaded_doc_path and os.path.exists(uploaded_doc_path):
                        st.download_button(
                            label=f"Download Attached Document: {os.path.basename(uploaded_doc_path)}",
                            data=open(uploaded_doc_path, "rb").read(),
                            file_name=os.path.basename(uploaded_doc_path),
                            key=f"download_opex_doc_{i}"
                        )
                    else:
                        st.info("No supporting document uploaded.")
                
                pdf_bytes = generate_opex_capex_pdf(req, st.session_state.user_profile)
                st.download_button(
                    label=f"Download Requisition {i+1} as PDF",
                    data=pdf_bytes,
                    file_name=f"Opex_Capex_Requisition_{i+1}_{req.get('submitted_date', 'N/A')}.pdf",
                    mime="application/pdf",
                    key=f"download_opex_pdf_{i}"
                )
                st.markdown("---")

    if st.button("Back to Dashboard", key="back_from_view_opex_capex"):
        st.session_state.current_page = "dashboard"
        st.rerun()

# --- Performance Goal Setting Page ---
def performance_goal_setting():
    st.title("Performance Goal Setting")
    st.write("Define your performance goals for the upcoming appraisal period.")

    with st.expander("Add New Performance Goal", expanded=True):
        with st.form("new_goal_form"):
            s_n_goals = st.text_area("S/N and Goals", help="State the goal clearly and concisely.")
            weight_self_rating = st.slider("Weight (%) (Self-Rating)", 0, 100, 20, help="Assign a weight to this goal indicating its importance.")
            
            add_goal_button = st.form_submit_button("Add Goal")

            if add_goal_button:
                if s_n_goals and weight_self_rating >= 0:
                    new_goal = {
                        "s_n_goals": s_n_goals,
                        "weight_self_rating": weight_self_rating,
                        "status": "Not Started", # Initial status
                        "self_appraisal_score": None, # Will be set during appraisal
                        "employee_remark": "",
                        "line_managers_rating": None, # Will be set by manager
                        "supervisor_comment": ""
                    }
                    st.session_state.performance_goals.append(new_goal)
                    save_data(st.session_state.performance_goals, "performance_goals.json")
                    st.success("Performance goal added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in the goal description and set a valid weight.")

    st.markdown("---")
    st.subheader("My Performance Goals")

    if not st.session_state.performance_goals:
        st.info("You haven't set any performance goals yet.")
    else:
        # Display existing goals with edit/delete options
        for i, goal in enumerate(st.session_state.performance_goals):
            st.markdown(f"#### Goal {i+1}")
            st.write(f"**Goal:** {goal.get('s_n_goals', 'N/A')}")
            st.write(f"**Weight:** {goal.get('weight_self_rating', 0)}%")
            st.write(f"**Status:** `{goal.get('status', 'N/A')}`")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Edit Goal {i+1}", key=f"edit_goal_{i}"):
                    st.session_state.edit_goal_index = i
                    st.rerun()
            with col2:
                if st.button(f"Delete Goal {i+1}", key=f"delete_goal_{i}"):
                    del st.session_state.performance_goals[i]
                    save_data(st.session_state.performance_goals, "performance_goals.json")
                    st.success(f"Goal {i+1} deleted.")
                    st.session_state.edit_goal_index = None # Reset edit state if deleted
                    st.rerun()
            st.markdown("---")

        # Edit form for selected goal
        if st.session_state.edit_goal_index is not None:
            edit_goal = st.session_state.performance_goals[st.session_state.edit_goal_index]
            st.subheader(f"Editing Goal {st.session_state.edit_goal_index + 1}")
            with st.form("edit_goal_form"):
                edited_s_n_goals = st.text_area("S/N and Goals", value=edit_goal.get('s_n_goals', ''), key="edited_s_n_goals")
                edited_weight_self_rating = st.slider("Weight (%)", 0, 100, edit_goal.get('weight_self_rating', 0), key="edited_weight_self_rating")
                edited_status = st.selectbox("Status", ["Not Started", "In Progress", "On Hold", "Complete"], index=["Not Started", "In Progress", "On Hold", "Complete"].index(edit_goal.get('status', 'Not Started')), key="edited_status")
                
                update_goal_button = st.form_submit_button("Update Goal")

                if update_goal_button:
                    st.session_state.performance_goals[st.session_state.edit_goal_index] = {
                        "s_n_goals": edited_s_n_goals,
                        "weight_self_rating": edited_weight_self_rating,
                        "status": edited_status,
                        "self_appraisal_score": edit_goal.get('self_appraisal_score'),
                        "employee_remark": edit_goal.get('employee_remark'),
                        "line_managers_rating": edit_goal.get('line_managers_rating'),
                        "supervisor_comment": edit_goal.get('supervisor_comment')
                    }
                    save_data(st.session_state.performance_goals, "performance_goals.json")
                    st.success("Goal updated successfully!")
                    st.session_state.edit_goal_index = None # Exit edit mode
                    st.rerun()
                
                if st.button("Cancel Edit", key="cancel_edit_goal"):
                    st.session_state.edit_goal_index = None
                    st.rerun()

    if st.button("Back to Dashboard", key="back_from_goal_setting"):
        st.session_state.current_page = "dashboard"
        st.rerun()

# --- Performance Appraisal Page ---
def performance_appraisal_page():
    st.title("My Performance Appraisal")

    st.info("This section allows you to conduct your self-appraisal and view supervisor ratings.")

    # Initialize current appraisal if not already done, pulling from session state
    if not st.session_state.current_appraisal.get("appraisal_period"):
        st.session_state.current_appraisal["appraisal_period"] = f"Annual Appraisal {datetime.now().year}"

    st.subheader(f"Appraisal Period: {st.session_state.current_appraisal['appraisal_period']}")
    
    st.markdown("---")
    st.subheader("Performance Goals Self-Appraisal")

    if not st.session_state.performance_goals:
        st.warning("You have no performance goals set. Please set goals first in the 'Performance Goal Setting' section.")
        if st.button("Go to Goal Setting"):
            st.session_state.current_page = "performance_goal_setting"
            st.rerun()
        return

    # Create a form for self-appraisal
    with st.form("self_appraisal_form"):
        updated_goals_for_appraisal = []
        for i, goal in enumerate(st.session_state.performance_goals):
            st.markdown(f"#### Goal {i+1}: {goal.get('s_n_goals', 'N/A')} (Weight: {goal.get('weight_self_rating', 0)}%)")
            
            # Employee's self-appraisal score
            self_score = st.slider(
                f"Your Self-Appraisal Score (0-5) for Goal {i+1}",
                0, 5, value=goal.get('self_appraisal_score', 0) or 0, key=f"self_score_{i}"
            )
            # Employee's remark
            employee_remark = st.text_area(
                f"Your Remark for Goal {i+1}",
                value=goal.get('employee_remark', ''), key=f"employee_remark_{i}"
            )

            # Display supervisor's rating and comment if available (read-only for employee)
            st.write(f"**Supervisor's Score:** `{goal.get('line_managers_rating', 'N/A')}`")
            st.write(f"**Supervisor's Comment:** `{goal.get('supervisor_comment', 'N/A')}`")

            # Update the goal dictionary for submission
            updated_goal = goal.copy()
            updated_goal['self_appraisal_score'] = self_score
            updated_goal['employee_remark'] = employee_remark
            updated_goals_for_appraisal.append(updated_goal)
        
        st.markdown("---")
        st.subheader("Overall Feedback")
        overall_supervisor_comment_placeholder = st.empty()
        recommendation_placeholder = st.empty()

        # Display overall supervisor comment and recommendation (read-only)
        overall_supervisor_comment_placeholder.write(f"**Overall Supervisor's Comment:** `{st.session_state.current_appraisal.get('overall_supervisor_comment', 'N/A')}`")
        recommendation_placeholder.write(f"**Recommendation:** `{st.session_state.current_appraisal.get('recommendation', 'N/A')}`")

        submit_appraisal = st.form_submit_button("Save Self-Appraisal")

        if submit_appraisal:
            st.session_state.performance_goals = updated_goals_for_appraisal # Update main goals list
            save_data(st.session_state.performance_goals, "performance_goals.json")
            
            # Update current_appraisal structure for PDF generation
            st.session_state.current_appraisal['goals'] = updated_goals_for_appraisal
            save_data(st.session_state.current_appraisal, "current_appraisal.json") # Save full appraisal data
            st.success("Your self-appraisal has been saved!")
            st.rerun()

    # Calculate and display overall scores
    if st.session_state.performance_goals:
        total_weighted_self_score = 0
        total_weighted_supervisor_score = 0
        total_weight = sum(g.get('weight_self_rating', 0) for g in st.session_state.performance_goals)

        for goal in st.session_state.performance_goals:
            weight = goal.get('weight_self_rating', 0)
            self_score = goal.get('self_appraisal_score', 0) or 0
            supervisor_score = goal.get('line_managers_rating', 0) or 0

            total_weighted_self_score += (weight / 100) * self_score
            total_weighted_supervisor_score += (weight / 100) * supervisor_score

        st.markdown("---")
        st.subheader("Appraisal Summary")
        if total_weight > 0:
            overall_self_score_0_5 = (total_weighted_self_score / total_weight) * 5
            overall_supervisor_score_0_5 = (total_weighted_supervisor_score / total_weight) * 5 # Scale to 0-5

            st.metric(label="Overall Self-Appraisal Score (0-5)", value=f"{overall_self_score_0_5:,.2f}")
            st.metric(label="Overall Supervisor's Score (0-5)", value=f"{overall_supervisor_score_0_5:,.2f}")
        else:
            st.info("No weighted goals to calculate overall scores.")

    # PDF Download Button
    if st.session_state.current_appraisal.get('goals'): # Only allow download if there are goals saved
        pdf_bytes = generate_appraisal_pdf(st.session_state.current_appraisal, st.session_state.user_profile)
        st.download_button(
            label="Download My Performance Appraisal as PDF",
            data=pdf_bytes,
            file_name=f"Performance_Appraisal_{st.session_state.user_profile.get('name', 'Employee')}_{datetime.now().year}.pdf",
            mime="application/pdf",
            key="download_appraisal_pdf"
        )

    if st.button("Back to Dashboard", key="back_from_appraisal"):
        st.session_state.current_page = "dashboard"
        st.rerun()


# --- Main Application Logic ---
def main():
    st.set_page_config(
        page_title="Polaris Digitech Staff Portal",
        page_icon=":briefcase:", # Use an appropriate icon
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for Font Awesome icons and general styling
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .st-emotion-cache-1jm9LEf { /* Adjust sidebar width */
                width: 250px;
            }
            .sidebar .sidebar-content {
                padding-top: 20px;
            }
            .sidebar .stButton>button {
                width: 100%;
                text-align: left;
                padding-left: 20px;
            }
            .st-emotion-cache-v01q57 a { /* For the links generated by st.link_button */
                width: 100%;
                text-align: center;
                padding-left: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
                background-color: #f0f2f6;
                color: #000;
                border-radius: 0.5rem;
                padding: 0.46875rem 0.8125rem;
                line-height: 1.7;
            }
            .st-emotion-cache-v01q57 a:hover {
                background-color: #e0e2e6;
            }
        </style>
        """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        login_form()
    else:
        # Sidebar for navigation
        with st.sidebar:
            st.markdown(f"### Welcome, {st.session_state.username.split()[0]}!")
            st.write("---")
            
            # Use columns for icon and text for better alignment
            if st.button("🏠 Dashboard", key="nav_dashboard"):
                st.session_state.current_page = "dashboard"
                st.rerun()
            if st.button("🗓️ Leave Request", key="nav_leave_request"):
                st.session_state.current_page = "leave_request"
                st.rerun()
            if st.button("📄 View Leave Applications", key="nav_view_leave"):
                st.session_state.current_page = "view_leave_applications"
                st.rerun()
            if st.button("💰 Opex/Capex Requisition", key="nav_opex_capex"):
                st.session_state.current_page = "opex_capex_form"
                st.rerun()
            if st.button("📈 View Opex/Capex", key="nav_view_opex_capex"):
                st.session_state.current_page = "view_opex_capex_applications"
                st.rerun()
            if st.button("🎯 Performance Goal Setting", key="nav_goal_setting"):
                st.session_state.current_page = "performance_goal_setting"
                st.rerun()
            if st.button("📊 My Performance Appraisal", key="nav_appraisal"):
                st.session_state.current_page = "performance_appraisal_page"
                st.rerun()
            
            st.write("---")
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
        elif st.session_state.current_page == "performance_appraisal_page":
            performance_appraisal_page()

if __name__ == "__main__":
    main()
