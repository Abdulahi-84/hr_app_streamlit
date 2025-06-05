import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64
import bcrypt # For password hashing
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration & Paths ---
# For deployment, assume images are in the same directory as the app
LOGO_FILE_NAME = "polaris_digitech_logo.png"
LOGO_PATH = LOGO_FILE_NAME # Now directly refers to the file in the same directory

ABDULAHI_IMAGE_FILE_NAME = "abdulahi_image.png"
ABDULAHI_IMAGE_PATH = ABDULAHI_IMAGE_FILE_NAME

# --- Data Files ---
USERS_FILE = "users.json" # File for all user accounts and their specific data (profile, goals, appraisal)
LEAVE_REQUESTS_FILE = "leave_requests.json"
OPEX_CAPEX_REQUESTS_FILE = "opex_capex_requests.json"


# --- Define Approval Route Emails (For Simulated Notifications) ---
# NOTE: For actual email sending, you'd need an email server and credentials (use Streamlit secrets for credentials!)
APPROVAL_EMAILS = {
    "Admin Manager": "admin.manager@example.com",
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
    "Emmafem Resources Nig. Ent.": {"Account Name": "Alimi", "Account No": "0987654321", "Bank": "Zenith Bank"},
    "Topmost Group": {"Account Name": "Ola", "Account No": "3456789012", "Bank": "UBA"},
    "Wella Services": {"Account Name": "Adeola", "Account No": "4567890123", "Bank": "First Bank"},
    "Zuma Construction": {"Account Name": "Musa", "Account No": "5678901234", "Bank": "Access Bank"},
    "Prime Innovations": {"Account Name": "Chidi", "Account No": "6789012345", "Bank": "GTB"},
    "Global Logistics Inc.": {"Account Name": "Fatima", "Account No": "7890123456", "Bank": "Zenith Bank"},
    "Tech Solutions Ltd.": {"Account Name": "David", "Account No": "8901234567", "Bank": "UBA"}
}


# --- Utility Functions ---

def hash_password(password):
    """Hashes a password using bcrypt."""
    # Generate a salt and hash the password
    # 12 is a good cost factor; higher is slower but more secure
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def check_password(password, hashed_password):
    """Checks if a password matches a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def load_data(file_path, default_value):
    """Loads JSON data from a file, returning default_value if file not found or empty."""
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        return default_value
    with open(file_path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default_value

def save_data(data, file_path):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# --- User Management (Centralized in users.json) ---

def initialize_users_data():
    """Initializes the users.json file with default accounts if it doesn't exist.
    Each user now contains their profile, goals, and appraisal data directly.
    """
    if not os.path.exists(USERS_FILE) or os.stat(USERS_FILE).st_size == 0:
        st.info("No users file found. Initializing with default admin and manager accounts.")
        default_users = [
            {
                "username": "admin",
                "password_hash": hash_password("admin_password_123"), # Change this for production!
                "role": "Admin Manager",
                "employee_id": "EMP001",
                "profile": {
                    "full_name": "Admin User",
                    "employee_id": "EMP001",
                    "department": "Administration",
                    "position": "Admin Manager",
                    "email": "admin@example.com",
                    "phone": "08011111111",
                    "address": "123 Admin St, Lagos",
                    "emergency_contact": "Admin Emergency, 09011111111"
                },
                "performance_goals": [],
                "current_appraisal": {}
            },
            {
                "username": "finance",
                "password_hash": hash_password("finance_password_123"), # Change this for production!
                "role": "Finance Manager",
                "employee_id": "EMP002",
                "profile": {
                    "full_name": "Finance User",
                    "employee_id": "EMP002",
                    "department": "Finance",
                    "position": "Finance Manager",
                    "email": "finance@example.com",
                    "phone": "08022222222",
                    "address": "456 Finance Ave, Lagos",
                    "emergency_contact": "Finance Emergency, 09022222222"
                },
                "performance_goals": [],
                "current_appraisal": {}
            },
            {
                "username": "hr",
                "password_hash": hash_password("hr_password_123"), # Change this for production!
                "role": "HR Manager",
                "employee_id": "EMP003",
                "profile": {
                    "full_name": "HR User",
                    "employee_id": "EMP003",
                    "department": "Human Resources",
                    "position": "HR Manager",
                    "email": "hr@example.com",
                    "phone": "08033333333",
                    "address": "789 HR Rd, Lagos",
                    "emergency_contact": "HR Emergency, 09033333333"
                },
                "performance_goals": [],
                "current_appraisal": {}
            },
            {
                "username": "md",
                "password_hash": hash_password("md_password_123"), # Change this for production!
                "role": "Managing Director",
                "employee_id": "EMP004",
                "profile": {
                    "full_name": "Managing Director User",
                    "employee_id": "EMP004",
                    "department": "Executive",
                    "position": "Managing Director",
                    "email": "md@example.com",
                    "phone": "08044444444",
                    "address": "101 MD Blvd, Lagos",
                    "emergency_contact": "MD Emergency, 09044444444"
                },
                "performance_goals": [],
                "current_appraisal": {}
            }
        ]
        save_data(default_users, USERS_FILE)
        st.success("Initial users created.")
    else:
        st.info("Users file found. Loading existing users.")


def get_user_by_username(username):
    users = load_data(USERS_FILE, [])
    for user in users:
        if user["username"] == username:
            return user
    return None

def get_user_by_employee_id(employee_id):
    users = load_data(USERS_FILE, [])
    for user in users:
        if user["employee_id"] == employee_id:
            return user
    return None

def update_user_data(updated_user):
    """Updates a user's data in the users.json file."""
    all_users = load_data(USERS_FILE, [])
    for i, user in enumerate(all_users):
        if user["username"] == updated_user["username"]:
            all_users[i] = updated_user
            break
    save_data(all_users, USERS_FILE)

