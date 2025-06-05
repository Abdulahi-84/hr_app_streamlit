import streamlit as st
import json
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import base64
import bcrypt # New: For password hashing
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration & Paths ---
# For deployment, assume images are in the same directory as the app
# Ensure these image files (polaris_digitech_logo.png, abdulahi_image.png) are in the same directory as hr_app.py
LOGO_FILE_NAME = "polaris_digitech_logo.png"
LOGO_PATH = LOGO_FILE_NAME # Now directly refers to the file in the same directory

ABDULAHI_IMAGE_FILE_NAME = "abdulahi_image.png"
ABDULAHI_IMAGE_PATH = ABDULAHI_IMAGE_FILE_NAME

# --- Data Files ---
USERS_FILE = "users.json" # New: File for all user accounts
LEAVE_REQUESTS_FILE = "leave_requests.json"
OPEX_CAPEX_REQUESTS_FILE = "opex_capex_requests.json"
PERFORMANCE_GOALS_FILE = "performance_goals.json"
CURRENT_APPRAISAL_FILE = "current_appraisal.json"

# --- Define Approval Route Emails (For Simulated Notifications) ---
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
    "Emmafem Resources Nig. Ent.": {"Account Name": "Emmafem", "Account No": "3456789012", "Bank": "First Bank"},
    "S.O.G Int'l Services": {"Account Name": "S.O.G", "Account No": "4567890123", "Bank": "Zenith Bank"},
    "Abbas & Co. Ltd": {"Account Name": "Abbas", "Account No": "5678901234", "Bank": "UBA"},
    "Prime Ventures": {"Account Name": "Prime", "Account No": "6789012345", "Bank": "Access Bank"}
}

# --- Utility Functions ---
def load_data(file_path, default_value=None):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                st.warning(f"Error decoding JSON from {file_path}. Returning default value.")
                return default_value
    return default_value

