import streamlit as st
import subprocess
import sys
import os
import time
import datetime
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    /* Global theme */
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1a1f2c, #121419);
    }
    
    /* Glassmorphism effect */
    .glass-card {
        background: rgba(31, 41, 55, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Neon accents */
    .neon-border {
        position: relative;
    }
    
    .neon-border::after {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        border-radius: 16px;
        background: linear-gradient(45deg, #ff3366, #ff33cc, #33ccff, #33ff66);
        z-index: -1;
        filter: blur(14px);
        opacity: 0.15;
    }
    
    /* Custom button */
    .stButton button {
        background: rgba(51, 204, 255, 0.1);
        border: 1px solid rgba(51, 204, 255, 0.2);
        color: #33ccff;
        border-radius: 12px;
        padding: 15px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton button:hover {
        background: rgba(51, 204, 255, 0.2);
        border-color: #33ccff;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(51, 204, 255, 0.4);
    }
    
    /* Text area */
    .stTextArea textarea {
        background: rgba(31, 41, 55, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Typography */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    p {
        color: #cbd5e0;
    }
    
    code {
        color: #33ccff;
        background: rgba(51, 204, 255, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    /* Status indicators */
    .status-active {
        background: rgba(52, 211, 153, 0.1);
        border: 1px solid rgba(52, 211, 153, 0.2);
        color: #34d399;
        padding: 8px 12px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# =================== FUNCTION: Run External Scripts ===================
def run_script(script_name):
    """Runs a Python script asynchronously and returns the output."""
    script_path = os.path.join(os.getcwd(), script_name)

    if not os.path.exists(script_path):
        return f"⚠️ Script not found: `{script_name}`"

    start_time = time.time()

    try:
        with st.spinner(f"⚡ Executing {script_name}"):
            result = subprocess.run(
                [PYTHON_EXECUTABLE, script_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONUTF8": "1"}
            )

        execution_time = round(time.time() - start_time, 2)
        stdout = result.stdout.strip() if result.stdout else "No output received"
        stderr = result.stderr.strip() if result.stderr else ""

        if result.returncode == 0:
            return f"✨ Success ({execution_time}s)\n\n```\n{stdout}\n```"
        else:
            return f"❌ Failed ({execution_time}s)\n\n```\n{stderr}\n```"

    except Exception as e:
        return f"💥 Error: {str(e)}"

# =================== UI HEADER ===================
st.markdown(
    """
    <div class="glass-card neon-border" style="text-align: center; margin-bottom: 40px;">
        <div style="font-size: 48px; margin-bottom: 10px;">🎯</div>
        <h1 style="font-size: 36px; margin-bottom: 10px;">ACN Command Center</h1>
        <p style="font-size: 18px; opacity: 0.8;">Enterprise Script Management Interface</p>
    </div>
    """,
    unsafe_allow_html=True
)

# =================== SESSION STATE INITIALIZATION ===================
if "output" not in st.session_state:
    st.session_state.output = ""

# =================== SCRIPTS LIST ===================
scripts = {
    "Agents": {
        "file": "agents-from-firebase.py",
        "icon": "👤",
        "description": "Sync agent data from Firebase"
    },
    "Inventory": {
        "file": "inventories-from-firebase.py",
        "icon": "📦",
        "description": "Update inventory records"
    },
    "Enquiries": {
        "file": "enquires-from-firebase.py",
        "icon": "📋",
        "description": "Process pending enquiries"
    },
    "Database": {
        "file": "Dateupdate.py",
        "icon": "🔄",
        "description": "Perform database updates"
    }
}

# =================== SCRIPT EXECUTION UI ===================
st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>Available Operations</h2>", unsafe_allow_html=True)

for i in range(0, len(scripts), 2):
    cols = st.columns(2)
    for j in range(2):
        if i + j < len(scripts):
            label = list(scripts.keys())[i + j]
            info = scripts[label]
            with cols[j]:
                st.markdown(
                    f"""
                    <div class="glass-card neon-border" style="margin-bottom: 20px;">
                        <div style="font-size: 24px;">{info['icon']}</div>
                        <h3 style="margin: 10px 0;">{label}</h3>
                        <p style="margin-bottom: 20px; opacity: 0.8;">{info['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"Execute {label}", key=f"btn_{label}", use_container_width=True):
                    st.session_state.output = run_script(info['file'])

# =================== OUTPUT DISPLAY ===================
if st.session_state.output:
    st.markdown(
        """
        <div style="margin: 40px 0 20px 0;">
            <h2 style="text-align: center;">Operation Output</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="glass-card neon-border">', unsafe_allow_html=True)
    st.text_area(
        "",
        st.session_state.output,
        height=300,
        key="output_area"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =================== KEEP-ALIVE MECHANISM ===================
def keep_alive():
    while True:
        st.session_state["keep_alive_time"] = datetime.datetime.now().strftime('%H:%M:%S')
        time.sleep(60)

keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

# Status footer
if "keep_alive_time" in st.session_state:
    st.markdown(
        f"""
        <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000;">
            <div class="status-active">
                ⚡ System Active | {st.session_state.keep_alive_time}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