# --- Email Simulation Function ---
def send_email_notification(to_email, subject, body):
    """Simulates sending an email notification."""
    # In a real app, you would use smtplib to connect to an SMTP server
    # and send the email. For this simulation, we just print the details.
    st.info(f"--- SIMULATING EMAIL SEND ---")
    st.info(f"To: {to_email}")
    st.info(f"Subject: {subject}")
    st.info(f"Body: {body}")
    st.info(f"--- EMAIL SIMULATION END ---")

    # Example of actual email sending (requires configuration and credentials)
    # sender_email = "your_email@example.com"
    # sender_password = os.getenv("EMAIL_PASSWORD") # IMPORTANT: Use environment variable for password!
    # if not sender_password:
    #     st.warning("Email password not set in environment variables. Email notification failed.")
    #     return

    # try:
    #     msg = MIMEMultipart()
    #     msg['From'] = sender_email
    #     msg['To'] = to_email
    #     msg['Subject'] = subject
    #     msg.attach(MIMEText(body, 'plain'))

    #     server = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Example for Gmail
    #     server.login(sender_email, sender_password)
    #     server.send_message(msg)
    #     server.quit()
    #     st.success(f"Notification email sent to {to_email}")
    # except Exception as e:
    #     st.error(f"Failed to send email notification: {e}")


# --- Authentication & Pages ---

def login_page():
    st.sidebar.image(LOGO_PATH, width=200)
    st.title("Polaris Digitech HR System")

    # State to toggle between Login and Sign Up forms
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False

    col1, col2 = st.columns([1,1])

    with col1:
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Username").strip()
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                user = get_user_by_username(username)
                if user and check_password(password, user["password_hash"]):
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.user_profile = user # Store the entire user object
                    st.session_state.current_page = "dashboard" # Default page after login
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with col2:
        st.header("New User?")
        st.write("Register to access the HR system.")
        if st.button("Sign Up Now"):
            st.session_state.show_signup = True
            st.rerun()

    if st.session_state.show_signup:
        st.markdown("---")
        st.header("Sign Up")
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username").strip()
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            new_employee_id = st.text_input("Employee ID").strip() # Unique ID for employees
            # You might want to limit roles for sign-up or have admin approval
            new_role = st.selectbox("Select Role", ["Employee"]) # Only employee can sign up

            signup_button = st.form_submit_button("Register")

            if signup_button:
                if not new_username or not new_password or not confirm_password or not new_employee_id:
                    st.error("All fields are required.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif get_user_by_username(new_username):
                    st.error("Username already exists. Please choose a different one.")
                elif get_user_by_employee_id(new_employee_id):
                    st.error("Employee ID already registered. Please check or contact admin.")
                else:
                    hashed_new_password = hash_password(new_password)
                    all_users = load_data(USERS_FILE, [])

                    new_user_data = {
                        "username": new_username,
                        "password_hash": hashed_new_password,
                        "role": new_role,
                        "employee_id": new_employee_id,
                        "profile": { # Initial profile for new user
                            "full_name": "", # User can update this later
                            "employee_id": new_employee_id,
                            "department": "",
                            "position": new_role, # Default position same as role for simplicity
                            "email": "",
                            "phone": "",
                            "address": "",
                            "emergency_contact": ""
                        },
                        "performance_goals": [],
                        "current_appraisal": {}
                    }
                    all_users.append(new_user_data)
                    save_data(all_users, USERS_FILE)
                    st.success("Registration successful! You can now log in.")
                    st.session_state.show_signup = False # Go back to login form
                    st.rerun()

# --- Dashboard Functionality ---
def display_dashboard():
    st.subheader(f"Welcome, {st.session_state.username}!")
    st.markdown("### HR System Dashboard")

    # Assuming you have a way to filter data specific to this user's department/role
    # For now, let's display some general HR stats or user-specific overview

    if st.session_state.role == "Admin Manager":
        st.success("You have Admin Manager access.")
        # Display admin-specific dashboard elements
        all_leave_requests = load_data(LEAVE_REQUESTS_FILE, [])
        all_opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])
        all_users = load_data(USERS_FILE, [])

        st.markdown("#### Overview Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Employees", len(all_users))
        with col2:
            st.metric("Pending Leave Requests", len([r for r in all_leave_requests if r['status'] == 'Pending']))
        with col3:
            st.metric("Pending OPEX/CAPEX Requests", len([r for r in all_opex_capex_requests if r['status'] == 'Pending']))

        # Example: Employee Distribution by Department (requires 'profile' data to be filled)
        if all_users:
            profiles = [u['profile'] for u in all_users if 'profile' in u and u['profile'].get('department')]
            if profiles:
                profile_df = pd.DataFrame(profiles)
                dept_counts = profile_df['department'].value_counts().reset_index()
                dept_counts.columns = ['Department', 'Count']
                fig = px.pie(dept_counts, values='Count', names='Department', title='Employee Distribution by Department')
                st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.role == "Finance Manager":
        st.success("You have Finance Manager access.")
        # Display finance-specific dashboard elements
        opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])
        st.markdown("#### OPEX/CAPEX Request Summary")
        if opex_capex_requests:
            df_opex_capex = pd.DataFrame(opex_capex_requests)
            status_counts = df_opex_capex['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.bar(status_counts, x='Status', y='Count', title='OPEX/CAPEX Request Status')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No OPEX/CAPEX requests to display.")

    elif st.session_state.role == "HR Manager":
        st.success("You have HR Manager access.")
        # Display HR-specific dashboard elements
        leave_requests = load_data(LEAVE_REQUESTS_FILE, [])
        st.markdown("#### Leave Request Summary")
        if leave_requests:
            df_leave = pd.DataFrame(leave_requests)
            status_counts = df_leave['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(status_counts, values='Count', names='Status', title='Leave Request Status Distribution')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No leave requests to display.")

    elif st.session_state.role == "Managing Director":
        st.success("You have Managing Director access.")
        # Display MD-specific dashboard elements (e.g., high-level summaries)
        all_leave_requests = load_data(LEAVE_REQUESTS_FILE, [])
        all_opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])

        st.markdown("#### Overall Request Performance")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Approved Leave", len([r for r in all_leave_requests if r['status'] == 'Approved']))
        with col2:
            st.metric("Total Approved OPEX/CAPEX", len([r for r in all_opex_capex_requests if r['status'] == 'Approved']))

    elif st.session_state.role == "Employee":
        st.success(f"You have Employee access. Your Employee ID: {st.session_state.user_profile.get('employee_id', 'N/A')}")
        # Display employee-specific dashboard (e.g., summary of their requests)
        employee_id = st.session_state.user_profile.get('employee_id')
        my_leave_requests = [req for req in load_data(LEAVE_REQUESTS_FILE, []) if req.get('employee_id') == employee_id]
        my_opex_capex_requests = [req for req in load_data(OPEX_CAPEX_REQUESTS_FILE, []) if req.get('employee_id') == employee_id]

        st.markdown("#### My Requests Overview")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("My Pending Leave Requests", len([r for r in my_leave_requests if r['status'] == 'Pending']))
        with col2:
            st.metric("My Pending OPEX/CAPEX Requests", len([r for r in my_opex_capex_requests if r['status'] == 'Pending']))

        # Display recent activities (e.g., latest leave/opex status)
        st.markdown("#### Recent Activity")
        if my_leave_requests or my_opex_capex_requests:
            st.write("Your most recent request statuses:")
            if my_leave_requests:
                latest_leave = max(my_leave_requests, key=lambda x: datetime.strptime(x['submission_date'], '%Y-%m-%d'))
                st.info(f"Latest Leave Request (ID: {latest_leave['request_id']}): {latest_leave['status']}")
            if my_opex_capex_requests:
                latest_opex_capex = max(my_opex_capex_requests, key=lambda x: datetime.strptime(x['submission_date'], '%Y-%m-%d'))
                st.info(f"Latest OPEX/CAPEX Request (ID: {latest_opex_capex['request_id']}): {latest_opex_capex['status']}")
        else:
            st.info("You have not submitted any requests yet.")