def save_data(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def calculate_leave_balance(employee_id, leave_requests):
    # For simplicity, assume all employees start with 20 days annual leave
    # You might want to store this in user_profile or a more sophisticated system
    total_annual_leave_days = 20
    leave_taken = 0
    for req in leave_requests:
        if req["employee_id"] == employee_id and req["status"] == "Approved":
            start_date = datetime.strptime(req["start_date"], '%Y-%m-%d').date()
            end_date = datetime.strptime(req["end_date"], '%Y-%m-%d').date()
            leave_taken += (end_date - start_date).days + 1 # Include start and end day

    return total_annual_leave_days - leave_taken

# --- Password Hashing Utilities (New) ---
def hash_password(password):
    """Hashes a password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    """Checks if a plain password matches a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- User Initialization (Run once to create initial users.json) ---
def initialize_users_data():
    if not os.path.exists(USERS_FILE):
        st.info("No users file found. Initializing with default admin and manager accounts.")
        initial_users = [
            {
                "username": "admin",
                "password_hash": hash_password("admin_password_123"), # **CHANGE THIS IN PRODUCTION**
                "role": "Admin Manager",
                "name": "Admin Polaris",
                "employee_id": "ADM000",
                "department": "IT",
                "phone_number": "00000000000",
                "email_address": APPROVAL_EMAILS["Admin Manager"]
            },
            {
                "username": "finance",
                "password_hash": hash_password("finance_password_123"), # **CHANGE THIS IN PRODUCTION**
                "role": "Finance Manager",
                "name": "Finance Manager Polaris",
                "employee_id": "FIN001",
                "department": "Finance",
                "phone_number": "08033334444",
                "email_address": APPROVAL_EMAILS["Finance Manager"]
            },
            {
                "username": "hr",
                "password_hash": hash_password("hr_password_123"), # **CHANGE THIS IN PRODUCTION**
                "role": "HR Manager",
                "name": "HR Manager Polaris",
                "employee_id": "HRM001",
                "department": "Human Resources",
                "phone_number": "08055556666",
                "email_address": APPROVAL_EMAILS["HR Manager"]
            },
            {
                "username": "md",
                "password_hash": hash_password("md_password_123"), # **CHANGE THIS IN PRODUCTION**
                "role": "Managing Director",
                "name": "Managing Director Polaris",
                "employee_id": "MD001",
                "department": "Executive",
                "phone_number": "08077778888",
                "email_address": APPROVAL_EMAILS["Managing Director"]
            },
            {
                "username": "employee",
                "password_hash": hash_password("employee_password_123"), # **CHANGE THIS IN PRODUCTION**
                "role": "Employee",
                "name": "Generic Employee",
                "employee_id": "EMP002",
                "department": "Operations",
                "phone_number": "07012345678",
                "email_address": "employee@example.com"
            }
        ]
        save_data(initial_users, USERS_FILE)
        st.success("Initial users created.")

# --- Email Sending Function ---
def send_email_notification(recipient_email, subject, body):
    try:
        sender_email = st.secrets["EMAIL_SENDER_ADDRESS"]
        sender_password = st.secrets["EMAIL_SENDER_PASSWORD"]
        smtp_server = st.secrets["SMTP_SERVER"]
        smtp_port = st.secrets["SMTP_PORT"]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade to a secure connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email to {recipient_email}: {e}")
        return False

# --- PDF Generation Functions ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None

def generate_leave_pdf(leave_request_data, user_profile):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    pdf.set_text_color(30, 144, 255) # Polaris Blue
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Polaris Digitech - Leave Request", align="C", ln=True)
    pdf.set_text_color(0, 0, 0) # Reset to black

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
    pdf.cell(0, 10, "Leave Request Details:", ln=True)
    pdf.set_font("Helvetica", '', 10)

    # Exclude certain keys that are handled separately or not needed in the main list
    exclude_keys = ["employee_id", "status", "leave_type_other"]

    for key, value in leave_request_data.items():
        if key not in exclude_keys:
            if key in ["start_date", "end_date", "submission_date"] and value:
                try:
                    value = datetime.strptime(value, '%Y-%m-%d').strftime('%B %d, %Y')
                except ValueError:
                    pass # value remains as is, might be string if not datetime
            display_key = key.replace('_', ' ').title()
            pdf.cell(0, 7, f"{display_key}: {value}", ln=True)

    # Add the custom "other" leave type if applicable
    if leave_request_data.get("leave_type") == "Other" and leave_request_data.get("leave_type_other"):
        pdf.cell(0, 7, f"Other Leave Type: {leave_request_data['leave_type_other']}", ln=True)

    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Approval Status:", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 7, f"Status: {leave_request_data.get('status', 'Pending')}", ln=True)

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
        "uploaded_document_path", "amount_requested"
    ]

    # Manually add the itemized costs first for clarity
    pdf.cell(0, 7, f"Title: {request_data.get('title', 'N/A')}", ln=True)
    pdf.multi_cell(0, 7, f"Details: {request_data.get('details', 'N/A')}")
    pdf.cell(0, 7, f"Beneficiary: {request_data.get('beneficiaries', 'N/A')}", ln=True)

    pdf.ln(2)
    pdf.set_font("Helvetica", 'BU', 10)
    pdf.cell(0, 7, "Cost Breakdown:", ln=True)
    pdf.set_font("Helvetica", '', 10)

    # Explicitly cast values to float before formatting to prevent TypeError from non-numeric strings
    try:
        materials_cost_val = float(request_data.get('materials_cost', 0.0))
    except (ValueError, TypeError):
        materials_cost_val = 0.0
        st.warning(f"Invalid 'materials_cost' value in request_data: {request_data.get('materials_cost')}. Defaulting to 0.0.")
    try:
        labour_cost_val = float(request_data.get('labour_cost', 0.0))
    except (ValueError, TypeError):
        labour_cost_val = 0.0
        st.warning(f"Invalid 'labour_cost' value in request_data: {request_data.get('labour_cost')}. Defaulting to 0.0.")

    wht_percentage_val = request_data.get('wht_percentage', 'None') # This is a string, no float conversion needed

    try:
        wht_amount_val = float(request_data.get('wht_amount', 0.0))
    except (ValueError, TypeError):
        wht_amount_val = 0.0
        st.warning(f"Invalid 'wht_amount' value in request_data: {request_data.get('wht_amount')}. Defaulting to 0.0.")
    try:
        net_labour_cost_val = float(request_data.get('net_labour_cost', 0.0))
    except (ValueError, TypeError):
        net_labour_cost_val = 0.0
        st.warning(f"Invalid 'net_labour_cost' value in request_data: {request_data.get('net_labour_cost')}. Defaulting to 0.0.")
    try:
        net_amount_requested_val = float(request_data.get('net_amount_requested', 0.0))
    except (ValueError, TypeError):
        net_amount_requested_val = 0.0
        st.warning(f"Invalid 'net_amount_requested' value in request_data: {request_data.get('net_amount_requested')}. Defaulting to 0.0.")
    try:
        amount_budgeted_val = float(request_data.get('amount_budgeted', 0.0))
    except (ValueError, TypeError):
        amount_budgeted_val = 0.0
        st.warning(f"Invalid 'amount_budgeted' value in request_data: {request_data.get('amount_budgeted')}. Defaulting to 0.0.")
    try:
        budget_balance_val = float(request_data.get('budget_balance', 0.0))
    except (ValueError, TypeError):
        budget_balance_val = 0.0
        st.warning(f"Invalid 'budget_balance' value in request_data: {request_data.get('budget_balance')}. Defaulting to 0.0.")


    pdf.cell(0, 7, f"Materials Cost: {materials_cost_val:,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Labour/Services Cost: {labour_cost_val:,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Withholding Tax (%): {wht_percentage_val}", ln=True)
    pdf.cell(0, 7, f"Withholding Tax Amount: {wht_amount_val:,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Net Labour/Services Cost: {net_labour_cost_val:,.2f} NGN", ln=True)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 7, f"Total Net Amount Requested: {net_amount_requested_val:,.2f} NGN", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 7, f"Amount Budgeted: {amount_budgeted_val:,.2f} NGN", ln=True)
    pdf.cell(0, 7, f"Budget Balance: {budget_balance_val:,.2f} NGN", ln=True)
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
            "beneficiaries", "account_name", "account_no", "bank", "requisition_type",
            "submitted_date" # Handled separately below if not done already
        ]: # Ensure we don't duplicate already printed fields
            # Attempt to format date fields if they look like dates
            if "_date" in key and value:
                try:
                    # Try common date formats
                    dt_obj = None
                    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y'):
                        try:
                            dt_obj = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                    if dt_obj:
                        value = dt_obj.strftime('%B %d, %Y')
                except Exception:
                    pass # Keep original value if conversion fails

            display_key = key.replace('_', ' ').title()
            pdf.cell(0, 7, f"{display_key}: {value}", ln=True)

    # Ensure submitted_date is always printed, even if not covered by the loop above
    if "submitted_date" in request_data and request_data["submitted_date"]:
        display_date = request_data["submitted_date"]
        try:
            display_date = datetime.strptime(display_date, '%Y-%m-%d').strftime('%B %d, %Y')
        except ValueError:
            pass
        pdf.cell(0, 7, f"Submitted Date: {display_date}", ln=True)


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

    # Before output, print the data to Streamlit logs for debugging
    # This will show up in "Manage App -> Logs" on Streamlit Cloud if deployed
    print(f"DEBUG: Data used for PDF generation: {json.dumps(request_data, indent=2)}")
    print(f"DEBUG: User profile used for PDF generation: {json.dumps(user_profile, indent=2)}")

    try:
        return bytes(pdf.output(dest='S'))
    except Exception as e:
        st.error(f"An error occurred during PDF generation: {e}")
        st.info("Please check the Streamlit Cloud logs for full details of the `request_data` and `user_profile` that caused the error.")
        # Re-raise the exception to see it in Streamlit Cloud logs more clearly
        raise


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
    pdf.cell(0, 7, f"Employee ID: {user_profile.get('employee_id', 'N/A')}", ln=True)
    pdf.cell(0, 7, f"Appraisal Period: {appraisal_data.get('appraisal_period', 'N/A')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Goals & Self-Appraisal:", ln=True)
    pdf.set_font("Helvetica", '', 10)

    total_weighted_self_score = 0
    total_weighted_supervisor_score = 0
    total_weight = 0

    for i, goal in enumerate(appraisal_data.get('goals', [])):
        pdf.set_font("Helvetica", 'BU', 10)
        pdf.cell(0, 7, f"Goal {i+1}: {goal.get('goal_name', 'N/A')}", ln=True)
        pdf.set_font("Helvetica", '', 10)
        pdf.multi_cell(0, 7, f"Description: {goal.get('description', 'N/A')}")

        weight = goal.get('weight_self_rating', 0)
        self_score = goal.get('self_appraisal_score', 0) or 0
        supervisor_score = goal.get('line_managers_rating', 0) or 0 # Corrected key
        comments = goal.get('self_appraisal_comments', 'N/A')

        pdf.cell(0, 7, f"Weight: {weight}", ln=True)
        pdf.cell(0, 7, f"Self-Appraisal Score (1-5): {self_score}", ln=True)
        pdf.multi_cell(0, 7, f"Self-Appraisal Comments: {comments}")
        pdf.cell(0, 7, f"Line Manager's Rating (1-5): {supervisor_score}", ln=True)
        pdf.ln(2)

        # Calculate weighted scores
        try:
            total_weighted_self_score += (float(self_score) * float(weight))
            total_weighted_supervisor_score += (float(supervisor_score) * float(weight))
            total_weight += float(weight)
        except ValueError:
            st.warning(f"Non-numeric score or weight found for goal {i+1}. Skipping for overall calculation.")


    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Overall Appraisal Scores:", ln=True)
    pdf.set_font("Helvetica", '', 10)

    overall_self_score_0_5 = 0.0
    overall_supervisor_score_0_5 = 0.0

    if total_weight > 0:
        overall_self_score_0_5 = (total_weighted_self_score / total_weight) * 5
        overall_supervisor_score_0_5 = (total_weighted_supervisor_score / total_weight) * 5 # Scale to 0-5

    pdf.cell(0, 7, f"Overall Self-Appraisal Score (0-5): {overall_self_score_0_5:,.2f}", ln=True)
    pdf.cell(0, 7, f"Overall Supervisor's Score (0-5): {overall_supervisor_score_0_5:,.2f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Development Areas & Training Needs:", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 7, appraisal_data.get('development_areas', 'N/A'))
    pdf.multi_cell(0, 7, appraisal_data.get('training_needs', 'N/A'))
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "Comments & Signatures:", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 7, f"Employee Comments: {appraisal_data.get('employee_comments', 'N/A')}")
    pdf.multi_cell(0, 7, f"Line Manager's Comments: {appraisal_data.get('line_managers_comments', 'N/A')}")
    pdf.ln(10)

    pdf.set_font("Helvetica", 'I', 9)
    pdf.cell(0, 5, "This is an electronically generated document and does not require a signature.", align="C")

    try:
        return bytes(pdf.output(dest='S'))
    except Exception as e:
        st.error(f"An error occurred during PDF generation: {e}")
        st.info("Please check the Streamlit Cloud logs for full details of the `appraisal_data` and `user_profile` that caused the error.")
        raise


