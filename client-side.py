import streamlit as st
import subprocess
import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the Python interpreter path
PYTHON_EXECUTABLE = sys.executable

# Streamlit page configuration
st.set_page_config(page_title="ACN Script Runner", layout="wide")

# Function to execute external Python scripts
def run_script(script_name):
    """Runs a Python script and returns the output."""
    script_path = os.path.join(os.getcwd(), script_name)  # Ensure correct path

    if not os.path.exists(script_path):
        return f"❌ Error: Script `{script_name}` not found! Path: `{script_path}`"

    st.markdown(f"🔹 **Executing:** `{script_name}` ⏳")
    start_time = time.time()  # Start time tracking

    try:
        result = subprocess.run(
            [PYTHON_EXECUTABLE, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",  # <--- Force UTF-8 Encoding
            env={**os.environ, "PYTHONUTF8": "1"}  # <--- Ensure UTF-8 in subprocess
        )


        execution_time = round(time.time() - start_time, 2)  # Calculate execution time

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

# Debug: Show the Python version being used
# st.markdown(f"### 🐍 Using Python: `{PYTHON_EXECUTABLE}`")

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>ACN Script Runner Dashboard</h1>
    <p style='text-align: center; font-size: 18px;'>Click a button to run a script and view the output.</p>
    <p style='text-align: center; font-size: 18px; font-weight: bold; color: red;'>⚠️ Avoid unnecessary execution—API limits may cause a shutdown.</p>
    """,
    unsafe_allow_html=True,
)

# Initialize session state for output
if "output" not in st.session_state:
    st.session_state.output = ""

# Define scripts to run
scripts = {
    "Agents Data": "agents-from-firebase.py",
    "Inventories Data": "inventories-from-firebase.py",
    "Enquiries Data": "enquires-from-firebase.py"
}

# UI for script execution
st.markdown("## 🔹 Available Scripts")
cols = st.columns(len(scripts))

for col, (label, script) in zip(cols, scripts.items()):
    with col:
        st.markdown(f"### {label}")
        if st.button(f"▶ Run {label}", use_container_width=True):
            st.session_state.output = run_script(script)

# Display output log
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
# st.success("✅ Ensure scripts are valid and have necessary permissions.")