# --- Profile Management ---
def display_profile_management():
    st.subheader("My Profile")
    user_profile = st.session_state.user_profile.get('profile', {}) # Get profile data from session state

    with st.form("profile_form"):
        st.markdown("#### Personal Information")
        full_name = st.text_input("Full Name", value=user_profile.get("full_name", ""))
        employee_id = st.text_input("Employee ID", value=user_profile.get("employee_id", ""), disabled=True) # Employee ID usually not editable
        department = st.text_input("Department", value=user_profile.get("department", ""))
        position = st.text_input("Position", value=user_profile.get("position", ""))
        email = st.text_input("Email", value=user_profile.get("email", ""))
        phone = st.text_input("Phone Number", value=user_profile.get("phone", ""))
        address = st.text_area("Address", value=user_profile.get("address", ""))
        emergency_contact = st.text_input("Emergency Contact", value=user_profile.get("emergency_contact", ""))

        submit_button = st.form_submit_button("Update Profile")

        if submit_button:
            updated_profile = {
                "full_name": full_name,
                "employee_id": employee_id,
                "department": department,
                "position": position,
                "email": email,
                "phone": phone,
                "address": address,
                "emergency_contact": emergency_contact
            }
            # Update profile within the user's data in session state
            st.session_state.user_profile['profile'] = updated_profile
            # Save the entire users.json file
            update_user_data(st.session_state.user_profile)
            st.success("Profile updated successfully!")
            st.rerun()

# --- Leave Request Functionality ---
def leave_request_form():
    st.subheader("Leave Request Form")
    with st.form("leave_form"):
        employee_id = st.session_state.user_profile.get('employee_id', 'N/A')
        username = st.session_state.username

        st.text_input("Employee ID", value=employee_id, disabled=True)
        st.text_input("Requesting User", value=username, disabled=True)

        leave_type = st.selectbox("Leave Type", ["Annual Leave", "Sick Leave", "Maternity Leave", "Paternity Leave", "Casual Leave", "Bereavement Leave"])
        start_date = st.date_input("Start Date", datetime.today())
        end_date = st.date_input("End Date", datetime.today() + timedelta(days=7))
        reason = st.text_area("Reason for Leave")

        submit_button = st.form_submit_button("Submit Leave Request")

        if submit_button:
            if not reason:
                st.error("Reason for leave is required.")
            elif end_date < start_date:
                st.error("End date cannot be before start date.")
            else:
                leave_requests = load_data(LEAVE_REQUESTS_FILE, [])
                request_id = f"LR-{len(leave_requests) + 1:04d}"
                new_request = {
                    "request_id": request_id,
                    "employee_id": employee_id, # Tag with employee ID
                    "username": username, # Tag with username
                    "leave_type": leave_type,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "reason": reason,
                    "submission_date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "Pending",
                    "approvals": {
                        "HR Manager": {"status": "Pending", "date": None},
                        "Admin Manager": {"status": "Pending", "date": None}
                    }
                }
                leave_requests.append(new_request)
                save_data(leave_requests, LEAVE_REQUESTS_FILE)
                st.success(f"Leave request {request_id} submitted successfully!")

                # Simulate email notification to HR Manager
                hr_manager_email = APPROVAL_EMAILS.get("HR Manager", "hr_manager@example.com")
                subject = f"New Leave Request ({request_id}) from {username}"
                body = f"A new leave request has been submitted by {username} (ID: {employee_id}) for {leave_type} from {start_date} to {end_date}. Reason: {reason}. Please review."
                send_email_notification(hr_manager_email, subject, body)
                st.rerun()

