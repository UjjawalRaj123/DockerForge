import streamlit as st
import os
from agent import DockerForgeAgent

st.set_page_config(
    page_title="DockerForge",
    page_icon="🐳",
    layout="wide"
)

st.title("🐳 DockerForge — AI-Powered Dockerfile Generator")
st.caption("Full Stack + Agentic AI Developer")

# ── Sidebar config ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", "")
    )
    st.markdown("---")
    st.markdown("**How it works:**")
    st.markdown("""
    1. Accepts a GitHub URL  
    2. Clones & scans the repo  
    3. AI generates a Dockerfile  
    4. Runs `docker build`  
    5. Auto-fixes on failure (max 3×)  
    6. Runs `docker run` to verify  
    7. Displays the final Dockerfile  
    """)

# ── Main input ─────────────────────────────────────────────────────────────
st.subheader("🔗 Enter a Public GitHub Repository URL")
github_url = st.text_input(
    "GitHub URL",
    placeholder="https://github.com/username/repository"
)

if st.button("🚀 Generate Dockerfile", type="primary",
             disabled=not (github_url and api_key)):

    log_area   = st.empty()
    logs       = []

    def append_log(msg):
        logs.append(msg)
        log_area.code("\n".join(logs), language="bash")

    with st.spinner("DockerForge agent is working..."):
        agent  = DockerForgeAgent(api_key=api_key)
        result = agent.run(github_url, log_callback=append_log)

    st.markdown("---")

    # ── Step 7: Display final Dockerfile ───────────────────────────
    st.subheader("📄 Generated Dockerfile")
    st.code(result["dockerfile"], language="dockerfile")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔨 Build Output")
        status = "✅ Success" if result["build_output"]["success"] else "❌ Failed"
        st.markdown(f"**Status:** {status}")
        with st.expander("stdout"):
            st.text(result["build_output"]["stdout"][-3000:])
        with st.expander("stderr"):
            st.text(result["build_output"]["stderr"][-3000:])

    with col2:
        if result["run_output"]:
            st.subheader("🚀 Run Output")
            run_status = "✅ Started" if result["run_output"]["success"] \
                         else "⚠️ Check logs"
            st.markdown(f"**Status:** {run_status}")
            with st.expander("stdout"):
                st.text(result["run_output"]["stdout"])
            with st.expander("stderr"):
                st.text(result["run_output"]["stderr"])

    # Download button
    st.download_button(
        label="⬇️ Download Dockerfile",
        data=result["dockerfile"],
        file_name="Dockerfile",
        mime="text/plain"
    )