# --- Page Functions ---

# Dashboard Page
def display_dashboard():
    st.title(f"Welcome, {st.session_state.user_profile.get('name', st.session_state.username).title()}!")

    # Load and display Polaris Digitech Logo
    logo_base64 = get_image_base64(LOGO_PATH)
    if logo_base64:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/png;base64,{logo_base64}" style="max-width: 200px; height: auto;">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Polaris Digitech logo not found. Please ensure 'polaris_digitech_logo.png' is in the app directory.")

    st.header("HR Dashboard Overview")

    # Display user profile information
    st.subheader("Your Profile")
    profile_data = {
        "Employee ID": st.session_state.user_profile.get('employee_id', 'N/A'),
        "Role": st.session_state.user_role,
        "Department": st.session_state.user_profile.get('department', 'N/A'),
        "Email": st.session_state.user_profile.get('email_address', 'N/A'),
        "Phone": st.session_state.user_profile.get('phone_number', 'N/A')
    }
    st.json(profile_data)

    # Quick Stats (can be expanded)
    st.subheader("Quick Stats")
    col1, col2 = st.columns(2)

    # Leave balance
    employee_id = st.session_state.user_profile.get('employee_id')
    current_leave_balance = 0
    if employee_id:
        current_leave_balance = calculate_leave_balance(employee_id, st.session_state.leave_requests)

    col1.metric("Current Leave Balance", f"{current_leave_balance} Days")

    # Pending Opex/Capex for the current user
    user_pending_opex_capex = [
        req for req in st.session_state.opex_capex_requests
        if req.get("employee_id") == employee_id and
           (req.get("status_admin") == "Pending" or
            req.get("status_finance") == "Pending" or
            req.get("status_hr") == "Pending" or
            req.get("status_md") == "Pending")
    ]
    col2.metric("Pending Requisitions", len(user_pending_opex_capex))

    # General system stats (for Admin/HR roles)
    if st.session_state.user_role in ["Admin Manager", "HR Manager"]:
        st.subheader("System-Wide Statistics")
        total_employees = len(load_data(USERS_FILE, [])) - 1 # Assuming one admin account
        st.write(f"Total Registered Employees: {total_employees}")

        total_pending_leave = len([req for req in st.session_state.leave_requests if req["status"] == "Pending"])
        st.write(f"Total Pending Leave Requests: {total_pending_leave}")

        total_pending_opex_capex = len([
            req for req in st.session_state.opex_capex_requests
            if req.get("status_admin") == "Pending" or req.get("status_finance") == "Pending" or \
               req.get("status_hr") == "Pending" or req.get("status_md") == "Pending"
        ])
        st.write(f"Total Pending Opex/Capex Requests: {total_pending_opex_capex}")

        # Basic chart for leave requests by type
        leave_df = pd.DataFrame(st.session_state.leave_requests)
        if not leave_df.empty:
            leave_type_counts = leave_df["leave_type"].value_counts().reset_index()
            leave_type_counts.columns = ["Leave Type", "Count"]
            fig = px.pie(leave_type_counts, values="Count", names="Leave Type",
                         title="Leave Requests by Type",
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig)

        # Basic chart for opex/capex requests by type
        opex_capex_df = pd.DataFrame(st.session_state.opex_capex_requests)
        if not opex_capex_df.empty:
            req_type_counts = opex_capex_df["requisition_type"].value_counts().reset_index()
            req_type_counts.columns = ["Requisition Type", "Count"]
            fig2 = px.bar(req_type_counts, x="Requisition Type", y="Count",
                          title="Opex/Capex Requisitions by Type",
                          color="Requisition Type",
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2)


# Leave Request Form Page
def leave_request_form():
    st.title("Submit Leave Request")

    leave_types = ["Annual Leave", "Sick Leave", "Maternity Leave", "Paternity Leave", "Study Leave", "Other"]
    leave_type = st.selectbox("Leave Type", leave_types)

    other_leave_type = ""
    if leave_type == "Other":
        other_leave_type = st.text_input("Please specify 'Other' Leave Type")

    start_date = st.date_input("Start Date", datetime.now())
    end_date = st.date_input("End Date", datetime.now() + timedelta(days=7))

    reason = st.text_area("Reason for Leave")

    if st.button("Submit Leave Request"):
        if end_date < start_date:
            st.error("End date cannot be before start date.")
        elif not reason:
            st.error("Please provide a reason for your leave.")
        elif leave_type == "Other" and not other_leave_type:
            st.error("Please specify the 'Other' leave type.")
        else:
            total_days_requested = (end_date - start_date).days + 1
            employee_id = st.session_state.user_profile.get('employee_id')
            current_leave_balance = calculate_leave_balance(employee_id, st.session_state.leave_requests)

            if total_days_requested > current_leave_balance and leave_type == "Annual Leave":
                st.warning(f"You are requesting {total_days_requested} days, but only have {current_leave_balance} annual leave days remaining.")
                if not st.checkbox("Proceed anyway (may require special approval)?"):
                    st.stop()

            leave_request = {
                "employee_id": employee_id,
                "name": st.session_state.user_profile.get('name'),
                "leave_type": leave_type,
                "leave_type_other": other_leave_type if leave_type == "Other" else "",
                "start_date": str(start_date),
                "end_date": str(end_date),
                "total_days_requested": total_days_requested,
                "reason": reason,
                "submission_date": str(datetime.now().date()),
                "status": "Pending" # All new requests are pending initially
            }
            st.session_state.leave_requests.append(leave_request)
            save_data(st.session_state.leave_requests, LEAVE_REQUESTS_FILE)
            st.success("Leave request submitted successfully!")
            st.session_state.current_page = "view_leave_applications"
            st.rerun()