def view_leave_applications():
    st.subheader("View Leave Applications")
    all_leave_requests = load_data(LEAVE_REQUESTS_FILE, [])

    if not all_leave_requests:
        st.info("No leave applications available.")
        return

    # Filter based on role
    if st.session_state.role == "Employee":
        employee_id = st.session_state.user_profile.get('employee_id')
        filtered_requests = [req for req in all_leave_requests if req.get('employee_id') == employee_id]
        if not filtered_requests:
            st.info("You have not submitted any leave requests.")
            return
        df = pd.DataFrame(filtered_requests)
        st.dataframe(df)

    elif st.session_state.role in ["HR Manager", "Admin Manager", "Managing Director"]:
        df = pd.DataFrame(all_leave_requests)

        # Basic filtering for managers
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
        if filter_status != "All":
            df = df[df['status'] == filter_status]

        if not df.empty:
            st.dataframe(df)

            # Approval/Rejection for HR/Admin Managers
            if st.session_state.role in ["HR Manager", "Admin Manager"]:
                st.markdown("#### Action on Leave Requests")
                selected_request_id = st.selectbox("Select Request ID to Action", df['request_id'].tolist())

                if selected_request_id:
                    request_to_action = next((req for req in all_leave_requests if req['request_id'] == selected_request_id), None)
                    if request_to_action:
                        # Ensure only relevant manager can approve/reject their part
                        current_manager_role = st.session_state.role
                        approval_key = current_manager_role # Use role as key (e.g., "HR Manager")

                        st.write(f"**Request ID:** {request_to_action['request_id']}")
                        st.write(f"**Employee:** {request_to_action['username']} (ID: {request_to_action['employee_id']})")
                        st.write(f"**Type:** {request_to_action['leave_type']}")
                        st.write(f"**Dates:** {request_to_action['start_date']} to {request_to_action['end_date']}")
                        st.write(f"**Reason:** {request_to_action['reason']}")
                        st.write(f"**Current Status:** {request_to_action['status']}")
                        st.write(f"**HR Approval:** {request_to_action['approvals'].get('HR Manager', {}).get('status', 'N/A')}")
                        st.write(f"**Admin Approval:** {request_to_action['approvals'].get('Admin Manager', {}).get('status', 'N/A')}")

                        if request_to_action['approvals'].get(approval_key, {}).get('status') == "Pending":
                            action = st.radio(f"Action for {current_manager_role}", ["None", "Approve", "Reject"], key=f"leave_action_{selected_request_id}")
                            if action != "None":
                                if st.button(f"Confirm {action} for {selected_request_id}"):
                                    request_to_action['approvals'][approval_key]['status'] = action
                                    request_to_action['approvals'][approval_key]['date'] = datetime.now().strftime("%Y-%m-%d")

                                    # Check overall status
                                    hr_status = request_to_action['approvals'].get('HR Manager', {}).get('status')
                                    admin_status = request_to_action['approvals'].get('Admin Manager', {}).get('status')

                                    if action == "Rejected":
                                        request_to_action['status'] = "Rejected" # Any rejection makes the whole request rejected
                                    elif hr_status == "Approved" and admin_status == "Approved":
                                        request_to_action['status'] = "Approved"

                                    save_data(all_leave_requests, LEAVE_REQUESTS_FILE)
                                    st.success(f"Leave request {selected_request_id} {action} by {current_manager_role}.")

                                    # Notify requesting employee
                                    employee_email = next((u['profile']['email'] for u in load_data(USERS_FILE, []) if u['employee_id'] == request_to_action['employee_id']), None)
                                    if employee_email:
                                        subject = f"Your Leave Request ({selected_request_id}) Status Update"
                                        body = f"Your leave request for {request_to_action['leave_type']} from {request_to_action['start_date']} to {request_to_action['end_date']} has been {request_to_action['status']} by {current_manager_role}."
                                        send_email_notification(employee_email, subject, body)
                                    st.rerun()
                        else:
                            st.info(f"This request has already been {request_to_action['approvals'].get(approval_key, {}).get('status', 'N/A')} by {current_manager_role}.")
                    else:
                        st.warning("Selected request not found.")
        else:
            st.info("No leave applications matching the filter.")

# --- OPEX/CAPEX Request Functionality ---
def opex_capex_form():
    st.subheader("OPEX/CAPEX Request Form")
    with st.form("opex_capex_form"):
        employee_id = st.session_state.user_profile.get('employee_id', 'N/A')
        username = st.session_state.username

        st.text_input("Employee ID", value=employee_id, disabled=True)
        st.text_input("Requesting User", value=username, disabled=True)

        request_type = st.selectbox("Request Type", ["OPEX", "CAPEX"])
        item_description = st.text_area("Item Description/Purpose")
        estimated_cost = st.number_input("Estimated Cost (NGN)", min_value=0.0, format="%.2f")
        beneficiary_name = st.selectbox("Beneficiary Name", list(BENEFICIARIES_DATA.keys()))

        submit_button = st.form_submit_button("Submit Request")

        if submit_button:
            if not item_description or not estimated_cost or not beneficiary_name:
                st.error("All fields are required.")
            else:
                opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])
                request_id = f"{request_type}-{len(opex_capex_requests) + 1:04d}"
                beneficiary_details = BENEFICIARIES_DATA.get(beneficiary_name, {})

                new_request = {
                    "request_id": request_id,
                    "employee_id": employee_id, # Tag with employee ID
                    "username": username, # Tag with username
                    "request_type": request_type,
                    "item_description": item_description,
                    "estimated_cost": estimated_cost,
                    "beneficiary_name": beneficiary_name,
                    "beneficiary_account_name": beneficiary_details.get("Account Name", ""),
                    "beneficiary_account_no": beneficiary_details.get("Account No", ""),
                    "beneficiary_bank": beneficiary_details.get("Bank", ""),
                    "submission_date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "Pending",
                    "approvals": {
                        "Finance Manager": {"status": "Pending", "date": None},
                        "Managing Director": {"status": "Pending", "date": None}
                    }
                }
                opex_capex_requests.append(new_request)
                save_data(opex_capex_requests, OPEX_CAPEX_REQUESTS_FILE)
                st.success(f"OPEX/CAPEX request {request_id} submitted successfully!")

                # Simulate email notification to Finance Manager
                finance_manager_email = APPROVAL_EMAILS.get("Finance Manager", "finance_manager@example.com")
                subject = f"New OPEX/CAPEX Request ({request_id}) from {username}"
                body = f"A new {request_type} request for '{item_description}' (Estimated Cost: NGN {estimated_cost:,.2f}) has been submitted by {username} (ID: {employee_id}). Please review."
                send_email_notification(finance_manager_email, subject, body)
                st.rerun()

