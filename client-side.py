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
    </style>
""", unsafe_allow_html=True)

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

# Scripts list
dict_scripts = {
    "Agents": {"file":"agents-from-firebase.py","icon":"👤","desc":"Sync agent data from Firebase"},
    "Inventory": {"file":"inventories-from-firebase.py","icon":"📦","desc":"Sync inventory records from Firebase"},
    "Enquiries": {"file":"enquires-from-firebase.py","icon":"📋","desc":"Sync enquiries from Firebase"},
    "Database": {"file":"Dateupdate.py","icon":"🔄","desc":"Update Last Checked Date in Firebase"},
    "Requirements": {"file":"requirements-from-firebase.py","icon":"📑","desc":"Sync requirements from Firebase"}
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
                    st.session_state.output = run_script(info['file'])

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
        st.session_state.keep_alive_time = datetime.datetime.now().strftime('%H:%M:%S')
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
