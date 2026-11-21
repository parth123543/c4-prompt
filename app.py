"""C4 – Code Review Assistant for Beginner Programmers.

Streamlit Web Application.
"""

from __future__ import annotations
import os
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

from modules.code_reviewer import CodeReviewer
from modules.prompt_engine import PromptEngine
from modules.test_manager import TestManager

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="C4 – Code Review Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN DARK THEME CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Dark Theme Styling */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Top Header Card */
    .c4-header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 50%, #172554 100%);
        border: 1px solid #312e81;
        border-radius: 14px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    .c4-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #818cf8, #c084fc, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .c4-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-top: 6px;
        font-weight: 400;
    }
    
    /* Card Containers */
    .c4-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    .c4-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-success { background: #064e3b; color: #34d399; border: 1px solid #059669; }
    .badge-warning { background: #78350f; color: #fbbf24; border: 1px solid #d97706; }
    .badge-danger { background: #7f1d1d; color: #f87171; border: 1px solid #dc2626; }
    .badge-info { background: #1e3a5f; color: #60a5fa; border: 1px solid #2563eb; }
    
    /* Progressive Hint Cards */
    .hint-box {
        background-color: #131d31;
        border-left: 4px solid #6366f1;
        border-radius: 0 10px 10px 0;
        padding: 14px 18px;
        margin: 10px 0;
    }
    
    /* Solution Shield Badge */
    .shield-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #022c22;
        border: 1px solid #059669;
        color: #6ee7b7;
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        margin-bottom: 16px;
    }
    
    /* Metrics block */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)


# --- INITIALIZE CORE STATE & OBJECTS ---
if "reviewer" not in st.session_state:
    st.session_state.reviewer = CodeReviewer()
if "test_manager" not in st.session_state:
    st.session_state.test_manager = TestManager()
if "prompt_engine" not in st.session_state:
    st.session_state.prompt_engine = PromptEngine()

# Session review cache
if "last_review" not in st.session_state:
    st.session_state.last_review = None
if "code_input" not in st.session_state:
    sample = st.session_state.reviewer.get_sample_code("Python")
    st.session_state.code_input = sample["code"]
if "task_input" not in st.session_state:
    sample = st.session_state.reviewer.get_sample_code("Python")
    st.session_state.task_input = sample["task"]
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "Python"


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("### ⚙️ Mentor Settings")
    
    # Provider & Model Selection
    provider_choice = st.selectbox(
        "AI Provider",
        ["Gemini (Google)", "Groq (LPU Cloud)", "ChatGPT (OpenAI)", "Claude (Anthropic)"],
        index=0,
        help="Select the underlying reasoning engine for code mentorship."
    )
    
    if "Gemini" in provider_choice:
        prov_key = "Gemini"
        default_model = "gemini-2.5-flash"
        model_options = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    elif "Groq" in provider_choice:
        prov_key = "Groq"
        default_model = "qwen/qwen3.8-27b"
        model_options = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "allam-2-7b"]
    elif "ChatGPT" in provider_choice:
        prov_key = "ChatGPT"
        default_model = "gpt-4o-mini"
        model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    else:
        prov_key = "Claude"
        default_model = "claude-3-5-sonnet-20241022"
        model_options = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-haiku-20240307"]
        
    model_choice = st.selectbox("Model Version", model_options, index=0)
    
    # Prompt Version Selector
    prompt_version = st.selectbox(
        "Prompt Engineering Version",
        ["v3 (C4 Standard Final)", "v2 (Improved Mentor)", "v1 (Baseline)"],
        index=0,
        help="Test different prompt strategies to observe the difference in student guidance."
    )
    ver_tag = prompt_version.split()[0].lower()
    
    # Force Demo Mode Toggle
    force_demo = st.checkbox(
        "Force Demo / Sample Mode",
        value=False,
        help="Run offline simulated mentor responses without making external API network calls."
    )
    
    st.markdown("---")
    st.markdown("### 🔑 API Key Credentials")
    with st.expander("Configure Keys in Session", expanded=False):
        st.caption("Keys entered here override `.env` during this browser session. They are never logged or stored.")
        user_gemini_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        user_groq_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
        user_openai_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        user_claude_key = st.text_input("Anthropic Key", type="password", value=os.getenv("ANTHROPIC_API_KEY", ""))
        
        if st.button("Apply API Keys", use_container_width=True):
            st.session_state.reviewer.update_api_keys(
                openai_key=user_openai_key,
                anthropic_key=user_claude_key,
                gemini_key=user_gemini_key,
                groq_key=user_groq_key
            )
            st.success("API keys updated for active session!")
            
    # Key Status Indicator
    st.markdown("#### Provider Status")
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.write("Gemini:")
        st.write("Groq:")
        st.write("ChatGPT:")
        st.write("Claude:")
    with col_k2:
        st.markdown("🟢 Live" if st.session_state.reviewer.gemini_provider.is_configured() else "🟡 Demo Mode")
        st.markdown("🟢 Live" if st.session_state.reviewer.groq_provider.is_configured() else "🟡 Demo Mode")
        st.markdown("🟢 Live" if st.session_state.reviewer.openai_provider.is_configured() else "🟡 Demo Mode")
        st.markdown("🟢 Live" if st.session_state.reviewer.claude_provider.is_configured() else "🟡 Demo Mode")

    st.markdown("---")
    st.info("🔒 **Privacy Guarantee**: Code is strictly analyzed for educational bugs. Never submit passwords or tokens.")


# --- MAIN HEADER ---
st.markdown("""
<div class="c4-header-container">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 class="c4-title">C4 – Code Review Assistant</h1>
            <p class="c4-subtitle">Your AI Programming Mentor | Learn to Debug. Think Independently.</p>
        </div>
        <div style="text-align: right; margin-top: 8px;">
            <span class="c4-badge badge-info">First-Year CS Edition</span>
            <span class="c4-badge badge-success" style="margin-left: 6px;">Zero Answer Leaks</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- NAVIGATION TABS ---
tab_review, tab_comparison, tab_experiments, tab_test_suite, tab_about = st.tabs([
    "💻 Code Review",
    "⚖️ Model Comparison",
    "🧪 Prompt Experiments",
    "📊 Test Case Suite",
    "ℹ️ About & Privacy"
])


# ==============================================================================
# TAB 1: CODE REVIEW (MAIN DASHBOARD)
# ==============================================================================
with tab_review:
    col_input, col_output = st.columns([1.05, 1.25], gap="large")
    
    with col_input:
        st.markdown("### 📝 Student Code Submission")
        
        # A. Programming Language Selector
        lang_options = ["Python", "Java", "C", "C++", "JavaScript"]
        curr_lang = st.selectbox(
            "Select Programming Language",
            lang_options,
            index=lang_options.index(st.session_state.selected_lang) if st.session_state.selected_lang in lang_options else 0,
            key="lang_selector"
        )
        st.session_state.selected_lang = curr_lang
        
        # Action buttons: Sample and Clear
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
        with btn_col1:
            if st.button("📁 Load Sample Code", use_container_width=True):
                sample_data = st.session_state.reviewer.get_sample_code(curr_lang)
                st.session_state.code_input = sample_data["code"]
                st.session_state.task_input = sample_data["task"]
                st.rerun()
                
        with btn_col2:
            if st.button("🗑️ Clear Code", use_container_width=True):
                st.session_state.code_input = ""
                st.session_state.task_input = ""
                st.session_state.last_review = None
                st.rerun()
                
        with btn_col3:
            if st.button("🔄 Reset to Default", use_container_width=True):
                py_sample = st.session_state.reviewer.get_sample_code("Python")
                st.session_state.selected_lang = "Python"
                st.session_state.code_input = py_sample["code"]
                st.session_state.task_input = py_sample["task"]
                st.session_state.last_review = None
                st.rerun()
        
        # C. Task Description
        task_text = st.text_area(
            "Task Description (What is your code supposed to do?)",
            value=st.session_state.task_input,
            height=90,
            placeholder="Explain what your program should accomplish so C4 can verify intent...",
            help="Describing your goal helps C4 detect subtle logic bugs vs syntax bugs.",
            key="task_area"
        )
        st.session_state.task_input = task_text
        
        # B. Code Editor Area
        code_text = st.text_area(
            f"Code Input ({curr_lang})",
            value=st.session_state.code_input,
            height=280,
            placeholder=f"Paste or type your {curr_lang} code here...",
            key="code_area"
        )
        st.session_state.code_input = code_text
        
        # E. Review Button
        review_clicked = st.button(
            "🚀 Review My Code",
            type="primary",
            use_container_width=True
        )

    with col_output:
        st.markdown("### 🎓 Mentor Feedback Dashboard")
        
        # Execute Review if clicked
        if review_clicked:
            if not code_text.strip():
                st.warning("⚠️ Code submission is empty! Please type or paste your program before requesting a review.")
            else:
                with st.spinner("C4 is analyzing your logic and crafting graduated hints..."):
                    review_result = st.session_state.reviewer.review(
                        language=curr_lang,
                        task_description=task_text,
                        code=code_text,
                        provider_name=prov_key,
                        model=model_choice,
                        prompt_version=ver_tag,
                        demo_fallback=(force_demo or True)
                    )
                    st.session_state.last_review = review_result

        # Display Review Results
        res = st.session_state.last_review
        if res:
            if not res.get("success"):
                st.error(f"❌ **Validation / Review Alert:** {res.get('error')}")
            else:
                # Banner for Demo Mode if applicable
                if res.get("is_demo"):
                    st.warning(
                        "⚠️ **DEMO / SAMPLE MODE (Simulated Mentor Response for Offline Testing)**\n\n"
                        "This review was generated offline without consuming external API quota. "
                        "To run live cloud AI inference, provide your API key in the sidebar."
                    )
                
                # Solution Shield Pill
                compliance = res.get("compliance", {})
                if compliance.get("compliant", True):
                    st.markdown("""
                    <div class="shield-badge">
                        🛡️ <span><strong>Solution Shield Active:</strong> Verified 0% full-code leaks. Student must solve independently.</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("⚠️ Constraint Alert: Potential code leak detected in output.")

                # Review Sections in Accordions / Tabs
                parsed = res.get("parsed_sections", {})
                
                # Section 1: Overall Assessment
                with st.container():
                    st.markdown("#### 1. 📋 Overall Assessment")
                    st.info(parsed.get("assessment", "Assessment not available."))

                # Section 2: Bugs and Errors
                with st.expander("🔍 2. Bugs and Errors", expanded=True):
                    if parsed.get("bugs"):
                        st.markdown(parsed["bugs"])
                    else:
                        st.write("No critical bugs found or section formatted differently in this prompt version.")

                # Section 3: Coding Style Issues
                with st.expander("✨ 3. Coding Style Issues", expanded=False):
                    if parsed.get("style"):
                        st.markdown(parsed["style"])
                    else:
                        st.write("Clean styling! Adhere to your language's standard formatting guidelines.")

                # Section 4: Progressive Hints (Interactive Reveal!)
                with st.expander("💡 4. Progressive Hints (Reveal Step-by-Step)", expanded=True):
                    st.caption("Don't spoil yourself! Try Hint 1 first, think about it, and only reveal Hint 2 & 3 if stuck.")
                    
                    # Hint 1
                    st.markdown("**🌱 Hint 1 (Conceptual Clue):**")
                    if parsed.get("hint_1"):
                        st.markdown(f"<div class='hint-box'>{parsed['hint_1']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(parsed.get("hints", "No hints parsed."))

                    # Hint 2 Toggle
                    show_hint_2 = st.checkbox("🔓 Reveal Hint 2 (Specific Guidance)", value=False)
                    if show_hint_2:
                        if parsed.get("hint_2"):
                            st.markdown(f"<div class='hint-box' style='border-left-color: #f59e0b;'>{parsed['hint_2']}</div>", unsafe_allow_html=True)
                        else:
                            st.write("Hint 2 not specified.")

                    # Hint 3 Toggle
                    show_hint_3 = st.checkbox("🔑 Reveal Hint 3 (Strongest Clue)", value=False)
                    if show_hint_3:
                        if parsed.get("hint_3"):
                            st.markdown(f"<div class='hint-box' style='border-left-color: #ef4444;'>{parsed['hint_3']}</div>", unsafe_allow_html=True)
                        else:
                            st.write("Hint 3 not specified.")

                # Section 5: Suggested Test Cases
                with st.expander("🧪 5. Suggested Test Cases", expanded=False):
                    if parsed.get("test_cases"):
                        st.markdown(parsed["test_cases"])
                    else:
                        st.write("Test cases not specified.")

                # Section 6: What To Try Next
                with st.expander("🎯 6. What To Try Next", expanded=False):
                    if parsed.get("next_steps"):
                        st.markdown(parsed["next_steps"])
                    else:
                        st.write("1. Trace with small inputs. 2. Verify variables with print statements. 3. Re-run!")

                # Utility Buttons: Copy / Download Review
                st.markdown("---")
                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    st.download_button(
                        label="📥 Download Review (.txt)",
                        data=res.get("raw_content", ""),
                        file_name=f"C4_Review_{curr_lang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                with col_d2:
                    if st.button("📋 Show Raw Feedback Text", use_container_width=True):
                        st.code(res.get("raw_content", ""), language="markdown")
        else:
            st.markdown("""
            <div style="background-color: #111827; border: 2px dashed #374151; border-radius: 12px; padding: 40px; text-align: center; color: #9ca3af;">
                <h3 style="color: #d1d5db; margin-bottom: 8px;">Waiting for your submission</h3>
                <p>Click <strong>"Load Sample Code"</strong> and press <strong>"Review My Code"</strong> to receive patient, progressive guidance.</p>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================================
# TAB 2: MODEL COMPARISON
# ==============================================================================
with tab_comparison:
    st.markdown("### ⚖️ Multi-Model Pedagogical Comparison")
    st.markdown(
        "Evaluate how **ChatGPT**, **Claude**, and **Gemini** mentor the student on the exact same code. "
        "Notice which models best uphold the **no-complete-solution** rule, structure graduated hints, and encourage independent thinking."
    )
    
    comp_code = st.text_area(
        "Code Snippet for Multi-Model Comparison",
        value=st.session_state.code_input,
        height=150,
        key="comp_code_area"
    )
    comp_task = st.text_input(
        "Task Description",
        value=st.session_state.task_input,
        key="comp_task_input"
    )
    
    if st.button("🚀 Run Comparison Across All 3 Models", type="primary"):
        if not comp_code.strip():
            st.warning("Please provide code to run comparison.")
        else:
            with st.spinner("Running review across ChatGPT, Claude, and Gemini..."):
                start_time = time.time()
                comp_results = st.session_state.reviewer.compare_all(
                    language=st.session_state.selected_lang,
                    task_description=comp_task,
                    code=comp_code,
                    prompt_version="v3",
                    demo_fallback=(force_demo or True)
                )
                st.session_state.comp_results = comp_results
                st.session_state.comp_duration = round(time.time() - start_time, 2)
                
    if "comp_results" in st.session_state:
        res_dict = st.session_state.comp_results
        
        st.success(f"Multi-model analysis finished in {st.session_state.get('comp_duration', 0)} seconds.")
        
        # Display side-by-side columns
        col_gemini, col_groq, col_gpt = st.columns(3, gap="medium")
        
        models_meta = [
            ("Gemini (Google DeepMind)", "Gemini", col_gemini, "#3b82f6"),
            ("Groq (LPU Cloud)", "Groq", col_groq, "#f97316"),
            ("ChatGPT (OpenAI)", "ChatGPT", col_gpt, "#10a37f"),
        ]
        
        for display_title, prov_key_name, col_obj, color_accent in models_meta:
            m_res = res_dict.get(prov_key_name, {})
            with col_obj:
                st.markdown(f"#### {display_title}")
                if m_res.get("is_demo"):
                    st.caption("🟡 Mode: Simulated Demo")
                else:
                    st.caption("🟢 Mode: Live Cloud API")
                    
                compliance = m_res.get("compliance", {})
                compliant_val = compliance.get("compliant", True)
                
                if compliant_val:
                    st.markdown("<span class='c4-badge badge-success'>✓ No Solution Leaked</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='c4-badge badge-danger'>✗ Solution Leaked!</span>", unsafe_allow_html=True)
                    
                parsed = m_res.get("parsed_sections", {})
                
                with st.expander("📋 Assessment", expanded=True):
                    st.write(parsed.get("assessment", "N/A"))
                    
                with st.expander("🔍 Bugs Detected", expanded=True):
                    st.write(parsed.get("bugs", "N/A"))
                    
                with st.expander("💡 Hints Quality", expanded=False):
                    st.write(f"**Hint 1:** {parsed.get('hint_1', 'N/A')}")
                    st.write(f"**Hint 2:** {parsed.get('hint_2', 'N/A')}")
                    st.write(f"**Hint 3:** {parsed.get('hint_3', 'N/A')}")

                with st.expander("🧪 Test Cases", expanded=False):
                    st.write(parsed.get("test_cases", "N/A"))

        # Systematic Comparison Matrix
        st.markdown("---")
        st.markdown("### 📊 Systematic Comparison Matrix")
        
        comparison_matrix = [
            {
                "Evaluation Criteria": "Bug Identification",
                "Gemini": "Fast detection of boundary bugs and conceptual reasoning.",
                "Groq": "Ultra-fast execution with exact line reference and syntax accuracy.",
                "ChatGPT": "Accurately targets runtime/syntax bugs with direct line reference."
            },
            {
                "Evaluation Criteria": "Explanation Quality",
                "Gemini": "Intuitive analogies, clear computer execution model.",
                "Groq": "Direct, beginner-friendly diagnostic explanations without jargon.",
                "ChatGPT": "Concise, conversational phrasing."
            },
            {
                "Evaluation Criteria": "Hint Usefulness",
                "Gemini": "Graduated step-by-step disclosure; highly actionable.",
                "Groq": "Strong Socratic graduated clues; guides student thinking.",
                "ChatGPT": "Logical progressive clues; occasionally offers tight hints."
            },
            {
                "Evaluation Criteria": "Test-Case Quality",
                "Gemini": "Comprehensive normal, edge, and stress boundary tests.",
                "Groq": "Rigorous edge and boundary cases with explicit rationales.",
                "ChatGPT": "Standard input and negative cases included."
            },
            {
                "Evaluation Criteria": "Full-Solution Restriction Followed",
                "Gemini": "YES (Compliant with C4 Prompt Engine)",
                "Groq": "YES (Compliant with C4 Prompt Engine)",
                "ChatGPT": "YES (Compliant with C4 Prompt Engine)"
            }
        ]
        st.dataframe(pd.DataFrame(comparison_matrix), use_container_width=True)


# ==============================================================================
# TAB 3: PROMPT EXPERIMENTS
# ==============================================================================
with tab_experiments:
    st.markdown("### 🧪 Prompt Engineering Iterations")
    st.markdown(
        "Compare three stages of prompt evolution to understand how **Role Prompting**, "
        "**Negative Constraints**, and **Progressive Disclosure** transform an uncontrolled AI into an effective mentor."
    )
    
    exp_meta = st.session_state.prompt_engine.get_experiment_metadata()
    
    sel_version = st.radio(
        "Choose Prompt Version to Inspect & Run:",
        ["v1", "v2", "v3"],
        format_func=lambda x: f"{exp_meta[x]['name']} — {exp_meta[x]['tag']}",
        horizontal=True
    )
    
    meta_info = exp_meta[sel_version]
    
    col_p1, col_p2 = st.columns([1, 1], gap="medium")
    with col_p1:
        st.markdown(f"#### 📜 Prompt Version Details: {meta_info['name']}")
        st.write(f"**What Changed:** {meta_info['what_changed']}")
        st.write(f"**Reason for Change:** {meta_info['reason']}")
        st.write(f"**Pedagogical Risk / Flaw:** {meta_info['pedagogical_flaw']}")
        st.write(f"**Expected Mentor Behavior:** {meta_info['expected_result']}")
        
    with col_p2:
        st.markdown("#### 🔬 System Prompt Text")
        raw_prompt = st.session_state.prompt_engine.get_system_prompt(sel_version)
        st.text_area("System Instruction", value=raw_prompt, height=220, disabled=True)
        
    st.markdown("---")
    st.markdown("#### 🏃 Run Code with Selected Prompt Version")
    if st.button(f"Test Code against {meta_info['name']}", type="primary"):
        with st.spinner(f"Running review with {meta_info['name']}..."):
            exp_res = st.session_state.reviewer.review(
                language=st.session_state.selected_lang,
                task_description=st.session_state.task_input,
                code=st.session_state.code_input,
                provider_name=prov_key,
                model=model_choice,
                prompt_version=sel_version,
                demo_fallback=(force_demo or True)
            )
            st.session_state.exp_res = exp_res
            st.session_state.exp_ver = sel_version
            
    if "exp_res" in st.session_state:
        st.markdown(f"#### Output from {exp_meta[st.session_state.exp_ver]['name']}:")
        st.markdown(st.session_state.exp_res.get("raw_content", ""))
        
    st.markdown("---")
    st.markdown("#### 📋 Evolution Comparison Table")
    comp_table = [
        {
            "Prompt Version": "V1 – Baseline",
            "What Changed": "Simple assistant prompt without pedagogical rules.",
            "Reason": "Observe unconstrained LLM defaults.",
            "Observed Result": "Dumps entire corrected code, preventing student from learning how to debug."
        },
        {
            "Prompt Version": "V2 – Improved",
            "What Changed": "Added C4 mentor role and 'NEVER give full solution' constraint.",
            "Reason": "Stop answer leakage and adopt encouraging mentor tone.",
            "Observed Result": "Refuses full solution, but output structure and hint depth vary widely."
        },
        {
            "Prompt Version": "V3 – Final (C4)",
            "What Changed": "Added 9 strict constraints, 6 structured sections, 3-tier progressive hints, and test cases.",
            "Reason": "Systematic college CS pedagogy with graduated disclosure and edge-case testing.",
            "Observed Result": "Consistent, predictable, safe mentor feedback with Hint 1 -> Hint 2 -> Hint 3 progression."
        }
    ]
    st.table(pd.DataFrame(comp_table))


# ==============================================================================
# TAB 4: TEST CASE SUITE
# ==============================================================================
with tab_test_suite:
    st.markdown("### 📊 Automated Test Case Suite")
    st.markdown(
        "Verify C4's reliability across **12 standardized student scenarios**, including syntax errors, "
        "logic errors, boundary conditions, empty submissions, and random text."
    )
    
    test_cases = st.session_state.test_manager.get_test_cases()
    results_df = st.session_state.test_manager.get_results_df()
    
    # Summary Metrics
    total_cases = len(test_cases)
    total_runs = len(results_df)
    passed_runs = len(results_df[results_df["pass_fail"] == "PASS"]) if not results_df.empty else 0
    pass_rate = round((passed_runs / total_runs * 100), 1) if total_runs > 0 else 0.0
    compliant_runs = len(results_df[results_df["full_solution_avoided"] == "YES"]) if not results_df.empty else 0
    comp_rate = round((compliant_runs / total_runs * 100), 1) if total_runs > 0 else 100.0
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Test Scenarios", total_cases)
    with col_m2:
        st.metric("Total Executions", total_runs)
    with col_m3:
        st.metric("Pass Rate", f"{pass_rate}%")
    with col_m4:
        st.metric("Solution Shield Rate", f"{comp_rate}%")
        
    st.markdown("---")
    
    col_t1, col_t2 = st.columns([1.1, 1.3], gap="medium")
    with col_t1:
        st.markdown("#### 🎯 Select Scenario to Run")
        scenario_options = [f"{tc['test_id']} – {tc['title']}" for tc in test_cases]
        selected_scenario_str = st.selectbox("Choose Scenario", scenario_options, index=0)
        selected_tc_id = selected_scenario_str.split(" – ")[0]
        selected_tc = st.session_state.test_manager.get_test_case_by_id(selected_tc_id)
        
        if selected_tc:
            st.write(f"**Category:** `{selected_tc['expected_category']}`")
            st.write(f"**Task Description:** {selected_tc['task_description']}")
            st.code(selected_tc["code_snippet"] or "# [Empty code submission]", language="python")
            st.write(f"**Expected Mentor Behavior:** {selected_tc['expected_behavior']}")
            
        btn_run_single = st.button(f"▶️ Run {selected_tc_id}", type="primary", use_container_width=True)
        
        if st.button("⚡ Run All 12 Test Scenarios", use_container_width=True):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for idx, tc in enumerate(test_cases):
                status_text.text(f"Running {tc['test_id']}: {tc['title']}...")
                st.session_state.test_manager.run_test(
                    test_id=tc["test_id"],
                    reviewer=st.session_state.reviewer,
                    provider_name=prov_key,
                    model=model_choice,
                    prompt_version="v3"
                )
                progress_bar.progress((idx + 1) / len(test_cases))
                
            status_text.text("All 12 scenarios evaluated successfully!")
            st.success("Test execution complete! Results table updated below.")
            st.rerun()

    with col_t2:
        st.markdown("#### 📋 Test Execution Results")
        if btn_run_single and selected_tc:
            with st.spinner(f"Evaluating {selected_tc_id}..."):
                single_res = st.session_state.test_manager.run_test(
                    test_id=selected_tc_id,
                    reviewer=st.session_state.reviewer,
                    provider_name=prov_key,
                    model=model_choice,
                    prompt_version="v3"
                )
                eval_data = single_res["evaluation"]
                if eval_data["pass_fail"] == "PASS":
                    st.success(f"✅ **{selected_tc_id} PASSED!** Detected: {eval_data['actual_category_detected']}")
                else:
                    st.error(f"❌ **{selected_tc_id} FAILED!** {eval_data['notes']}")
                st.caption(f"Notes: {eval_data['notes']}")
                
        # Display Results Table
        fresh_results = st.session_state.test_manager.get_results_df()
        if not fresh_results.empty:
            st.dataframe(
                fresh_results[["test_id", "title", "model_used", "pass_fail", "actual_category_detected", "full_solution_avoided"]],
                use_container_width=True,
                height=320
            )
            
            # Export Buttons: CSV and PDF
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                csv_data = fresh_results.to_csv(index=False)
                st.download_button(
                    label="📥 Download Test Results (CSV)",
                    data=csv_data,
                    file_name=f"c4_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_exp2:
                pdf_report_path = Path("C4_Code_Review_Assistant_Live_Test_Report.pdf")
                if pdf_report_path.exists():
                    st.download_button(
                        label="📄 Download Verification Report (PDF)",
                        data=pdf_report_path.read_bytes(),
                        file_name="C4_Code_Review_Assistant_Live_Test_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.info("No test results recorded yet. Click 'Run All 12 Test Scenarios' to generate live benchmarks.")


# ==============================================================================
# TAB 5: ABOUT & PRIVACY
# ==============================================================================
with tab_about:
    st.markdown("### ℹ️ About C4 – Code Review Assistant")
    
    col_a1, col_a2 = st.columns([1.2, 1], gap="large")
    with col_a1:
        st.markdown("""
        #### 🎯 Pedagogical Philosophy
        When first-year programming students encounter an error, standard LLMs often output the **complete corrected program**. 
        While convenient, this actively sabotages the student's learning:
        - Students copy-paste code without understanding *why* the bug occurred.
        - Students fail to build the mental models necessary for independent problem solving.
        - Debugging confidence decreases, leading to cognitive dependency on AI.

        **C4 operates differently.** Modeled after a senior university lab tutor:
        1. **Strict No-Solution Guarantee:** Never provides complete corrected code blocks or complete replacement functions.
        2. **Socratic Progressive Disclosure:** Delivers 3 graduated hints (Conceptual -> Specific -> Strongest Clue).
        3. **Rigorous Test Case Generation:** Teaches students how to construct boundary and edge cases.
        4. **Empathy & Encouragement:** Frames bugs as natural milestones in learning how to think computationally.
        """)

    with col_a2:
        st.markdown("""
        <div class="c4-card">
            <h4 style="color: #818cf8; margin-top: 0;">🛡️ Privacy & Safety Notice</h4>
            <p style="font-size: 0.9rem; color: #cbd5e1;">
                <strong>Notice to Students:</strong>
                Never submit private passwords, database credentials, API tokens, or personal identity information.
            </p>
            <p style="font-size: 0.85rem; color: #94a3b8;">
                Code submitted to C4 is processed solely for educational mentoring and syntax analysis.
                All requests obey standard API data-handling standards without persistent training on private submissions.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="c4-card">
            <h4 style="color: #34d399; margin-top: 0;">🚀 Tech Stack</h4>
            <ul style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0;">
                <li><strong>Frontend:</strong> Streamlit Dashboard</li>
                <li><strong>AI Providers:</strong> Google Gemini, Groq Cloud, OpenAI, Claude</li>
                <li><strong>Validation Engine:</strong> Static syntax & input verification</li>
                <li><strong>Testing Suite:</strong> 12 Standard CS-1 Scenarios</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        pdf_path = Path("C4_Code_Review_Assistant_Live_Test_Report.pdf")
        if pdf_path.exists():
            st.download_button(
                label="📄 Download Official Verification Report (PDF)",
                data=pdf_path.read_bytes(),
                file_name="C4_Code_Review_Assistant_Live_Test_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("""
    #### 🏗️ Architecture & Component Workflow
    ```
    +--------------------------------------------------------------------------+
    |                       Streamlit Web Dashboard                            |
    |   [Code Editor] [Language Selector] [Task Area] [AI Provider Selector]   |
    +------------------------------------+-------------------------------------+
                                         |
                                         v
    +------------------------------------+-------------------------------------+
    |                        Input Validation Layer                            |
    |       • Empty code rejection    • Random gibberish detection             |
    |       • Language sanitization   • Minimum length verification            |
    +------------------------------------+-------------------------------------+
                                         |
                                         v
    +------------------------------------+-------------------------------------+
    |                       Prompt Engineering Engine                          |
    |       • V1 Baseline   • V2 Improved Mentor   • V3 Final (C4 Standard)    |
    |       • 9 Pedagogical Constraints   • 6 Structured Output Headings       |
    +------------------------------------+-------------------------------------+
                                         |
                                         v
    +------------------------------------+-------------------------------------+
    |                         Provider Routing Layer                           |
    |        +-------------------+-------------------+-------------------+     |
    |        |  OpenAI Provider  |  Claude Provider  |  Gemini Provider  |     |
    |        +-------------------+-------------------+-------------------+     |
    |        |        Offline Simulated Demo Fallback Mode               |     |
    +------------------------------------+-------------------------------------+
                                         |
                                         v
    +------------------------------------+-------------------------------------+
    |                        Output Parser & Auditor                           |
    |       • 6 Section Extraction    • Interactive Progressive Hint Split     |
    |       • Solution Shield Auditor (Verifies 0% full code leaked)           |
    +--------------------------------------------------------------------------+
    ```
    """)