def view_opex_capex_applications():
    st.subheader("View OPEX/CAPEX Applications")
    all_opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])

    if not all_opex_capex_requests:
        st.info("No OPEX/CAPEX applications available.")
        return

    # Filter based on role
    if st.session_state.role == "Employee":
        employee_id = st.session_state.user_profile.get('employee_id')
        filtered_requests = [req for req in all_opex_capex_requests if req.get('employee_id') == employee_id]
        if not filtered_requests:
            st.info("You have not submitted any OPEX/CAPEX requests.")
            return
        df = pd.DataFrame(filtered_requests)
        st.dataframe(df)

    elif st.session_state.role in ["Finance Manager", "Managing Director", "Admin Manager"]: # Admin can also view all
        df = pd.DataFrame(all_opex_capex_requests)

        # Basic filtering for managers
        filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
        if filter_status != "All":
            df = df[df['status'] == filter_status]

        if not df.empty:
            st.dataframe(df)

            # Approval/Rejection for Finance/MD
            if st.session_state.role in ["Finance Manager", "Managing Director"]:
                st.markdown("#### Action on OPEX/CAPEX Requests")
                selected_request_id = st.selectbox("Select Request ID to Action", df['request_id'].tolist())

                if selected_request_id:
                    request_to_action = next((req for req in all_opex_capex_requests if req['request_id'] == selected_request_id), None)
                    if request_to_action:
                        current_manager_role = st.session_state.role
                        approval_key = current_manager_role # Use role as key (e.g., "Finance Manager")

                        st.write(f"**Request ID:** {request_to_action['request_id']}")
                        st.write(f"**Employee:** {request_to_action['username']} (ID: {request_to_action['employee_id']})")
                        st.write(f"**Type:** {request_to_action['request_type']}")
                        st.write(f"**Description:** {request_to_action['item_description']}")
                        st.write(f"**Cost:** NGN {request_to_action['estimated_cost']:,.2f}")
                        st.write(f"**Beneficiary:** {request_to_action['beneficiary_name']}")
                        st.write(f"**Current Status:** {request_to_action['status']}")
                        st.write(f"**Finance Approval:** {request_to_action['approvals'].get('Finance Manager', {}).get('status', 'N/A')}")
                        st.write(f"**MD Approval:** {request_to_action['approvals'].get('Managing Director', {}).get('status', 'N/A')}")

                        if request_to_action['approvals'].get(approval_key, {}).get('status') == "Pending":
                            action = st.radio(f"Action for {current_manager_role}", ["None", "Approve", "Reject"], key=f"opex_capex_action_{selected_request_id}")
                            if action != "None":
                                if st.button(f"Confirm {action} for {selected_request_id}"):
                                    request_to_action['approvals'][approval_key]['status'] = action
                                    request_to_action['approvals'][approval_key]['date'] = datetime.now().strftime("%Y-%m-%d")

                                    # Check overall status
                                    finance_status = request_to_action['approvals'].get('Finance Manager', {}).get('status')
                                    md_status = request_to_action['approvals'].get('Managing Director', {}).get('status')

                                    if action == "Rejected":
                                        request_to_action['status'] = "Rejected" # Any rejection makes the whole request rejected
                                    elif finance_status == "Approved" and md_status == "Approved":
                                        request_to_action['status'] = "Approved"

                                    save_data(all_opex_capex_requests, OPEX_CAPEX_REQUESTS_FILE)
                                    st.success(f"OPEX/CAPEX request {selected_request_id} {action} by {current_manager_role}.")

                                    # Notify requesting employee
                                    employee_email = next((u['profile']['email'] for u in load_data(USERS_FILE, []) if u['employee_id'] == request_to_action['employee_id']), None)
                                    if employee_email:
                                        subject = f"Your OPEX/CAPEX Request ({selected_request_id}) Status Update"
                                        body = f"Your {request_to_action['request_type']} request for '{request_to_action['item_description']}' has been {request_to_action['status']} by {current_manager_role}."
                                        send_email_notification(employee_email, subject, body)
                                    st.rerun()
                        else:
                            st.info(f"This request has already been {request_to_action['approvals'].get(approval_key, {}).get('status', 'N/A')} by {current_manager_role}.")
                    else:
                        st.warning("Selected request not found.")
        else:
            st.info("No OPEX/CAPEX applications matching the filter.")

