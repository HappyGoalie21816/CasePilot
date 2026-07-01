"""
AI Copilot for Caseworkers — Streamlit Application

A multi-agent AI system that explains financial calculations,
classifies enforcement risk, and summarizes cases for
Child Maintenance Service caseworkers.
"""

import json
import os
import streamlit as st

from llm.gateway import LLMGateway, LLMGatewayError
from agents.orchestrator import AgentOrchestrator

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
LLM_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
LLM_MODEL = "meta-llama-3-8b-instruct"
LLM_API_KEY = "lm-studio"

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Copilot — Caseworker Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0a0e27 50%, #1a1145 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at 30% 50%, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .main-header h1 {
        color: #e2e8f0;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }

    /* Agent card styling */
    .agent-card {
        background: linear-gradient(145deg, #131836 0%, #0d1025 100%);
        border: 1px solid rgba(59, 130, 246, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }

    .agent-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.1);
    }

    .agent-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }

    .agent-header h3 {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }

    /* Status badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }

    .status-success {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }

    .status-error {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .status-partial {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    /* Timing pill */
    .timing-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.5rem;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 12px;
        color: #60a5fa;
        font-size: 0.7rem;
        font-weight: 500;
    }

    /* Metrics row */
    .metrics-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }

    .metric-card {
        flex: 1;
        background: rgba(59, 130, 246, 0.05);
        border: 1px solid rgba(59, 130, 246, 0.12);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #3b82f6;
    }

    .metric-label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1025 0%, #0a0e27 100%);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8;
    }

    /* Tab styling improvements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(13, 16, 37, 0.5);
        border-radius: 10px;
        padding: 0.3rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        font-weight: 500;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.01em;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
    }

    .stButton > button:hover {
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.5);
        transform: translateY(-1px);
    }

    /* Info boxes */
    .info-box {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.2);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.75rem 0;
        font-size: 0.9rem;
        color: #94a3b8;
    }

    /* Divider */
    .styled-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(59, 130, 246, 0.3) 50%, transparent 100%);
        margin: 1.5rem 0;
        border: none;
    }

    /* Hide default Streamlit footer */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0e27;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(59, 130, 246, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(59, 130, 246, 0.5);
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper: Load demo data
# ---------------------------------------------------------------------------
@st.cache_data
def load_demo_data() -> dict:
    """Load the built-in demo case data."""
    demo_path = os.path.join(os.path.dirname(__file__), "data", "demo_case.json")
    with open(demo_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Sidebar — Settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Model Configuration
    st.markdown("### 🧠 Models")
    model_summarizer_lm = st.text_input("Case Summarizer Model (LM Studio)", value=LLM_MODEL)
    model_summarizer_qwen = st.text_input("Case Summarizer Model (Qwen 14B)", value="qwen-14b")
    model_explainer_lm = st.text_input("Calculation Explainer Model (LM Studio)", value=LLM_MODEL)
    model_explainer_qwen = st.text_input("Calculation Explainer Model (Qwen 14B)", value="qwen-14b")
    model_advisor_lm = st.text_input("Action Advisor Model (LM Studio)", value=LLM_MODEL)
    model_advisor_qwen = st.text_input("Action Advisor Model (Qwen 14B)", value="qwen-14b")

    st.markdown(f"""
    <div class="info-box">
        <strong>API Endpoint:</strong><br>
        <code>{LLM_API_URL.split('//')[1].split('/')[0]}</code>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # Agent selection
    st.markdown("### 🤖 Agents")
    run_summarizer_lm = st.checkbox("📋 Case Summarizer (LM Studio)", value=True)
    run_summarizer_qwen = st.checkbox("📋 Case Summarizer (Qwen 14B)", value=True)
    run_explainer_lm = st.checkbox("🔢 Calculation Explainer (LM Studio)", value=True)
    run_explainer_qwen = st.checkbox("🔢 Calculation Explainer (Qwen 14B)", value=True)
    run_advisor_lm = st.checkbox("⚡ Action Advisor (LM Studio)", value=True)
    run_advisor_qwen = st.checkbox("⚡ Action Advisor (Qwen 14B)", value=True)

    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **AI Copilot for Caseworkers** v1.0

        A multi-agent AI system that helps caseworkers
        understand financial calculations in the Child
        Maintenance Service.

        **Agents:**
        - 📋 **Summarizer** — Case overview
        - 🔢 **Explainer** — Calculation breakdown
        - ⚡ **Advisor (LM Studio)** — Risk & recommendations
        - ⚡ **Advisor (Qwen 14B)** — Risk & recommendations

        Built with Streamlit + Python.
        """)


# ---------------------------------------------------------------------------
# Main Content — Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Copilot — Caseworker Assistant</h1>
    <p>Multi-Agent AI System for Child Maintenance Calculation Explanation & Case Advisory</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Content Layout
# ---------------------------------------------------------------------------
chat_col, main_col = st.columns([1.2, 2.5], gap="large")

with chat_col:
    st.markdown('''
    <div style="background: linear-gradient(145deg, #131836 0%, #0d1025 100%); 
                border: 1px solid rgba(59, 130, 246, 0.15); 
                border-radius: 12px; 
                padding: 1rem; 
                margin-bottom: 1rem;
                text-align: center;">
        <h3 style="margin: 0; color: #e2e8f0; font-size: 1.2rem;">💬 AI Assistant</h3>
        <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 0.3rem;">Ask questions about your cases</p>
    </div>
    ''', unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am your AI Copilot. Load a case and ask me any questions about calculations, risks, or summaries."}
        ]
        
    chat_container = st.container(height=550)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    if prompt := st.chat_input("Ask the AI Copilot..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        gateway = LLMGateway(api_key=LLM_API_KEY, api_url=LLM_API_URL, model=LLM_MODEL)
                        context = "No case data loaded yet."
                        if "case_data" in st.session_state and st.session_state["case_data"]:
                            context = json.dumps(st.session_state["case_data"])[:3000]
                        system_prompt = "You are a helpful AI Assistant for Child Maintenance caseworkers. Be concise and clear. Base your answer on the provided context if relevant."
                        user_msg = f"Context (Case Data snippet): {context}\n\nUser Question: {prompt}"
                        response = gateway.chat(system_prompt=system_prompt, user_message=user_msg)
                        reply = response.get("content", "I am unable to provide a response right now.")
                    except Exception as e:
                        reply = f"Sorry, there was an error: {e}"
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

with main_col:
    # ---------------------------------------------------------------------------
    # Case Data Input Section
    # ---------------------------------------------------------------------------
    st.markdown("### 📂 Case Data Workspace")

    # Adding a quick status dashboard to the UI as requested
    active_agents_count = sum([run_summarizer_lm, run_summarizer_qwen, run_explainer_lm, run_explainer_qwen, run_advisor_lm, run_advisor_qwen])
    st.markdown(f'''
    <div style="display: flex; gap: 1rem; margin-bottom: 1.5rem;">
        <div class="metric-card" style="flex: 1;">
            <div class="metric-label">System Status</div>
            <div class="metric-value" style="color: #22c55e;">Online</div>
        </div>
        <div class="metric-card" style="flex: 1;">
            <div class="metric-label">Active Agents</div>
            <div class="metric-value">{active_agents_count}</div>
        </div>
        <div class="metric-card" style="flex: 1;">
            <div class="metric-label">Model Endpoint</div>
            <div class="metric-value" style="font-size: 1.2rem;">Multi-Model</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    input_method = st.radio(
        "Choose input method:",
        ["📎 Load Demo Data", "📝 Paste JSON", "📁 Upload File"],
        horizontal=True,
        label_visibility="collapsed",
    )

    case_data = None

    if input_method == "📎 Load Demo Data":
        st.markdown('''
        <div class="info-box">
            💡 <strong>Demo Mode:</strong> Load a pre-built synthetic case with 2 cases under 1 master case.
            Case 1 has arrears (enforcement risk), Case 2 is clean with shared care.
        </div>
        ''', unsafe_allow_html=True)

        if st.button("🚀 Load Demo Data", use_container_width=True):
            case_data = load_demo_data()
            st.session_state["case_data"] = case_data
            st.success("✅ Demo data loaded successfully!")

    elif input_method == "📝 Paste JSON":
        json_input = st.text_area(
            "Paste case JSON:",
            height=250,
            placeholder='{\n  "masterCase": {\n    "id": "...",\n    "cases": [...]\n  }\n}',
        )
        if json_input:
            try:
                case_data = json.loads(json_input)
                st.session_state["case_data"] = case_data
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON: {e}")

    elif input_method == "📁 Upload File":
        uploaded_file = st.file_uploader(
            "Upload a JSON case file:",
            type=["json"],
            help="Upload a JSON file containing the case data.",
        )
        if uploaded_file:
            try:
                case_data = json.loads(uploaded_file.getvalue().decode("utf-8"))
                st.session_state["case_data"] = case_data
                st.success(f"✅ Loaded: {uploaded_file.name}")
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON in uploaded file: {e}")

    # Use cached case data if available
    if case_data is None and "case_data" in st.session_state:
        case_data = st.session_state["case_data"]


    # ---------------------------------------------------------------------------
    # Display loaded case data preview
    # ---------------------------------------------------------------------------
    if case_data:
        master = case_data.get("masterCase", case_data)
        cases = master.get("cases", [])
        nrp = master.get("nrp", {})

        # Metrics row
        total_arrears = sum(
            c.get("arrearsDetails", {}).get("totalArrearsBalance", 0)
            for c in cases
        )
        total_monthly = sum(
            c.get("calculations", {}).get("outputs", {}).get("totalMonthlySchedule", 0)
            for c in cases
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Master Case", master.get("masterCaseNumber", master.get("id", "N/A")))
        with col2:
            st.metric("Active Cases", len(cases))
        with col3:
            st.metric("Total Monthly", f"£{total_monthly:,.2f}")
        with col4:
            st.metric("Total Arrears", f"£{total_arrears:,.2f}",
                       delta="At Risk" if total_arrears > 500 else "OK",
                       delta_color="inverse" if total_arrears > 500 else "normal")

        # Expandable raw JSON viewer
        with st.expander("👁️ View Raw Case Data"):
            st.json(case_data)

        st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)


    # ---------------------------------------------------------------------------
    # Analyze Button & Agent Execution
    # ---------------------------------------------------------------------------
    if case_data:
        # Validate settings before allowing analysis
        can_analyze = True

        # Build agent list
        selected_agents = []
        if run_summarizer_lm:
            selected_agents.append("case_summarizer_lm")
        if run_summarizer_qwen:
            selected_agents.append("case_summarizer_qwen")
        if run_explainer_lm:
            selected_agents.append("calculation_explainer_lm")
        if run_explainer_qwen:
            selected_agents.append("calculation_explainer_qwen")
        if run_advisor_lm:
            selected_agents.append("action_advisor_lm")
        if run_advisor_qwen:
            selected_agents.append("action_advisor_qwen")

        if not selected_agents:
            st.warning("⚠️ Please select at least one agent in the sidebar.")
            can_analyze = False

        if can_analyze:
            analyze_col1, analyze_col2, analyze_col3 = st.columns([1, 2, 1])
            with analyze_col2:
                analyze_button = st.button(
                    "🧠 Analyze Case with AI Agents",
                    use_container_width=True,
                    type="primary",
                )

            if analyze_button:
                try:
                    # Create LLM Gateway
                    gateway = LLMGateway(
                        api_key=LLM_API_KEY,
                        api_url=LLM_API_URL,
                        model=LLM_MODEL,
                    )

                    # Create Orchestrator
                    orchestrator = AgentOrchestrator(gateway)

                    agent_models = {
                        "case_summarizer_lm": model_summarizer_lm,
                        "case_summarizer_qwen": model_summarizer_qwen,
                        "calculation_explainer_lm": model_explainer_lm,
                        "calculation_explainer_qwen": model_explainer_qwen,
                        "action_advisor_lm": model_advisor_lm,
                        "action_advisor_qwen": model_advisor_qwen,
                    }

                    # Run agents with progress
                    with st.spinner("🤖 AI Agents are analyzing the case in parallel..."):
                        results = orchestrator.run_all(
                            case_data=case_data,
                            agents=selected_agents,
                            agent_models=agent_models,
                        )

                    # Store results
                    st.session_state["results"] = results

                except LLMGatewayError as e:
                    st.error(f"❌ LLM Gateway Error: {e.message}")
                except Exception as e:
                    st.error(f"❌ Unexpected Error: {str(e)}")


    # ---------------------------------------------------------------------------
    # Results Display
    # ---------------------------------------------------------------------------
    if "results" in st.session_state:
        results = st.session_state["results"]
        overall_status = results["status"]

        # Status and timing header
        status_map = {
            "success": ("✅ All Agents Completed Successfully", "status-success"),
            "partial": ("⚠️ Partial Success — Some Agents Failed", "status-partial"),
            "error": ("❌ All Agents Failed", "status-error"),
        }
        status_text, status_class = status_map.get(overall_status, ("Unknown", ""))

        st.markdown(f'''
        <div style="display: flex; align-items: center; justify-content: space-between; margin: 1rem 0;">
            <span class="status-badge {status_class}">{status_text}</span>
            <span class="timing-pill">⏱️ Total: {results['total_time']}s</span>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

        # Tabbed results
        agent_results = results["results"]
        tab_names = []
        tab_keys = []

        if "case_summarizer_lm" in agent_results:
            tab_names.append("📋 Summary (LM)")
            tab_keys.append("case_summarizer_lm")
        if "case_summarizer_qwen" in agent_results:
            tab_names.append("📋 Summary (Qwen)")
            tab_keys.append("case_summarizer_qwen")
        if "calculation_explainer_lm" in agent_results:
            tab_names.append("🔢 Calc (LM)")
            tab_keys.append("calculation_explainer_lm")
        if "calculation_explainer_qwen" in agent_results:
            tab_names.append("🔢 Calc (Qwen)")
            tab_keys.append("calculation_explainer_qwen")
        if "action_advisor_lm" in agent_results:
            tab_names.append("⚡ Actions (LM)")
            tab_keys.append("action_advisor_lm")
        if "action_advisor_qwen" in agent_results:
            tab_names.append("⚡ Actions (Qwen)")
            tab_keys.append("action_advisor_qwen")

        if tab_names:
            tabs = st.tabs(tab_names)

            for tab, key in zip(tabs, tab_keys):
                with tab:
                    result = agent_results[key]
                    agent_status = result.get("status", "unknown")
                    agent_timing = results["timing"].get(key, 0)

                    # Agent card header
                    header_col1, header_col2 = st.columns([3, 1])
                    with header_col1:
                        agent_display_names = {
                            "case_summarizer_lm": "Case Summarizer Agent (LM Studio)",
                            "case_summarizer_qwen": "Case Summarizer Agent (Qwen 14B)",
                            "calculation_explainer_lm": "Calculation Explainer Agent (LM Studio)",
                            "calculation_explainer_qwen": "Calculation Explainer Agent (Qwen 14B)",
                            "action_advisor_lm": "Action Advisor Agent (LM Studio)",
                            "action_advisor_qwen": "Action Advisor Agent (Qwen 14B)",
                        }
                        st.markdown(f"**🤖 {agent_display_names.get(key, key)}**")
                    with header_col2:
                        badge_class = "status-success" if agent_status == "success" else "status-error"
                        st.markdown(
                            f'<span class="status-badge {badge_class}">{agent_status.upper()}</span> '
                            f'<span class="timing-pill">⏱️ {agent_timing}s</span>',
                            unsafe_allow_html=True,
                        )

                    st.markdown('<div class="styled-divider"></div>', unsafe_allow_html=True)

                    # Agent response content
                    st.markdown(result.get("content", "No content returned."))

                    # Usage info
                    usage = result.get("usage", {})
                    if usage:
                        with st.expander("📊 Token Usage"):
                            u_col1, u_col2, u_col3 = st.columns(3)
                            with u_col1:
                                st.metric("Prompt Tokens", usage.get("prompt_tokens", "N/A"))
                            with u_col2:
                                st.metric("Completion Tokens", usage.get("completion_tokens", "N/A"))
                            with u_col3:
                                st.metric("Total Tokens", usage.get("total_tokens", "N/A"))

    else:
        # Welcome state — no results yet
        if not case_data:
            st.markdown('''
            <div style="text-align: center; padding: 3rem 2rem; background: linear-gradient(145deg, #131836 0%, #0d1025 100%); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 12px;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🤖</div>
                <h2 style="color: #e2e8f0; font-weight: 600; margin-bottom: 0.5rem;">
                    Welcome to AI Copilot
                </h2>
                <p style="color: #64748b; font-size: 1.1rem; max-width: 500px; margin: 0 auto;">
                    Load case data using the options above, configure your API key
                    in the sidebar, then click <strong>Analyze</strong> to get started.
                </p>
                <div style="margin-top: 2rem;">
                    <div style="display: inline-flex; gap: 2rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem;">📋</div>
                            <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem;">Summarize</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem;">🔢</div>
                            <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem;">Explain</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem;">⚡</div>
                            <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem;">Advise (LM)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.5rem;">⚡</div>
                            <div style="color: #94a3b8; font-size: 0.8rem; margin-top: 0.3rem;">Advise (Qwen)</div>
                        </div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)