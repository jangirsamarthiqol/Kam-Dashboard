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
st.set_page_config(page_title="ACN Script Runner", layout="wide")

# =================== FUNCTION: Run External Scripts ===================
def run_script(script_name):
    """Runs a Python script asynchronously and returns the output."""
    script_path = os.path.join(os.getcwd(), script_name)

    if not os.path.exists(script_path):
        return f"❌ Error: Script `{script_name}` not found! Path: `{script_path}`"

    start_time = time.time()

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONUTF8": "1"}
        )

        execution_time = round(time.time() - start_time, 2)
        stdout = result.stdout.strip() if result.stdout else "⚠️ No standard output received."
        stderr = result.stderr.strip() if result.stderr else ""

        if result.returncode == 0:
            return f"✅ Success: `{script_name}` completed in {execution_time}s.\n\n```\n{stdout}\n```"
        else:
            return f"❌ Error: `{script_name}` failed (Exit Code: {result.returncode}, took {execution_time}s).\n\n```\n{stderr}\n```"

    except FileNotFoundError:
        return f"❌ Error: `{script_name}` not found or missing execution permissions."
    except Exception as e:
        return f"❌ Unexpected Error: `{script_name}` failed.\n\n```\n{str(e)}\n```"

# =================== UI HEADER ===================
st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>ACN Script Runner Dashboard</h1>
    <p style='text-align: center; font-size: 18px;'>Click a button to run a script and view the output.</p>
    <p style='text-align: center; font-size: 18px; font-weight: bold; color: red;'>⚠️ Avoid unnecessary execution—API limits may cause a shutdown.</p>
    """,
    unsafe_allow_html=True,
)

# =================== SESSION STATE INITIALIZATION ===================
if "output" not in st.session_state:
    st.session_state.output = ""

# =================== SCRIPTS LIST ===================
scripts = {
    "Agents Data": "agents-from-firebase.py",
    "Inventories Data": "inventories-from-firebase.py",
    "Enquiries Data": "enquires-from-firebase.py"
}

# =================== SCRIPT EXECUTION UI ===================
st.markdown("## 🔹 Available Scripts")
cols = st.columns(len(scripts))

for col, (label, script) in zip(cols, scripts.items()):
    with col:
        st.markdown(f"### {label}")
        if st.button(f"▶ Run {label}", use_container_width=True):
            with st.spinner(f"Running {label}..."):
                st.session_state.output = run_script(script)

# =================== EXECUTION OUTPUT UI ===================
st.markdown("## 📜 Execution Log")
st.markdown("### ✅ **Results:**")

st.text_area(
    "Execution Output:", 
    st.session_state.output, 
    height=350, 
    placeholder="Script output will appear here...",
    help="View logs and errors from executed scripts"
)

st.markdown("---")

# =================== KEEP-ALIVE MECHANISM ===================
def keep_alive():
    """Prevents server from going idle by updating a session state variable asynchronously."""
    while True:
        st.session_state["keep_alive_time"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(60)  # Prevents shutdown due to inactivity

# Start keep-alive in a background thread
keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

# Display keep-alive status without re-rendering every second
if "keep_alive_time" in st.session_state:
    st.markdown(f"🟢 **Keep-alive active** | Last updated: `{st.session_state.keep_alive_time}`")