# --- Performance Goal Setting ---
def performance_goal_setting():
    st.subheader("Performance Goal Setting")
    user_goals = st.session_state.user_profile.get('performance_goals', []) # Get goals from logged-in user's data

    if 'edit_goal_index' not in st.session_state:
        st.session_state.edit_goal_index = None

    with st.form("goal_form"):
        st.markdown("#### Set New Goal")
        goal_title = st.text_input("Goal Title")
        goal_description = st.text_area("Description")
        target_date = st.date_input("Target Completion Date", datetime.today() + timedelta(days=90))
        metric = st.text_input("Key Metric (e.g., 'Increase sales by 10%')")
        weight = st.slider("Weight (1-100%)", 1, 100, 50)

        add_goal_button = st.form_submit_button("Add Goal")

        if add_goal_button:
            if not goal_title or not goal_description or not metric:
                st.error("Goal Title, Description, and Key Metric are required.")
            else:
                new_goal = {
                    "id": len(user_goals) + 1, # Simple ID generation
                    "title": goal_title,
                    "description": goal_description,
                    "target_date": str(target_date),
                    "metric": metric,
                    "weight": weight,
                    "status": "Pending", # Initial status
                    "progress": 0 # Initial progress
                }
                user_goals.append(new_goal)
                st.session_state.user_profile['performance_goals'] = user_goals # Update session state
                update_user_data(st.session_state.user_profile) # Save updated user data
                st.success("Goal added successfully!")
                st.rerun()

    st.markdown("---")
    st.markdown("#### Your Current Goals")
    if user_goals:
        goals_df = pd.DataFrame(user_goals)
        st.dataframe(goals_df)

        # Allow editing/deleting
        col_edit, col_delete = st.columns(2)
        with col_edit:
            goal_to_edit_id = st.selectbox("Select Goal ID to Edit", [g['id'] for g in user_goals], key="edit_select")
        with col_delete:
            goal_to_delete_id = st.selectbox("Select Goal ID to Delete", [g['id'] for g in user_goals], key="delete_select")

        if col_edit.button("Edit Selected Goal"):
            st.session_state.edit_goal_index = next((i for i, g in enumerate(user_goals) if g['id'] == goal_to_edit_id), None)
            if st.session_state.edit_goal_index is not None:
                st.rerun()
            else:
                st.warning("Goal not found for editing.")

        if col_delete.button("Delete Selected Goal"):
            user_goals = [g for g in user_goals if g['id'] != goal_to_delete_id]
            st.session_state.user_profile['performance_goals'] = user_goals # Update session state
            update_user_data(st.session_state.user_profile) # Save updated user data
            st.success(f"Goal {goal_to_delete_id} deleted.")
            st.rerun()

        if st.session_state.edit_goal_index is not None:
            st.markdown("#### Edit Goal")
            current_goal = user_goals[st.session_state.edit_goal_index]
            with st.form("edit_goal_form"):
                edited_title = st.text_input("Goal Title", value=current_goal['title'])
                edited_description = st.text_area("Description", value=current_goal['description'])
                edited_target_date = st.date_input("Target Completion Date", value=datetime.strptime(current_goal['target_date'], '%Y-%m-%d'))
                edited_metric = st.text_input("Key Metric", value=current_goal['metric'])
                edited_weight = st.slider("Weight (1-100%)", 1, 100, current_goal['weight'])
                edited_status = st.selectbox("Status", ["Pending", "In Progress", "Completed", "Cancelled"], index=["Pending", "In Progress", "Completed", "Cancelled"].index(current_goal['status']))
                edited_progress = st.slider("Progress (%)", 0, 100, current_goal['progress'])

                save_edit_button = st.form_submit_button("Save Changes")

                if save_edit_button:
                    if not edited_title or not edited_description or not edited_metric:
                        st.error("Goal Title, Description, and Key Metric are required.")
                    else:
                        user_goals[st.session_state.edit_goal_index] = {
                            "id": current_goal['id'],
                            "title": edited_title,
                            "description": edited_description,
                            "target_date": str(edited_target_date),
                            "metric": edited_metric,
                            "weight": edited_weight,
                            "status": edited_status,
                            "progress": edited_progress
                        }
                        st.session_state.user_profile['performance_goals'] = user_goals # Update session state
                        update_user_data(st.session_state.user_profile) # Save updated user data
                        st.success(f"Goal {current_goal['id']} updated successfully!")
                        st.session_state.edit_goal_index = None # Exit edit mode
                        st.rerun()
    else:
        st.info("No goals set yet.")

# --- Self Appraisal Functionality ---
def self_appraisal():
    st.subheader("Self-Appraisal Form")
    user_appraisal = st.session_state.user_profile.get('current_appraisal', {}) # Get appraisal from logged-in user's data
    user_goals = st.session_state.user_profile.get('performance_goals', []) # Get goals from logged-in user's data

    st.write(f"Appraisal for: **{st.session_state.user_profile.get('profile', {}).get('full_name', st.session_state.username)}** (ID: {st.session_state.user_profile.get('employee_id')})")

    with st.form("self_appraisal_form"):
        st.markdown("#### Performance Against Goals")
        goal_scores = {}
        for goal in user_goals:
            st.markdown(f"**Goal:** {goal['title']} (Weight: {goal['weight']}%)")
            st.write(f"Description: {goal['description']}")
            st.write(f"Metric: {goal['metric']}")
            score = st.slider(f"Self-Score for '{goal['title']}' (1-5)", 1, 5, value=user_appraisal.get(f"goal_score_{goal['id']}", 3), key=f"self_score_{goal['id']}")
            comments = st.text_area(f"Self-Comments on '{goal['title']}'", value=user_appraisal.get(f"goal_comments_{goal['id']}", ""), key=f"self_comments_{goal['id']}")
            goal_scores[f"goal_score_{goal['id']}"] = score
            goal_scores[f"goal_comments_{goal['id']}"] = comments

        st.markdown("#### Overall Self-Assessment")
        overall_strengths = st.text_area("Key Strengths", value=user_appraisal.get("overall_strengths", ""))
        overall_improvements = st.text_area("Areas for Improvement", value=user_appraisal.get("overall_improvements", ""))
        development_needs = st.text_area("Development Needs/Training Required", value=user_appraisal.get("development_needs", ""))
        achievements = st.text_area("Key Achievements This Period", value=user_appraisal.get("achievements", ""))

        submit_appraisal_button = st.form_submit_button("Submit Self-Appraisal")

        if submit_appraisal_button:
            # Calculate weighted score (simplified example)
            total_weighted_score = 0
            total_weight = sum(goal['weight'] for goal in user_goals)
            if total_weight > 0:
                for goal in user_goals:
                    score = goal_scores.get(f"goal_score_{goal['id']}", 0)
                    total_weighted_score += (score * goal['weight'])
                overall_score = total_weighted_score / total_weight
            else:
                overall_score = 0 # No goals set

            appraisal_data = {
                "appraisal_date": datetime.now().strftime("%Y-%m-%d"),
                "employee_id": st.session_state.user_profile.get('employee_id'),
                "employee_name": st.session_state.user_profile.get('profile', {}).get('full_name', st.session_state.username),
                "goals_assessment": goal_scores,
                "overall_strengths": overall_strengths,
                "overall_improvements": overall_improvements,
                "development_needs": development_needs,
                "achievements": achievements,
                "overall_self_score": round(overall_score, 2),
                "status": "Submitted by Employee", # Status for review by manager
                "line_manager_comments": user_appraisal.get("line_manager_comments", ""),
                "line_manager_score": user_appraisal.get("line_manager_score", 0)
            }
            st.session_state.user_profile['current_appraisal'] = appraisal_data # Update session state
            update_user_data(st.session_state.user_profile) # Save updated user data
            st.success("Self-Appraisal submitted successfully!")
            st.rerun()
    else:
        st.info("Fill out the form above to submit your self-appraisal.")