# View Leave Applications Page
def view_leave_applications():
    st.title("View Leave Applications")

    if not st.session_state.leave_requests:
        st.info("No leave applications submitted yet.")
        return

    # Filter requests based on user role
    if st.session_state.user_role == "Employee":
        display_requests = [
            req for req in st.session_state.leave_requests
            if req["employee_id"] == st.session_state.user_profile.get('employee_id')
        ]
    elif st.session_state.user_role in ["Admin Manager", "HR Manager"]:
        display_requests = st.session_state.leave_requests
    else: # Other managers might see relevant requests, or no access
        st.warning("You do not have permission to view all leave applications.")
        display_requests = [] # No requests to display

    if not display_requests:
        st.info("No relevant leave applications to display.")
        return

    df = pd.DataFrame(display_requests)
    df_display = df.copy()

    # Format dates for display
    df_display['start_date'] = pd.to_datetime(df_display['start_date']).dt.strftime('%Y-%m-%d')
    df_display['end_date'] = pd.to_datetime(df_display['end_date']).dt.strftime('%Y-%m-%d')
    df_display['submission_date'] = pd.to_datetime(df_display['submission_date']).dt.strftime('%Y-%m-%d')

    st.dataframe(df_display, use_container_width=True)

    if st.session_state.user_role in ["Admin Manager", "HR Manager"]:
        st.subheader("Manage Applications")
        application_titles = [f"{req.get('name', 'N/A')} - {req.get('leave_type')} ({req.get('submission_date')})"
                              for req in display_requests]
        selected_application_index = st.selectbox("Select an application to manage", range(len(display_requests)),
                                                    format_func=lambda x: application_titles[x] if x is not None else "")

        if selected_application_index is not None:
            selected_request = display_requests[selected_application_index]
            st.write("---")
            st.subheader(f"Details for {selected_request.get('name', 'N/A')}'s {selected_request.get('leave_type')} Leave")
            st.json(selected_request)

            col1, col2, col3 = st.columns(3)
            current_status = selected_request.get('status', 'Pending')

            st.write(f"Current Status: **{current_status}**")

            if col1.button("Approve", key=f"approve_{selected_application_index}"):
                if current_status != "Approved":
                    selected_request["status"] = "Approved"
                    # Find the original request in session_state.leave_requests and update it
                    for i, req in enumerate(st.session_state.leave_requests):
                        if req == selected_request: # This simple comparison works if requests are unique
                            st.session_state.leave_requests[i] = selected_request
                            break
                    save_data(st.session_state.leave_requests, LEAVE_REQUESTS_FILE)
                    st.success("Leave request approved!")
                    # Send email notification to employee
                    employee_email = selected_request.get('email_address') # Assuming email is in request data
                    if not employee_email: # Fallback to user_profile if email not in request (e.g., old data)
                        all_users = load_data(USERS_FILE, [])
                        for user in all_users:
                            if user.get('employee_id') == selected_request.get('employee_id'):
                                employee_email = user.get('email_address')
                                break
                    if employee_email:
                        email_subject = f"Your Leave Request for {selected_request['leave_type']} has been Approved"
                        email_body = f"""
Dear {selected_request.get('name', 'Employee')},

Your leave request for {selected_request['leave_type']} from {selected_request['start_date']} to {selected_request['end_date']} has been APPROVED.

Total days approved: {selected_request['total_days_requested']}

Reason: {selected_request['reason']}

Thank you.

Polaris Digitech HR Team
"""
                        if send_email_notification(employee_email, email_subject, email_body):
                            st.success(f"Approval email sent to {employee_email}.")
                        else:
                            st.warning(f"Failed to send approval email to {employee_email}.")
                    else:
                        st.warning("Employee email not found for notification.")
                    st.rerun()
                else:
                    st.info("This application is already Approved.")

            if col2.button("Reject", key=f"reject_{selected_application_index}"):
                if current_status != "Rejected":
                    selected_request["status"] = "Rejected"
                    for i, req in enumerate(st.session_state.leave_requests):
                        if req == selected_request:
                            st.session_state.leave_requests[i] = selected_request
                            break
                    save_data(st.session_state.leave_requests, LEAVE_REQUESTS_FILE)
                    st.warning("Leave request rejected.")
                    # Send email notification to employee
                    employee_email = selected_request.get('email_address')
                    if not employee_email:
                        all_users = load_data(USERS_FILE, [])
                        for user in all_users:
                            if user.get('employee_id') == selected_request.get('employee_id'):
                                employee_email = user.get('email_address')
                                break
                    if employee_email:
                        email_subject = f"Your Leave Request for {selected_request['leave_type']} has been Rejected"
                        email_body = f"""
Dear {selected_request.get('name', 'Employee')},

Your leave request for {selected_request['leave_type']} from {selected_request['start_date']} to {selected_request['end_date']} has been REJECTED.

Reason provided for request: {selected_request['reason']}

Please contact HR for more details if needed.

Thank you.

Polaris Digitech HR Team
"""
                        if send_email_notification(employee_email, email_subject, email_body):
                            st.success(f"Rejection email sent to {employee_email}.")
                        else:
                            st.warning(f"Failed to send rejection email to {employee_email}.")
                    else:
                        st.warning("Employee email not found for notification.")
                    st.rerun()
                else:
                    st.info("This application is already Rejected.")

            if col3.button("Generate PDF", key=f"pdf_leave_{selected_application_index}"):
                pdf_bytes = generate_leave_pdf(selected_request, st.session_state.user_profile) # Pass current user profile for template
                st.download_button(
                    label="Download Leave Request PDF",
                    data=pdf_bytes,
                    file_name=f"Leave_Request_{selected_request.get('name', 'N/A')}_{selected_request.get('submission_date')}.pdf",
                    mime="application/pdf"
                )

