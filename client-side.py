import streamlit as st
import subprocess
import sys
import os

# Force UTF-8 encoding for output
sys.stdout.reconfigure(encoding="utf-8")
os.environ["PYTHONUTF8"] = "1"  # Ensure Python uses UTF-8 encoding

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {str(e)}"

st.set_page_config(page_title="ACN Script Runner", layout="wide")

st.markdown(
    """
    <h1 style='text-align: center; color: #4CAF50;'>🚀 ACN Script Execution Dashboard</h1>
    <p style='text-align: center; font-size: 18px;'>Click a button to run a script and view the output.</p>
<p style="text-align: center; font-size: 18px; font-weight: bold; color: red;">
    ⚠️ Caution: Do NOT interact with this unnecessarily—Exceeding API call limits may result in a complete shutdown.
</p>
    """,
    unsafe_allow_html=True,
)

if "output" not in st.session_state:
    st.session_state.output = ""

# st.markdown("## 🔹 Available Scripts")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📂 Agents Data")
    if st.button("▶ Run Agents Script", use_container_width=True):
        st.session_state.output = run_command("python agents-from-firebase.py")

with col2:
    st.markdown("### 🏢 Inventories Data")
    if st.button("▶ Run Inventories Script", use_container_width=True):
        st.session_state.output = run_command("python inventories-from-firebase.py")

with col3:
    st.markdown("### 📋 Enquiries Data")
    if st.button("▶ Run Enquiries Script", use_container_width=True):
        st.session_state.output = run_command("python enquires-from-firebase.py")

st.markdown("## 📜 Execution Log")
st.text_area("Execution Output:", st.session_state.output, height=300, placeholder="Script output will appear here...", help="View logs and errors from executed scripts")

st.markdown("---")
st.success("✅ Ensure that the commands are valid and have the necessary permissions.")