def line_manager_appraisal():
    st.subheader("Line Manager Appraisal")

    all_users = load_data(USERS_FILE, [])
    # Filter users based on your role, e.g., managers appraise their direct reports
    # For simplicity, Admin/HR/MD can appraise any employee here.
    appraisable_employees = [user for user in all_users if user['role'] == "Employee"]

    if not appraisable_employees:
        st.info("No employees to appraise.")
        return

    selected_employee_username = st.selectbox(
        "Select Employee to Appraise",
        [user['username'] for user in appraisable_employees]
    )

    selected_employee_user = next((user for user in appraisable_employees if user['username'] == selected_employee_username), None)

    if selected_employee_user:
        employee_appraisal = selected_employee_user.get('current_appraisal', {})
        employee_goals = selected_employee_user.get('performance_goals', [])
        employee_full_name = selected_employee_user.get('profile', {}).get('full_name', selected_employee_username)

        st.write(f"Appraising: **{employee_full_name}** (ID: {selected_employee_user.get('employee_id')})")
        st.write(f"Last Self-Appraisal Date: {employee_appraisal.get('appraisal_date', 'N/A')}")

        with st.form(f"line_manager_appraisal_form_{selected_employee_username}"):
            st.markdown("#### Employee's Self-Assessment (Read-Only)")
            st.json(employee_appraisal) # Display employee's self-assessment as JSON for review

            st.markdown("#### Line Manager's Assessment")
            manager_goal_scores = {}
            for goal in employee_goals:
                st.markdown(f"**Goal:** {goal['title']} (Weight: {goal['weight']}%)")
                st.write(f"Employee's Self-Score: {employee_appraisal.get(f'goal_score_{goal['id']}', 'N/A')}")
                st.write(f"Employee's Self-Comments: {employee_appraisal.get(f'goal_comments_{goal['id']}', 'N/A')}")
                
                score = st.slider(f"Manager's Score for '{goal['title']}' (1-5)", 1, 5, value=employee_appraisal.get(f"line_manager_goal_score_{goal['id']}", 3), key=f"manager_score_{selected_employee_username}_{goal['id']}")
                comments = st.text_area(f"Manager's Comments on '{goal['title']}'", value=employee_appraisal.get(f"line_manager_goal_comments_{goal['id']}", ""), key=f"manager_comments_{selected_employee_username}_{goal['id']}")
                manager_goal_scores[f"line_manager_goal_score_{goal['id']}"] = score
                manager_goal_scores[f"line_manager_goal_comments_{goal['id']}"] = comments

            line_manager_overall_comments = st.text_area("Overall Line Manager Comments", value=employee_appraisal.get("line_manager_comments", ""))
            line_manager_overall_score = st.slider("Overall Line Manager Score (1-5)", 1, 5, value=employee_appraisal.get("line_manager_score", 3))

            submit_manager_appraisal_button = st.form_submit_button("Submit Manager Appraisal")

            if submit_manager_appraisal_button:
                # Calculate weighted score (simplified example)
                total_weighted_score = 0
                total_weight = sum(goal['weight'] for goal in employee_goals)
                if total_weight > 0:
                    for goal in employee_goals:
                        score = manager_goal_scores.get(f"line_manager_goal_score_{goal['id']}", 0)
                        total_weighted_score += (score * goal['weight'])
                    overall_manager_score = total_weighted_score / total_weight
                else:
                    overall_manager_score = 0 # No goals set

                # Update the employee's appraisal data within their user object
                employee_appraisal.update({
                    "line_manager_comments": line_manager_overall_comments,
                    "line_manager_score": line_manager_overall_score,
                    "manager_appraisal_date": datetime.now().strftime("%Y-%m-%d"),
                    "status": "Appraised by Manager",
                    "manager_goal_assessments": manager_goal_scores,
                    "overall_manager_weighted_score": round(overall_manager_score, 2)
                })

                # Update the selected employee's user data in all_users list
                selected_employee_user['current_appraisal'] = employee_appraisal
                update_user_data(selected_employee_user) # Save updated user data

                st.success(f"Appraisal for {employee_full_name} submitted successfully!")
                st.rerun()
    else:
        st.info("Select an employee to view/submit their appraisal.")