# Opex/Capex Requisition Form
def opex_capex_form():
    st.title("Submit Opex/Capex Requisition")

    requisition_type = st.radio("Requisition Type", ["Opex (Operating Expense)", "Capex (Capital Expense)"])

    title = st.text_input("Requisition Title", help="e.g., Purchase of office supplies, Server upgrade")
    details = st.text_area("Detailed Description", help="Provide comprehensive details about the requisition")

    st.subheader("Cost Breakdown")
    materials_cost = st.number_input("Cost of Materials/Goods (NGN)", min_value=0.0, format="%.2f", value=0.0)
    labour_cost = st.number_input("Cost of Labour/Services (NGN)", min_value=0.0, format="%.2f", value=0.0)

    wht_percentage_options = ["0%", "5%", "10%"]
    wht_percentage_str = st.selectbox("Withholding Tax (WHT) Percentage on Services", options=wht_percentage_options, index=0)
    wht_percentage_value = float(wht_percentage_str.strip('%')) / 100

    wht_amount = labour_cost * wht_percentage_value
    net_labour_cost = labour_cost - wht_amount
    net_amount_requested = materials_cost + net_labour_cost

    st.write(f"**Calculated WHT Amount:** {wht_amount:,.2f} NGN")
    st.write(f"**Calculated Net Labour/Services Cost:** {net_labour_cost:,.2f} NGN")
    st.markdown(f"### **Total Net Amount Requested: {net_amount_requested:,.2f} NGN**")

    amount_budgeted = st.number_input("Amount Budgeted for this (NGN)", min_value=0.0, format="%.2f", help="Enter the budgeted amount for this specific request if applicable.")
    budget_balance = amount_budgeted - net_amount_requested
    st.write(f"**Budget Balance:** {budget_balance:,.2f} NGN")

    st.subheader("Beneficiary Details")
    beneficiary_names = list(BENEFICIARIES_DATA.keys())
    selected_beneficiary_name = st.selectbox("Select Beneficiary", [""] + beneficiary_names)

    account_name = ""
    account_no = ""
    bank = ""

    if selected_beneficiary_name:
        beneficiary_info = BENEFICIARIES_DATA.get(selected_beneficiary_name, {})
        account_name = beneficiary_info.get("Account Name", "")
        account_no = beneficiary_info.get("Account No", "")
        bank = beneficiary_info.get("Bank", "")
        st.write(f"**Account Name:** {account_name}")
        st.write(f"**Account No:** {account_no}")
        st.write(f"**Bank:** {bank}")
    else:
        st.info("Please select a beneficiary to auto-fill account details.")

    # Allow manual entry if no beneficiary selected or details are missing
    manual_account_name = st.text_input("Manual Account Name (if needed)", value=account_name)
    manual_account_no = st.text_input("Manual Account No (if needed)", value=account_no)
    manual_bank = st.text_input("Manual Bank (if needed)", value=bank)

    # Use manual entries if provided, otherwise use auto-filled
    account_name = manual_account_name if manual_account_name else account_name
    account_no = manual_account_no if manual_account_no else account_no
    bank = manual_bank if manual_bank else bank

    uploaded_file = st.file_uploader("Upload Supporting Document (PDF, Image)", type=["pdf", "png", "jpg", "jpeg"])
    uploaded_doc_path = None # Initialize to None

    submitted = st.button("Submit Requisition for Approval")

    if submitted:
        # Check if basic details are filled
        if not all([title, details, account_name, account_no, bank]):
            st.error("Please fill in all required requisition and beneficiary details.")
        elif net_amount_requested <= 0:
            st.error("Total Net Amount Requested must be greater than zero.")
        else:
            if uploaded_file:
                # Create 'uploads' directory if it doesn't exist
                os.makedirs('uploads', exist_ok=True)
                uploaded_doc_path = os.path.join('uploads', uploaded_file.name)
                with open(uploaded_doc_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Uploaded: {uploaded_file.name}")
            else:
                st.info("No supporting document uploaded.")


            opex_capex_request = {
                "employee_id": st.session_state.user_profile.get('employee_id'), # Store employee ID
                "name": st.session_state.user_profile.get('name'), # Store employee name
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
                "beneficiaries": selected_beneficiary_name if selected_beneficiary_name else "Manual Entry",
                "account_name": account_name,
                "account_no": account_no,
                "bank": bank,
                "uploaded_document_path": uploaded_doc_path, # Path to the saved document
                "submitted_date": str(datetime.now().date()),
                "status_admin": "Pending",
                "status_finance": "Pending",
                "status_hr": "Pending",
                "status_md": "Pending"
            }
            st.session_state.opex_capex_requests.append(opex_capex_request)
            save_data(st.session_state.opex_capex_requests, OPEX_CAPEX_REQUESTS_FILE)
            st.success("Opex/Capex requisition submitted for approval.")

            # --- Email Notification Logic ---
            st.info("Sending email notifications to approval managers...")

            # Construct email details
            email_subject = f"New {requisition_type} Requisition from {st.session_state.username}: {title} (NGN {net_amount_requested:,.2f})"
            email_body = f"""
Dear Approver,

A new {requisition_type} requisition has been submitted by {st.session_state.user_profile.get('name', st.session_state.username)}.

Title: {title}
Details: {details}
Net Amount Requested: {net_amount_requested:,.2f} NGN
Beneficiary: {selected_beneficiary_name if selected_beneficiary_name else 'Manual Entry'}
Submitted On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please log in to the Polaris Digitech Staff Portal to review and approve this request.

Portal Link: [Your Streamlit App URL Here]
(e.g., https://your-streamlit-app-name.streamlit.app/view_opex_capex_applications)

Thank you,
Polaris Digitech HR System
"""
            # Send email to each approval manager
            for role, email in APPROVAL_EMAILS.items():
                if send_email_notification(email, email_subject, email_body):
                    st.success(f"Notification email sent to {role} ({email}).")
                else:
                    st.warning(f"Failed to send notification email to {role} ({email}).")

            # --- END NEW: Email Notification Logic ---

            st.session_state.current_page = "view_opex_capex_applications"
            st.rerun()

# View Opex/Capex Applications
def view_opex_capex_applications():
    st.title("View Opex/Capex Applications")

    if not st.session_state.opex_capex_requests:
        st.info("No Opex/Capex applications submitted yet.")
        return

    # Filter requests based on user role
    # Employees see only their requests
    # Managers (Admin, Finance, HR, MD) see all requests
    if st.session_state.user_role == "Employee":
        display_requests = [
            req for req in st.session_state.opex_capex_requests
            if req["employee_id"] == st.session_state.user_profile.get('employee_id')
        ]
    elif st.session_state.user_role in ["Admin Manager", "Finance Manager", "HR Manager", "Managing Director"]:
        display_requests = st.session_state.opex_capex_requests
    else: # Should not happen with defined roles, but as a fallback
        st.warning("You do not have permission to view Opex/Capex applications.")
        display_requests = []

    if not display_requests:
        st.info("No relevant Opex/Capex applications to display.")
        return

    df = pd.DataFrame(display_requests)
    df_display = df.copy()

    # Format dates and amounts for display
    if 'submitted_date' in df_display.columns:
        df_display['submitted_date'] = pd.to_datetime(df_display['submitted_date']).dt.strftime('%Y-%m-%d')
    for col in ['materials_cost', 'labour_cost', 'wht_amount', 'net_labour_cost', 'net_amount_requested', 'amount_budgeted', 'budget_balance']:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if pd.notnull(x) else 'N/A')

    st.dataframe(df_display, use_container_width=True)

    # Manager Approval Section
    if st.session_state.user_role in ["Admin Manager", "Finance Manager", "HR Manager", "Managing Director"]:
        st.subheader("Manage Applications")

        # Create a dropdown to select a request by title and submitter
        request_options = [
            f"{req.get('title', 'No Title')} by {req.get('name', 'Unknown')} (Submitted: {req.get('submitted_date', 'N/A')})"
            for req in display_requests
        ]
        selected_request_idx = st.selectbox("Select Requisition to Manage", range(len(display_requests)), format_func=lambda x: request_options[x] if x is not None else "")

        if selected_request_idx is not None:
            selected_request = display_requests[selected_request_idx]
            st.write("---")
            st.subheader(f"Details for {selected_request.get('title', 'N/A')}")
            st.json(selected_request)

            current_status = selected_request.get(f"status_{st.session_state.user_role.split(' ')[0].lower()}", "Pending")
            st.write(f"Your current approval status: **{current_status}**")

            # Determine if this manager's approval is needed and possible
            can_approve = False
            if st.session_state.user_role == "Admin Manager":
                can_approve = True
            elif st.session_state.user_role == "Finance Manager":
                # Can only approve if Admin has approved
                if selected_request.get("status_admin") == "Approved":
                    can_approve = True
                else:
                    st.info("Finance Manager can only approve after Admin Manager's approval.")
            elif st.session_state.user_role == "HR Manager":
                # Can only approve if Admin and Finance have approved
                if selected_request.get("status_admin") == "Approved" and selected_request.get("status_finance") == "Approved":
                    can_approve = True
                else:
                    st.info("HR Manager can only approve after Admin and Finance Managers' approvals.")
            elif st.session_state.user_role == "Managing Director":
                # Can only approve if Admin, Finance, and HR have approved
                if selected_request.get("status_admin") == "Approved" and \
                   selected_request.get("status_finance") == "Approved" and \
                   selected_request.get("status_hr") == "Approved":
                    can_approve = True
                else:
                    st.info("Managing Director can only approve after Admin, Finance, and HR Managers' approvals.")


            col1, col2, col3 = st.columns(3)
            if can_approve:
                if col1.button("Approve", key=f"approve_opex_{selected_request_idx}"):
                    if current_status != "Approved":
                        selected_request[f"status_{st.session_state.user_role.split(' ')[0].lower()}"] = "Approved"
                        # Find the original request in session_state.opex_capex_requests and update it
                        for i, req in enumerate(st.session_state.opex_capex_requests):
                            if req == selected_request:
                                st.session_state.opex_capex_requests[i] = selected_request
                                break
                        save_data(st.session_state.opex_capex_requests, OPEX_CAPEX_REQUESTS_FILE)
                        st.success(f"{st.session_state.user_role} has approved this request!")
                        # Check if all approvals are done
                        if selected_request.get("status_admin") == "Approved" and \
                           selected_request.get("status_finance") == "Approved" and \
                           selected_request.get("status_hr") == "Approved" and \
                           selected_request.get("status_md") == "Approved":

                            # Send final approval email to requester
                            requester_email = None
                            all_users = load_data(USERS_FILE, [])
                            for user in all_users:
                                if user.get('employee_id') == selected_request.get('employee_id'):
                                    requester_email = user.get('email_address')
                                    break

                            if requester_email:
                                final_subject = f"Your {selected_request['requisition_type']} Requisition '{selected_request['title']}' is Fully Approved!"
                                final_body = f"""
Dear {selected_request.get('name', 'Requester')},

Your {selected_request['requisition_type']} requisition with title '{selected_request['title']}' and amount {selected_request['net_amount_requested']:,.2f} NGN has been fully APPROVED by all management levels.

You may proceed with the next steps as per company policy.

Thank you.

Polaris Digitech HR System
"""
                                if send_email_notification(requester_email, final_subject, final_body):
                                    st.success(f"Final approval email sent to requester ({requester_email}).")
                                else:
                                    st.warning(f"Failed to send final approval email to requester ({requester_email}).")
                            else:
                                st.warning("Requester email not found for final notification.")

                        st.rerun()
                    else:
                        st.info("You have already Approved this application.")
                else:
                    st.info("You have already Approved this application." if current_status == "Approved" else "")

                if col2.button("Reject", key=f"reject_opex_{selected_request_idx}"):
                    if current_status != "Rejected":
                        selected_request[f"status_{st.session_state.user_role.split(' ')[0].lower()}"] = "Rejected"
                        # Set all subsequent statuses to "Rejected" as well
                        roles_in_order = ["admin", "finance", "hr", "md"]
                        current_role_idx = roles_in_order.index(st.session_state.user_role.split(' ')[0].lower())
                        for i in range(current_role_idx, len(roles_in_order)):
                            selected_request[f"status_{roles_in_order[i]}"] = "Rejected"

                        for i, req in enumerate(st.session_state.opex_capex_requests):
                            if req == selected_request:
                                st.session_state.opex_capex_requests[i] = selected_request
                                break
                        save_data(st.session_state.opex_capex_requests, OPEX_CAPEX_REQUESTS_FILE)
                        st.warning(f"{st.session_state.user_role} has rejected this request. All subsequent approvals are also marked as rejected.")

                        # Send rejection email to requester
                        requester_email = None
                        all_users = load_data(USERS_FILE, [])
                        for user in all_users:
                            if user.get('employee_id') == selected_request.get('employee_id'):
                                requester_email = user.get('email_address')
                                break

                        if requester_email:
                            rejection_subject = f"Your {selected_request['requisition_type']} Requisition '{selected_request['title']}' has been Rejected"
                            rejection_body = f"""
Dear {selected_request.get('name', 'Requester')},

Your {selected_request['requisition_type']} requisition with title '{selected_request['title']}' and amount {selected_request['net_amount_requested']:,.2f} NGN has been REJECTED by {st.session_state.user_role}.

Reason for request: {selected_request['details']}

Please contact {st.session_state.user_role} for more details if needed.

Thank you.

Polaris Digitech HR System
"""
                            if send_email_notification(requester_email, rejection_subject, rejection_body):
                                st.success(f"Rejection email sent to requester ({requester_email}).")
                            else:
                                st.warning(f"Failed to send rejection email to requester ({requester_email}).")
                        else:
                            st.warning("Requester email not found for notification.")

                        st.rerun()
                    else:
                        st.info("You have already Rejected this application.")
                else:
                    st.info("You have already Rejected this application." if current_status == "Rejected" else "")
            else:
                st.info(f"You cannot approve/reject this request yet. Pending approval from previous levels.")

            if col3.button("Generate PDF", key=f"pdf_opex_{selected_request_idx}"):
                pdf_bytes = generate_opex_capex_pdf(selected_request, st.session_state.user_profile)
                st.download_button(
                    label="Download Requisition PDF",
                    data=pdf_bytes,
                    file_name=f"Opex_Capex_Request_{selected_request.get('title', 'N/A')}_{selected_request.get('submitted_date')}.pdf",
                    mime="application/pdf"
                )


