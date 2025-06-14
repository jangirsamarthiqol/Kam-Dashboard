import streamlit as st
import subprocess
import sys
import os
import time
import datetime
import threading
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import pytz
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK using environment variables
def initialize_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_credentials = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
        }
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred)

# Initialize Firebase
initialize_firebase()

# Get reference to Firestore database
db = firestore.client()

# Get the Python interpreter path
PYTHON_EXECUTABLE = sys.executable

# Streamlit page configuration
st.set_page_config(
    page_title="ACN Script Runner",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎯"
)

# Modern dark theme with glassmorphism
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #1a1f2c, #121419); }
    .glass-card { background: rgba(31, 41, 55, 0.4); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius:16px; padding:20px; box-shadow:0 8px 32px rgba(0,0,0,0.37); }
    .neon-border { position: relative; }
    .neon-border::after { content:''; position:absolute; top:-2px; left:-2px; right:-2px; bottom:-2px; border-radius:16px; background:linear-gradient(45deg,#ff3366,#ff33cc,#33ccff,#33ff66); z-index:-1; filter:blur(14px); opacity:0.15; }
    .stButton button { background:rgba(51,204,255,0.1); border:1px solid rgba(51,204,255,0.2); color:#33ccff; border-radius:12px; padding:15px 25px; font-weight:600; transition:all 0.3s ease; backdrop-filter:blur(5px); text-transform:uppercase; letter-spacing:1px; }
    .stButton button:hover { background:rgba(51,204,255,0.2); border-color:#33ccff; transform:translateY(-2px); box-shadow:0 0 20px rgba(51,204,255,0.4); }
    .stTextArea textarea { background:rgba(31,41,55,0.4)!important; border:1px solid rgba(255,255,255,0.1)!important; border-radius:12px!important; color:#e2e8f0!important; font-family:'JetBrains Mono', monospace!important; }
    h1,h2,h3 { font-family:'Inter',sans-serif; color:#ffffff!important; font-weight:700; }
    p { color:#cbd5e0; }
    code { color:#33ccff; background:rgba(51,204,255,0.1); padding:2px 6px; border-radius:4px; }
    .status-active { background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.2); color:#34d399; padding:8px 12px; border-radius:8px; }
    .plan-card { background:rgba(51,204,255,0.1); border:1px solid rgba(51,204,255,0.2); border-radius:12px; padding:20px; margin:10px 0; transition:all 0.3s ease; }
    .plan-card:hover { background:rgba(51,204,255,0.2); cursor:pointer; transform:translateY(-2px); }
    .plan-card.selected { background:rgba(51,204,255,0.3); border-color:#33ccff; box-shadow:0 0 20px rgba(51,204,255,0.2); }
    .plan-header { font-size:24px; font-weight:700; margin-bottom:10px; color:#33ccff; }
    .plan-price { font-size:20px; color:#34d399; margin-bottom:15px; }
    .plan-features { list-style:none; padding:0; margin:0; }
    .plan-features li { margin:8px 0; color:#cbd5e0; }
    .plan-features li:before { content:"✓"; color:#34d399; margin-right:8px; }
    .current-plan { background:rgba(52,211,153,0.1); border:1px solid rgba(52,211,153,0.2); border-radius:12px; padding:15px; margin:10px 0; }
    .current-plan-header { color:#34d399; font-weight:600; margin-bottom:10px; }
    .confirm-button { background:rgba(52,211,153,0.1)!important; border-color:rgba(52,211,153,0.2)!important; color:#34d399!important; }
    .confirm-button:hover { background:rgba(52,211,153,0.2)!important; border-color:#34d399!important; }
    </style>
""", unsafe_allow_html=True)

def standardize_phone_number(phone):
    # Remove any spaces or special characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # If number starts with 91 and is 12 digits, add + prefix
    if phone.startswith('91') and len(phone) == 12:
        return '+' + phone
    
    # If number is 10 digits, add +91 prefix
    if len(phone) == 10:
        return '+91' + phone
    
    # If number already has +91 prefix, return as is
    if phone.startswith('+91'):
        return phone
    
    # If none of the above conditions match, return original with +91
    return '+91' + phone

def update_user_plan(phone_number, plan, current_data):
    # Get the current date
    current_date = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_timestamp = int(current_date.timestamp())

    # Calculate next renewal date (30 days from now)
    next_renewal = current_date + timedelta(days=30)
    next_renewal_timestamp = int(next_renewal.timestamp())

    # Determine plan expiry, monthly credits, and user type based on selected plan
    if plan == "premium":
        plan_expiry = current_date + timedelta(days=365)  # 1 year for premium
        monthly_credits = 100
        user_type = "premium"
    elif plan == "trial":
        plan_expiry = current_date + timedelta(days=30)  # 30 days for trial
        monthly_credits = 100  # Trial gives 100 credits
        user_type = "trial"
    else:  # For basic plan
        plan_expiry = current_date + timedelta(days=30)  # 30 days for basic as well
        monthly_credits = 5  # Basic gives 5 credits
        user_type = "basic"

    # Prepare the update data while preserving existing fields
    update_data = {
        'nextRenewal': next_renewal_timestamp,
        'userType': user_type,
        'planExpiry': int(plan_expiry.timestamp()),
        'monthlyCredits': monthly_credits,
        'updatedAt': current_timestamp,
        'lastModified': current_timestamp
    }

    # If the previous plan was basic and we are switching to another plan, set trialUsed to True
    previous_plan = current_data.get('userType', None)
    if previous_plan == "basic" and plan != "basic":
        update_data['trialUsed'] = True
        update_data['trialStartedAt'] = current_timestamp

    # Get the document reference using the query result
    agent_ref = db.collection('agents').document(current_data['id'])

    # Update the agent's document in Firebase
    try:
        agent_ref.update(update_data)
        return True, f"Successfully updated plan to {plan}. New expiry: {plan_expiry.strftime('%Y-%m-%d')}, Credits: {monthly_credits}"
    except Exception as e:
        return False, f"Failed to update plan: {str(e)}"

# Function to run external scripts
def run_script(script_name):
    path = os.path.join(os.getcwd(), script_name)
    if not os.path.exists(path):
        return f"⚠️ Script not found: `{script_name}`"
    start = time.time()
    try:
        with st.spinner(f"⚡ Executing {script_name}"):
            proc = subprocess.run(
                [PYTHON_EXECUTABLE, path], capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"}
            )
        dura = round(time.time() - start, 2)
        out = proc.stdout.strip() or "No output received"
        err = proc.stderr.strip() or ""
        if proc.returncode == 0:
            return f"✨ Success ({dura}s)\n\n```\n{out}\n```"
        else:
            return f"❌ Failed ({dura}s)\n\n```\n{err}\n```"
    except Exception as e:
        return f"💥 Error: {e}"

# UI Header
st.markdown(
    """
    <div class="glass-card neon-border" style="text-align:center; margin-bottom:40px;">
      <div style="font-size:48px;">🎯</div>
      <h1 style="font-size:36px;">ACN Command Center</h1>
      <p style="font-size:18px; opacity:0.8;">Enterprise Script Management Interface</p>
    </div>
    """, unsafe_allow_html=True
)

# Initialize session state
if "output" not in st.session_state:
    st.session_state.output = ""
if "selected_plan" not in st.session_state:
    st.session_state.selected_plan = None
if "agent_data" not in st.session_state:
    st.session_state.agent_data = None

# Scripts list
dict_scripts = {
    "Agents": {"file":"agents-from-firebase.py","icon":"👤","desc":"Sync agent data from Firebase"},
    "Inventory": {"file":"inventories-from-firebase.py","icon":"📦","desc":"Sync inventory records from Firebase"},
    "Enquiries": {"file":"enquires-from-firebase.py","icon":"📋","desc":"Sync enquiries from Firebase"},
    "Database": {"file":"Dateupdate.py","icon":"🔄","desc":"Update Last Checked Date in Firebase"},
    "Requirements": {"file":"requirements-from-firebase.py","icon":"📑","desc":"Sync requirements from Firebase"},
    "Update Plan": {"file":None,"icon":"⭐","desc":"Update agent subscription plan"}
}
keys = list(dict_scripts.keys())

# Display operations
st.markdown("<h2 style='text-align:center; margin-bottom:30px;'>Available Operations</h2>", unsafe_allow_html=True)
for i in range(0, len(keys), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        idx = i + j
        if idx < len(keys):
            key = keys[idx]
            info = dict_scripts[key]
            with col:
                st.markdown(
                    f"""
                    <div class="glass-card neon-border" style="margin-bottom:20px;">
                      <div style="font-size:24px;">{info['icon']}</div>
                      <h3 style="margin:10px 0;">{key}</h3>
                      <p style="opacity:0.8;">{info['desc']}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
                if st.button(f"Execute {key}", key=f"btn_{key}", use_container_width=True):
                    if key == "Update Plan":
                        st.session_state.show_plan_update = True
                    else:
                        st.session_state.output = run_script(info['file'])

# Plan Update Interface
if st.session_state.get('show_plan_update', False):
    st.markdown("""
    <div style="margin:40px 0 20px 0;"><h2 style="text-align:center;">Update Agent Plan</h2></div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass-card neon-border">', unsafe_allow_html=True)
        
        # Phone number input with better styling
        phone_input = st.text_input("Enter Agent's Phone Number", key="phone_input", 
                                  placeholder="Enter 10-digit number (e.g., 8118823650)")
        
        if phone_input:
            phone_number = standardize_phone_number(phone_input)
            
            # Query the database
            agents_ref = db.collection('agents')
            query = agents_ref.where('phonenumber', '==', phone_number).limit(1)
            results = query.get()
            
            if results:
                agent_data = results[0].to_dict()
                agent_data['id'] = results[0].id
                st.session_state.agent_data = agent_data
                
                # Display current plan details in a better format
                st.markdown('<div class="current-plan">', unsafe_allow_html=True)
                st.markdown('<div class="current-plan-header">Current Plan Details</div>', unsafe_allow_html=True)
                st.markdown(f"""
                - **Name:** {agent_data.get('name', 'Not Available')}
                - **Phone:** {agent_data.get('phonenumber', 'Not Available')}
                - **Current Plan:** {agent_data.get('userType', 'Not Available').upper()}
                - **Plan Expiry:** {datetime.fromtimestamp(agent_data.get('planExpiry', 0)).strftime('%Y-%m-%d %H:%M:%S')}
                - **Monthly Credits:** {agent_data.get('monthlyCredits', 0)}
                - **Trial Used:** {agent_data.get('trialUsed', False)}
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Plan selection with better UI
                st.markdown("### Select New Plan")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown('<div class="plan-card">', unsafe_allow_html=True)
                    st.markdown('<div class="plan-header">Premium</div>', unsafe_allow_html=True)
                    st.markdown('<div class="plan-price">100 Credits</div>', unsafe_allow_html=True)
                    st.markdown("""
                    <ul class="plan-features">
                        <li>1 Year Validity</li>
                        <li>100 Monthly Credits</li>
                        <li>Full Access</li>
                    </ul>
                    """, unsafe_allow_html=True)
                    if st.button("Select Premium", key="premium_btn", use_container_width=True):
                        st.session_state.selected_plan = "premium"
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="plan-card">', unsafe_allow_html=True)
                    st.markdown('<div class="plan-header">Trial</div>', unsafe_allow_html=True)
                    st.markdown('<div class="plan-price">100 Credits</div>', unsafe_allow_html=True)
                    st.markdown("""
                    <ul class="plan-features">
                        <li>30 Days Validity</li>
                        <li>100 Monthly Credits</li>
                        <li>Full Access</li>
                    </ul>
                    """, unsafe_allow_html=True)
                    if st.button("Select Trial", key="trial_btn", use_container_width=True):
                        st.session_state.selected_plan = "trial"
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col3:
                    st.markdown('<div class="plan-card">', unsafe_allow_html=True)
                    st.markdown('<div class="plan-header">Basic</div>', unsafe_allow_html=True)
                    st.markdown('<div class="plan-price">5 Credits</div>', unsafe_allow_html=True)
                    st.markdown("""
                    <ul class="plan-features">
                        <li>30 Days Validity</li>
                        <li>5 Monthly Credits</li>
                        <li>Limited Access</li>
                    </ul>
                    """, unsafe_allow_html=True)
                    if st.button("Select Basic", key="basic_btn", use_container_width=True):
                        st.session_state.selected_plan = "basic"
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.selected_plan:
                    st.markdown(f"### Selected Plan: {st.session_state.selected_plan.upper()}")
                    if st.button("Confirm Update", type="primary", use_container_width=True, 
                               help="Click to confirm the plan update"):
                        success, message = update_user_plan(phone_number, st.session_state.selected_plan, agent_data)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                        st.session_state.selected_plan = None
                        st.session_state.agent_data = None
                        st.session_state.show_plan_update = False
            else:
                st.error(f"No agent found with phone number {phone_number}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Output display
if st.session_state.output:
    st.markdown("""
    <div style="margin:40px 0 20px 0;"><h2 style="text-align:center;">Operation Output</h2></div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="glass-card neon-border">', unsafe_allow_html=True)
    st.text_area("", st.session_state.output, height=300, key="output_area")
    st.markdown('</div>', unsafe_allow_html=True)

# Keep-alive thread
def keep_alive():
    while True:
        st.session_state.keep_alive_time = datetime.now().strftime('%H:%M:%S')
        time.sleep(60)
threading.Thread(target=keep_alive, daemon=True).start()

# Status footer
if 'keep_alive_time' in st.session_state:
    st.markdown(
        f"""
        <div style="position:fixed; bottom:20px; right:20px; z-index:1000;">
          <div class="status-active">⚡ System Active | {st.session_state.keep_alive_time}</div>
        </div>
        """, unsafe_allow_html=True
    )
