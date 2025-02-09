import streamlit as st
import subprocess
import sys
import os

# Force UTF-8 encoding for output
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONUTF8"] = "1"  # Ensure Python uses UTF-8 encoding

def run_command(script_name):
    """Efficiently runs a script and returns output or errors."""
    try:
        result = subprocess.run(["python", script_name], capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

# Configure Streamlit page
st.set_page_config(page_title="ACN Script Runner", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>🚀 ACN Script Execution Dashboard</h1>
    <p style='text-align: center; font-size: 18px;'>Click a button to run a script and view the output.</p>
    <p style='text-align: center; font-size: 18px; font-weight: bold; color: red;'>
    ⚠️ Caution: Do NOT interact unnecessarily—Exceeding API call limits may result in a complete shutdown.
    </p>
    """,
    unsafe_allow_html=True,
)

# Initialize session state if not present
if "output" not in st.session_state:
    st.session_state.output = ""

# Define scripts and their labels
scripts = {
    "Agents Data": "agents-from-firebase.py",
    "Inventories Data": "inventories-from-firebase.py",
    "Enquiries Data": "enquiries-from-firebase.py"
}

st.markdown("## 🔹 Available Scripts")

cols = st.columns(len(scripts))

for col, (label, script) in zip(cols, scripts.items()):
    with col:
        st.markdown(f"### {label}")
        if st.button(f"▶ Run {label}", use_container_width=True):
            st.session_state.output = run_command(script)

st.markdown("## 📜 Execution Log")
st.text_area("Execution Output:", st.session_state.output, height=300, placeholder="Script output will appear here...", help="View logs and errors from executed scripts")

st.markdown("---")
st.success("✅ Ensure that the commands are valid and have the necessary permissions.")