# Performance Goal Setting Page
def performance_goal_setting():
    st.title("Set Performance Goals")

    st.subheader("Current Goals")
    if not st.session_state.performance_goals:
        st.info("No goals set yet.")
    else:
        df_goals = pd.DataFrame(st.session_state.performance_goals)
        st.dataframe(df_goals, use_container_width=True)

        if st.session_state.user_role in ["Admin Manager", "HR Manager"]:
            st.subheader("Manage Goals (Admin/HR)")
            goals_to_edit_options = [f"{g.get('goal_name', 'N/A')} - {g.get('appraisal_period', 'N/A')}" for g in st.session_state.performance_goals]
            selected_goal_idx = st.selectbox("Select goal to edit/delete", range(len(st.session_state.performance_goals)), format_func=lambda x: goals_to_edit_options[x] if x is not None else "")

            if selected_goal_idx is not None:
                selected_goal = st.session_state.performance_goals[selected_goal_idx]
                st.write("---")
                st.subheader(f"Edit Goal: {selected_goal.get('goal_name', 'N/A')}")
                with st.form("edit_goal_form"):
                    edit_goal_name = st.text_input("Goal Name", value=selected_goal.get('goal_name', ''))
                    edit_description = st.text_area("Description", value=selected_goal.get('description', ''))
                    edit_appraisal_period = st.text_input("Appraisal Period (e.g., Q1 2024)", value=selected_goal.get('appraisal_period', ''))
                    edit_weight = st.number_input("Weight (1-10)", min_value=1, max_value=10, value=selected_goal.get('weight', 1))

                    if st.form_submit_button("Update Goal"):
                        st.session_state.performance_goals[selected_goal_idx] = {
                            "goal_name": edit_goal_name,
                            "description": edit_description,
                            "appraisal_period": edit_appraisal_period,
                            "weight": edit_weight,
                            "self_appraisal_score": selected_goal.get('self_appraisal_score', 0),
                            "self_appraisal_comments": selected_goal.get('self_appraisal_comments', ''),
                            "line_managers_rating": selected_goal.get('line_managers_rating', 0),
                            "line_managers_comments": selected_goal.get('line_managers_comments', '')
                        }
                        save_data(st.session_state.performance_goals, PERFORMANCE_GOALS_FILE)
                        st.success("Goal updated successfully!")
                        st.rerun()

                if st.button("Delete Goal", key=f"delete_goal_{selected_goal_idx}"):
                    st.session_state.performance_goals.pop(selected_goal_idx)
                    save_data(st.session_state.performance_goals, PERFORMANCE_GOALS_FILE)
                    st.success("Goal deleted successfully!")
                    st.rerun()

    if st.session_state.user_role in ["Admin Manager", "HR Manager"]:
        st.subheader("Add New Goal")
        with st.form("new_goal_form"):
            new_goal_name = st.text_input("New Goal Name")
            new_description = st.text_area("Description for New Goal")
            new_appraisal_period = st.text_input("Appraisal Period (e.g., Q1 2024)", value="Q" + str((datetime.now().month - 1) // 3 + 1) + " " + str(datetime.now().year))
            new_weight = st.number_input("Weight (1-10)", min_value=1, max_value=10, value=5)

            if st.form_submit_button("Add Goal"):
                if new_goal_name and new_description and new_appraisal_period:
                    new_goal = {
                        "goal_name": new_goal_name,
                        "description": new_description,
                        "appraisal_period": new_appraisal_period,
                        "weight": new_weight,
                        "self_appraisal_score": 0, # Default for new goals
                        "self_appraisal_comments": "",
                        "line_managers_rating": 0,
                        "line_managers_comments": ""
                    }
                    st.session_state.performance_goals.append(new_goal)
                    save_data(st.session_state.performance_goals, PERFORMANCE_GOALS_FILE)
                    st.success("New goal added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all fields for the new goal.")

# Self-Appraisal Page
def self_appraisal():
    st.title("Self-Appraisal")
    st.subheader("Rate Your Performance Against Goals")

    if not st.session_state.performance_goals:
        st.info("No performance goals have been set yet. Please contact HR.")
        return

    # Load existing appraisal data for the current user if available
    current_appraisal = load_data(CURRENT_APPRAISAL_FILE, {})
    if not current_appraisal:
        current_appraisal = {"appraisal_period": "N/A", "goals": [], "employee_comments": "", "development_areas": "", "training_needs": ""}

    # Filter goals by current appraisal period (you might need a mechanism to select this)
    # For now, let's assume all goals are for the current period or allow user to select
    unique_periods = sorted(list(set([g.get('appraisal_period', 'N/A') for g in st.session_state.performance_goals])))
    selected_period = st.selectbox("Select Appraisal Period", unique_periods, index=0 if unique_periods else None)

    if not selected_period:
        st.info("No appraisal periods available.")
        return

    # Filter goals for the selected period
    goals_for_period = [g for g in st.session_state.performance_goals if g.get('appraisal_period') == selected_period]

    if not goals_for_period:
        st.info(f"No goals set for the period: {selected_period}.")
        return

    # Initialize current_appraisal goals based on goals_for_period if not already set
    if not current_appraisal.get('goals') or len(current_appraisal['goals']) != len(goals_for_period):
        # If goals have changed or it's a new period, initialize current_appraisal.goals
        # with default values or carry over existing self-appraisal data if available
        current_appraisal['goals'] = [g.copy() for g in goals_for_period]
        for goal in current_appraisal['goals']:
            # Ensure self_appraisal fields are present, don't overwrite manager's rating
            goal['self_appraisal_score'] = goal.get('self_appraisal_score', 0)
            goal['self_appraisal_comments'] = goal.get('self_appraisal_comments', '')
            # Ensure managers fields are present if not already there
            goal['line_managers_rating'] = goal.get('line_managers_rating', 0)
            goal['line_managers_comments'] = goal.get('line_managers_comments', '')


    with st.form("self_appraisal_form"):
        st.write(f"Appraisal Period: **{selected_period}**")
        current_appraisal['appraisal_period'] = selected_period

        for i, goal in enumerate(current_appraisal['goals']):
            st.subheader(f"Goal {i+1}: {goal.get('goal_name', 'N/A')} (Weight: {goal.get('weight', 0)})")
            st.write(f"Description: {goal.get('description', 'N/A')}")

            # Display line manager's rating if available (read-only for employee)
            if goal.get('line_managers_rating', 0) > 0:
                st.info(f"Line Manager's Rating: **{goal.get('line_managers_rating')}**")
                st.write(f"Line Manager's Comments: {goal.get('line_managers_comments', 'N/A')}")


            score = st.slider(f"Your Score for '{goal.get('goal_name', 'Goal')}' (1-5)",
                              min_value=1, max_value=5, value=goal.get('self_appraisal_score', 1), key=f"score_{i}")
            comments = st.text_area(f"Your Comments for '{goal.get('goal_name', 'Goal')}'",
                                    value=goal.get('self_appraisal_comments', ''), key=f"comments_{i}")

            goal['self_appraisal_score'] = score
            goal['self_appraisal_comments'] = comments
            st.markdown("---")

        st.subheader("Overall Comments")
        employee_comments = st.text_area("General Comments on Performance", value=current_appraisal.get('employee_comments', ''))
        development_areas = st.text_area("Development Areas", value=current_appraisal.get('development_areas', ''))
        training_needs = st.text_area("Training Needs", value=current_appraisal.get('training_needs', ''))

        current_appraisal['employee_comments'] = employee_comments
        current_appraisal['development_areas'] = development_areas
        current_appraisal['training_needs'] = training_needs
        current_appraisal['employee_id'] = st.session_state.user_profile.get('employee_id') # Ensure employee_id is stored

        submitted = st.form_submit_button("Save Self-Appraisal")

        if submitted:
            save_data(current_appraisal, CURRENT_APPRAISAL_FILE)
            st.success("Self-appraisal saved successfully!")
            st.rerun()


# Line Manager's Appraisal Page
def line_manager_appraisal():
    st.title("Line Manager's Appraisal")
    st.subheader("Rate Employees' Performance")

    if st.session_state.user_role not in ["Admin Manager", "HR Manager", "Managing Director"]:
        st.warning("You do not have permission to access this page.")
        return

    # Load all user profiles to get employee names
    all_users = load_data(USERS_FILE, [])
    employee_users = [user for user in all_users if user.get('role') == 'Employee']

    if not employee_users:
        st.info("No employee users found to appraise.")
        return

    employee_options = {user['employee_id']: user['name'] for user in employee_users}
    selected_employee_id = st.selectbox("Select Employee to Appraise", options=list(employee_options.keys()), format_func=lambda x: employee_options[x] if x in employee_options else "Select Employee")

    if not selected_employee_id:
        st.info("Please select an employee.")
        return

    selected_employee_profile = next((user for user in employee_users if user['employee_id'] == selected_employee_id), None)
    if not selected_employee_profile:
        st.error("Selected employee profile not found.")
        return

    st.subheader(f"Appraising: {selected_employee_profile.get('name')}")

    # Load the appraisal data for the selected employee
    # A more robust system would store appraisals per employee, e.g., in a "appraisals/" directory
    # For simplicity, we'll load CURRENT_APPRAISAL_FILE which might overwrite if not careful
    # For now, let's assume CURRENT_APPRAISAL_FILE stores the "last viewed/edited" appraisal
    # A better way would be: load_employee_appraisal(selected_employee_id)
    # For now, if the file exists and matches the employee_id, load it.
    appraisal_file_for_employee = f"appraisals_{selected_employee_id}.json" # Unique file per employee
    appraisal_data = load_data(appraisal_file_for_employee, {})

    if not appraisal_data:
        st.info("This employee has not completed their self-appraisal yet for any period, or no goals are loaded for them.")
        # If no appraisal data, check if any goals exist for any period
        # If goals exist but no self-appraisal is saved, we can still show goals for manager to rate
        goals_for_employee = [g for g in st.session_state.performance_goals] # Assuming all goals apply to all employees for now
        if not goals_for_employee:
            st.warning("No performance goals are currently defined in the system.")
            return

        # Initialize basic appraisal data structure if no file exists
        appraisal_data = {
            "employee_id": selected_employee_id,
            "appraisal_period": "N/A", # Will be set by selected period
            "goals": [g.copy() for g in goals_for_employee],
            "employee_comments": "Employee has not submitted comments.",
            "development_areas": "Employee has not submitted development areas.",
            "training_needs": "Employee has not submitted training needs.",
            "line_managers_comments": ""
        }
        for goal in appraisal_data['goals']: # Ensure manager fields are initialized
            goal['line_managers_rating'] = goal.get('line_managers_rating', 0)
            goal['line_managers_comments'] = goal.get('line_managers_comments', '')

    # Filter goals by current appraisal period (same logic as self-appraisal)
    unique_periods = sorted(list(set([g.get('appraisal_period', 'N/A') for g in appraisal_data.get('goals', [])])))
    selected_period = st.selectbox("Select Appraisal Period", unique_periods, index=0 if unique_periods else None)

    if not selected_period:
        st.info("No appraisal periods available for this employee's goals.")
        return

    # Filter goals for the selected period
    goals_for_period = [g for g in appraisal_data['goals'] if g.get('appraisal_period') == selected_period]
    appraisal_data['appraisal_period'] = selected_period # Update the period in the data being edited

    if not goals_for_period:
        st.info(f"No goals found for {selected_employee_profile.get('name')} for the period: {selected_period}.")
        return

    with st.form("line_manager_appraisal_form"):
        st.write(f"Appraisal Period: **{selected_period}**")

        for i, goal in enumerate(goals_for_period):
            st.subheader(f"Goal {i+1}: {goal.get('goal_name', 'N/A')} (Weight: {goal.get('weight', 0)})")
            st.write(f"Description: {goal.get('description', 'N/A')}")
            st.info(f"Employee's Self-Appraisal Score: **{goal.get('self_appraisal_score', 'N/A')}**")
            st.write(f"Employee's Comments: {goal.get('self_appraisal_comments', 'N/A')}")

            manager_rating = st.slider(f"Your Rating for '{goal.get('goal_name', 'Goal')}' (1-5)",
                                       min_value=1, max_value=5, value=goal.get('line_managers_rating', 1), key=f"manager_rating_{selected_employee_id}_{i}")
            manager_comments = st.text_area(f"Your Comments for '{goal.get('goal_name', 'Goal')}'",
                                            value=goal.get('line_managers_comments', ''), key=f"manager_comments_{selected_employee_id}_{i}")

            # Update the goal in the `goals_for_period` list
            goals_for_period[i]['line_managers_rating'] = manager_rating
            goals_for_period[i]['line_managers_comments'] = manager_comments
            st.markdown("---")

        # Update the main appraisal_data's goals with the modified ones for this period
        appraisal_data['goals'] = [g for g in appraisal_data.get('goals', []) if g.get('appraisal_period') != selected_period] + goals_for_period


        st.subheader("Employee's Overall Comments")
        st.info(f"Employee's General Comments: {appraisal_data.get('employee_comments', 'N/A')}")
        st.info(f"Employee's Development Areas: {appraisal_data.get('development_areas', 'N/A')}")
        st.info(f"Employee's Training Needs: {appraisal_data.get('training_needs', 'N/A')}")


        line_managers_overall_comments = st.text_area("Your Overall Comments on Employee Performance", value=appraisal_data.get('line_managers_comments', ''))
        appraisal_data['line_managers_comments'] = line_managers_overall_comments


        submitted = st.form_submit_button("Save Manager's Appraisal")

        if submitted:
            save_data(appraisal_data, appraisal_file_for_employee) # Save to employee-specific file
            st.success(f"Manager's appraisal for {selected_employee_profile.get('name')} saved successfully!")
            st.rerun()

    # Generate PDF for this employee's appraisal
    if st.button(f"Generate Appraisal PDF for {selected_employee_profile.get('name')}"):
        pdf_bytes = generate_appraisal_pdf(appraisal_data, selected_employee_profile)
        st.download_button(
            label="Download Appraisal PDF",
            data=pdf_bytes,
            file_name=f"Performance_Appraisal_{selected_employee_profile.get('name')}_{appraisal_data.get('appraisal_period', 'N/A').replace(' ', '_')}.pdf",
            mime="application/pdf"
        )


# --- Login Page ---
def login_page():
    st.title("Login to Polaris Digitech HR System")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_data(USERS_FILE, []) # Load all users
        found_user = None
        for user in users:
            if user["username"] == username:
                found_user = user
                break

        if found_user and check_password(password, found_user["password_hash"]):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = found_user["role"] # Store user role
            st.session_state.user_profile = found_user # Store the entire user profile
            st.session_state.current_page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid username or password.")


# --- Main App Logic ---
def main():
    st.set_page_config(page_title="Polaris Digitech HR System", layout="wide", initial_sidebar_state="expanded")

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_role" not in st.session_state: # New: Store user role
        st.session_state.user_role = ""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
    if "leave_requests" not in st.session_state:
        st.session_state.leave_requests = load_data(LEAVE_REQUESTS_FILE, [])
    if "opex_capex_requests" not in st.session_state:
        st.session_state.opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, [])
    if "user_profile" not in st.session_state: # This will be populated on successful login
        st.session_state.user_profile = {} # Initialize as empty dict
    if "performance_goals" not in st.session_state:
        st.session_state.performance_goals = load_data(PERFORMANCE_GOALS_FILE, [])
    if "edit_goal_index" not in st.session_state:
        st.session_state.edit_goal_index = None

    # New: Call this once at the very beginning to ensure users.json exists
    # For production, you would remove this call after the first run and manage users via an admin interface
    initialize_users_data()

    if not st.session_state.logged_in:
        login_page()
    else:
        # Load and display company logo in sidebar
        logo_base64_sidebar = get_image_base64(LOGO_PATH)
        if logo_base64_sidebar:
            with st.sidebar:
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <img src="data:image/png;base64,{logo_base64_sidebar}" style="max-width: 150px; height: auto;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            with st.sidebar:
                st.warning("Logo not found.")

        st.sidebar.title(f"Welcome, {st.session_state.username.title()}!")
        st.sidebar.write(f"Role: **{st.session_state.user_role}**")

        st.sidebar.header("Navigation")
        if st.sidebar.button("Dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()

        if st.session_state.user_role == "Employee":
            if st.sidebar.button("Submit Leave Request"):
                st.session_state.current_page = "leave_request"
                st.rerun()
            if st.sidebar.button("View My Leave Applications"):
                st.session_state.current_page = "view_leave_applications"
                st.rerun()
            if st.sidebar.button("Submit Opex/Capex Requisition"):
                st.session_state.current_page = "opex_capex_form"
                st.rerun()
            if st.sidebar.button("View My Opex/Capex Applications"):
                st.session_state.current_page = "view_opex_capex_applications"
                st.rerun()
            if st.sidebar.button("Self-Appraisal"):
                st.session_state.current_page = "self_appraisal"
                st.rerun()

        # Admin/HR/Finance/MD permissions
        if st.session_state.user_role in ["Admin Manager", "HR Manager", "Finance Manager", "Managing Director"]:
            st.sidebar.subheader("Management")
            if st.sidebar.button("Manage Leave Applications"):
                st.session_state.current_page = "view_leave_applications"
                st.rerun()
            if st.sidebar.button("Manage Opex/Capex Applications"):
                st.session_state.current_page = "view_opex_capex_applications"
                st.rerun()

        if st.session_state.user_role in ["Admin Manager", "HR Manager"]:
            if st.sidebar.button("Set Performance Goals"):
                st.session_state.current_page = "performance_goal_setting"
                st.rerun()

        if st.session_state.user_role in ["Admin Manager", "HR Manager", "Managing Director"]: # Assuming Line Managers also rate
            if st.sidebar.button("Line Manager Appraisal"):
                st.session_state.current_page = "line_manager_appraisal"
                st.rerun()


        # Logout button
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_role = "" # Clear user role
            st.session_state.current_page = "login"
            st.session_state.leave_requests = load_data(LEAVE_REQUESTS_FILE, []) # Reload to clear current user's view
            st.session_state.opex_capex_requests = load_data(OPEX_CAPEX_REQUESTS_FILE, []) # Reload
            st.session_state.user_profile = {} # Clear user profile
            st.session_state.performance_goals = load_data(PERFORMANCE_GOALS_FILE, []) # Reload
            st.session_state.edit_goal_index = None
            # Also reset appraisal data if you want it fresh on logout (for the specific user)
            # This logic needs to be more robust for multi-user appraisals
            if os.path.exists(CURRENT_APPRAISAL_FILE):
                os.remove(CURRENT_APPRAISAL_FILE) # This will delete the last loaded appraisal, not ideal for multi-user
                                                 # Consider deleting specific user's appraisal file:
                                                 # if os.path.exists(f"appraisals_{st.session_state.user_profile.get('employee_id')}.json"):
                                                 # os.remove(f"appraisals_{st.session_state.user_profile.get('employee_id')}.json")
            st.rerun()

        # Display the selected page
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
        elif st.session_state.current_page == "self_appraisal":
            self_appraisal()
        elif st.session_state.current_page == "line_manager_appraisal":
            line_manager_appraisal()

if __name__ == "__main__":
    main()