def download_appraisal_pdf():
    st.subheader("Download Appraisal PDF")
    
    all_users = load_data(USERS_FILE, [])
    # Filter users based on your role, e.g., managers can download for their reports
    downloadable_employees = [user for user in all_users if user['role'] == "Employee"] # Assuming managers can download for employees

    selected_employee_username = st.selectbox(
        "Select Employee to Download Appraisal",
        [user['username'] for user in downloadable_employees]
    )

    selected_employee_user = next((user for user in downloadable_employees if user['username'] == selected_employee_username), None)

    if selected_employee_user and selected_employee_user.get('current_appraisal'):
        employee_appraisal = selected_employee_user['current_appraisal']
        employee_profile = selected_employee_user['profile']
        employee_goals = selected_employee_user['performance_goals']

        st.write(f"Generating PDF for {employee_profile.get('full_name', selected_employee_username)}")

        if st.button("Generate PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, txt="Performance Appraisal Report", ln=True, align="C")
            pdf.ln(10)

            pdf.set_font("Arial", style='B', size=10)
            pdf.cell(0, 10, "Employee Information:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 5, f"Full Name: {employee_profile.get('full_name', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Employee ID: {employee_profile.get('employee_id', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Department: {employee_profile.get('department', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Position: {employee_profile.get('position', 'N/A')}", ln=True)
            pdf.ln(5)

            pdf.set_font("Arial", style='B', size=10)
            pdf.cell(0, 10, "Appraisal Details:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 5, f"Appraisal Date: {employee_appraisal.get('appraisal_date', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Manager Appraisal Date: {employee_appraisal.get('manager_appraisal_date', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Status: {employee_appraisal.get('status', 'N/A')}", ln=True)
            pdf.ln(5)

            pdf.set_font("Arial", style='B', size=10)
            pdf.cell(0, 10, "Performance Goals Assessment:", ln=True)
            pdf.set_font("Arial", size=10)
            for goal in employee_goals:
                pdf.cell(0, 5, f"Goal: {goal['title']}", ln=True)
                pdf.cell(0, 5, f" - Description: {goal['description']}", ln=True)
                pdf.cell(0, 5, f" - Employee Self-Score: {employee_appraisal.get(f'goal_score_{goal['id']}', 'N/A')}", ln=True)
                pdf.multi_cell(0, 5, f" - Employee Comments: {employee_appraisal.get(f'goal_comments_{goal['id']}', 'N/A')}")
                pdf.cell(0, 5, f" - Manager Score: {employee_appraisal.get(f'line_manager_goal_score_{goal['id']}', 'N/A')}", ln=True)
                pdf.multi_cell(0, 5, f" - Manager Comments: {employee_appraisal.get(f'line_manager_goal_comments_{goal['id']}', 'N/A')}")
                pdf.ln(2)

            pdf.set_font("Arial", style='B', size=10)
            pdf.cell(0, 10, "Overall Assessment:", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, f"Key Strengths: {employee_appraisal.get('overall_strengths', 'N/A')}")
            pdf.multi_cell(0, 5, f"Areas for Improvement: {employee_appraisal.get('overall_improvements', 'N/A')}")
            pdf.multi_cell(0, 5, f"Development Needs: {employee_appraisal.get('development_needs', 'N/A')}")
            pdf.multi_cell(0, 5, f"Key Achievements: {employee_appraisal.get('achievements', 'N/A')}")
            pdf.cell(0, 5, f"Overall Self-Score: {employee_appraisal.get('overall_self_score', 'N/A')}", ln=True)
            pdf.cell(0, 5, f"Overall Manager Score: {employee_appraisal.get('line_manager_score', 'N/A')}", ln=True)
            pdf.multi_cell(0, 5, f"Overall Manager Comments: {employee_appraisal.get('line_manager_comments', 'N/A')}")

            pdf_output = pdf.output(dest='S').encode('latin-1')
            b64 = base64.b64encode(pdf_output).decode('latin-1')
            download_link = f'<a href="data:application/pdf;base64,{b64}" download="Appraisal_Report_{employee_profile.get("employee_id", "N/A")}.pdf">Download PDF Report</a>'
            st.markdown(download_link, unsafe_allow_html=True)
    elif selected_employee_user:
        st.info(f"No appraisal data available for {selected_employee_username}.")
    else:
        st.info("Select an employee to download their appraisal.")


# --- Main Application Logic ---

def main():
    st.set_page_config(page_title="Polaris Digitech HR System", layout="wide", initial_sidebar_state="expanded")

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = ""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
    if "user_profile" not in st.session_state:
        st.session_state.user_profile = {} # Store the full user object here

    # New: Call this once at the very beginning to ensure users.json exists
    initialize_users_data()

    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar for navigation
        st.sidebar.image(LOGO_PATH, width=200)
        st.sidebar.title("Navigation")
        st.sidebar.markdown(f"**Welcome, {st.session_state.username}!**")
        st.sidebar.markdown(f"Role: **{st.session_state.role}**")
        st.sidebar.markdown("---")

        menu_items = {
            "Employee": ["Dashboard", "My Profile", "Leave Request", "My Leave Applications", "OPEX/CAPEX Request", "My OPEX/CAPEX Applications", "Performance Goal Setting", "Self-Appraisal"],
            "HR Manager": ["Dashboard", "My Profile", "View Leave Applications", "Performance Goal Setting", "Self-Appraisal", "Line Manager Appraisal", "Download Appraisal PDF"],
            "Finance Manager": ["Dashboard", "My Profile", "View OPEX/CAPEX Applications"],
            "Admin Manager": ["Dashboard", "My Profile", "View Leave Applications", "View OPEX/CAPEX Applications", "Performance Goal Setting", "Self-Appraisal", "Line Manager Appraisal", "Download Appraisal PDF"],
            "Managing Director": ["Dashboard", "My Profile", "View Leave Applications", "View OPEX/CAPEX Applications", "Line Manager Appraisal", "Download Appraisal PDF"]
        }

        # Filter menu items based on user role
        role_specific_menu = menu_items.get(st.session_state.role, ["Dashboard"])

        for item in role_specific_menu:
            if st.sidebar.button(item):
                # Map button text to internal page state
                if item == "Dashboard": st.session_state.current_page = "dashboard"
                elif item == "My Profile": st.session_state.current_page = "my_profile"
                elif item == "Leave Request": st.session_state.current_page = "leave_request"
                elif item == "My Leave Applications": st.session_state.current_page = "view_leave_applications"
                elif item == "View Leave Applications": st.session_state.current_page = "view_leave_applications" # Managers
                elif item == "OPEX/CAPEX Request": st.session_state.current_page = "opex_capex_form"
                elif item == "My OPEX/CAPEX Applications": st.session_state.current_page = "view_opex_capex_applications"
                elif item == "View OPEX/CAPEX Applications": st.session_state.current_page = "view_opex_capex_applications" # Managers
                elif item == "Performance Goal Setting": st.session_state.current_page = "performance_goal_setting"
                elif item == "Self-Appraisal": st.session_state.current_page = "self_appraisal"
                elif item == "Line Manager Appraisal": st.session_state.current_page = "line_manager_appraisal"
                elif item == "Download Appraisal PDF": st.session_state.current_page = "download_appraisal_pdf"
                st.rerun()

        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.current_page = "login"
            st.session_state.user_profile = {} # Clear user-specific data on logout
            st.session_state.edit_goal_index = None
            st.rerun()

        # Display the selected page content
        if st.session_state.current_page == "dashboard":
            display_dashboard()
        elif st.session_state.current_page == "my_profile":
            display_profile_management()
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
        elif st.session_state.current_page == "self_appraisal":
            self_appraisal()
        elif st.session_state.current_page == "line_manager_appraisal":
            line_manager_appraisal()
        elif st.session_state.current_page == "download_appraisal_pdf":
            download_appraisal_pdf()

if __name__ == "__main__":
    main()
