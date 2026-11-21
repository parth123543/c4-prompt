# C4 – Code Review Assistant for Beginner Programmers

> **Your AI Programming Mentor | Learn to Debug. Think Independently.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-SDK-412991.svg)](https://platform.openai.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-D97706.svg)](https://www.anthropic.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-4285F4.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen.svg)]()

---

## 1. Project Overview

**C4 (Code Review Assistant)** is an AI-powered programming mentor designed specifically for first-year computer science students. Rather than acting like a conventional chatbot that simply rewrites broken code, C4 acts like an experienced, patient lab instructor: it diagnoses errors, explains the underlying computer science concepts in beginner-friendly language, and provides **progressive graduated hints** to empower students to fix the bugs themselves.

---

## 2. Problem Statement

When novice programmers encounter bugs, they often paste their code into standard AI chatbots. Conventional LLMs typically generate the **complete corrected program**. While this provides immediate gratification, it creates critical pedagogical flaws:

1. **Cognitive Dependency:** Students copy and paste code without understanding *why* the bug occurred.
2. **Loss of Debugging Skills:** Debugging is 80% of professional software engineering; unconstrained AI robs students of this practice.
3. **Overwhelming Technical Jargon:** Standard compiler messages and raw AI outputs can intimidate novices.

**C4 solves this** through strict prompt engineering, negative constraints ("Solution Shield"), and Socratic progressive hint disclosure.

---

## 3. Key Features

- **🛡️ Solution Shield (Zero Answer Leaks):** Enforces 9 strict constraints that prevent the AI from generating complete replacement functions or complete corrected programs.
- **💡 3-Tier Progressive Hints:**
  - *Hint 1 (Conceptual Clue):* High-level concept or mental model.
  - *Hint 2 (Specific Guidance):* Line-specific guiding diagnostic questions.
  - *Hint 3 (Strongest Clue):* Thought patterns or pseudo-code clues without writing the final answer.
- **🌐 5 Supported Programming Languages:** Python, Java, C, C++, and JavaScript with pre-loaded beginner bug samples.
- **🤖 Multi-Provider AI Support:**
  - **Gemini** (via Google GenAI API)
  - **Groq** (via Groq Cloud LPU)
  - **ChatGPT** (via OpenAI API)
  - **Claude** (via Anthropic API)
- **⚖️ Side-by-Side Model Comparison:** Submit identical code to ChatGPT, Claude, and Gemini simultaneously to evaluate differences in pedagogical tone, hint quality, and constraint compliance.
- **🧪 Prompt Engineering Laboratory:** Inspect and test code against **V1 Baseline**, **V2 Improved**, and **V3 Final (C4 Standard)** prompts to observe the evolution of mentor guidance.
- **📊 12 Automated Test Scenarios:** Built-in benchmarking suite covering syntax errors, off-by-one loops, zero division, empty collections, empty input, and non-code keyboard smashing.
- **🔒 Privacy-First Design:** Clear student warnings; zero persistent logging of private credentials or student code submissions.
- **🟡 Intelligent Demo / Offline Mode:** Fully functional offline simulation mode for live college presentations without requiring active cloud API credits.

---

## 4. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend UI** | [Streamlit](https://streamlit.io/) (Custom Dark Dashboard) |
| **Backend / Core** | Python 3.10+ |
| **AI Integrations** | `google-genai` (Gemini), `openai` / Groq Cloud LPU, `anthropic` (Claude) |
| **Environment & Config** | `python-dotenv` |
| **Data & Benchmarking** | `pandas` |
| **Automated Testing** | `pytest` |

---

## 5. Project Folder Structure

```
C4-Code-Review-Assistant/
│
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive project documentation
├── CHANGELOG.md                # Release notes and version history
├── .env.example                # Template for API credentials
├── .gitignore                  # Git exclusion rules
│
├── modules/                    # Modular core components
│   ├── __init__.py
│   ├── openai_provider.py      # OpenAI / ChatGPT API wrapper
│   ├── claude_provider.py      # Anthropic / Claude API wrapper
│   ├── gemini_provider.py      # Google Gemini API wrapper
│   ├── groq_provider.py        # Groq Cloud LPU API wrapper
│   ├── prompt_engine.py        # System prompt registry & validation
│   ├── code_reviewer.py        # Central orchestrator & output parser
│   ├── demo_generator.py       # Offline simulated demo mentor
│   └── test_manager.py         # 12-scenario test suite manager
│
├── prompts/                    # Versioned prompt artifacts
│   ├── v1/system_prompt.txt    # Baseline unconstrained prompt
│   ├── v2/system_prompt.txt    # Role prompting + negative constraints
│   ├── v3/system_prompt.txt    # Final C4 prompt (6 structured sections)
│   └── final/system_prompt.txt # Production prompt
│
├── test-data/                  # Persistent test datasets
│   ├── test_cases.csv          # 12 standard CS-1 student scenarios
│   └── test_results.csv        # Evaluated execution logs
│
├── docs/                       # Technical documentation
│   ├── architecture.md         # System architecture & Mermaid diagrams
│   └── workflow.md             # Student journey & testing workflows
│
└── tests/                      # Automated unit tests
    ├── test_prompt_engine.py   # Tests prompt loading & leakage audit
    ├── test_validation.py      # Tests empty code & gibberish checks
    └── test_providers.py       # Tests provider fallbacks & demo modes
```

---

## 6. Installation Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Git (optional, for cloning).

### Step 1: Clone or Navigate to the Project
```bash
cd "C4 CODE REVIEW ASSISTANT"
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. API Key Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Open `.env` in any text editor and add your API keys:
```env
# OpenAI API Key (ChatGPT)
OPENAI_API_KEY=sk-proj-yourOpenAIKeyHere

# Anthropic API Key (Claude)
ANTHROPIC_API_KEY=sk-ant-yourClaudeKeyHere

# Google Gemini API Key (Gemini)
GEMINI_API_KEY=AIzaSyYourGeminiKeyHere
```

> **Note:** If you do not have API keys, C4 includes an **Intelligent Demo / Offline Mode**. The application will automatically use realistic simulated mentor feedback so you can test all features without API credits!

You can also enter API keys directly into the **Sidebar Settings** during a live demonstration without editing any files.

---

## 8. How to Run the Application

Execute the following command in your terminal:

```bash
python -m streamlit run app.py
```

Streamlit will launch local server at:
```
Local URL: http://localhost:8501
Network URL: http://<your-ip>:8501
```

Open your browser to `http://localhost:8501`.

---

## 9. How to Test the Application

### Running Automated Unit Tests
To run the automated test suite verifying prompt generation, validation, and demo fallbacks:

```bash
python -m pytest -v
```

Expected output:
```
tests/test_prompt_engine.py::test_prompt_engine_initialization PASSED
tests/test_prompt_engine.py::test_get_system_prompt_versions PASSED
tests/test_prompt_engine.py::test_build_user_prompt PASSED
tests/test_prompt_engine.py::test_solution_leakage_detector PASSED
tests/test_providers.py::test_openai_unconfigured_demo_fallback PASSED
tests/test_providers.py::test_claude_unconfigured_demo_fallback PASSED
tests/test_providers.py::test_gemini_unconfigured_demo_fallback PASSED
tests/test_providers.py::test_code_reviewer_pipeline PASSED
tests/test_providers.py::test_test_manager_cases_loaded PASSED
tests/test_providers.py::test_test_manager_run_tc10_empty_code PASSED
tests/test_validation.py::test_empty_code_validation PASSED
tests/test_validation.py::test_short_code_validation PASSED
tests/test_validation.py::test_random_text_validation PASSED
tests/test_validation.py::test_valid_code_validation PASSED
tests/test_validation.py::test_reviewer_parse_sections PASSED
============================= 15 passed in 3.86s ==============================
```

### Running the 12 Prepared Pedagogical Scenarios
1. Launch the web app (`python -m streamlit run app.py`).
2. Go to the **📊 Test Case Suite** tab.
3. Click **"Run All 12 Test Scenarios"** or test any single scenario.
4. Download the generated CSV report for your project presentation.

---

## 10. Team Contribution Placeholders

- **Lead Full-Stack Developer & AI Specialist:** [Your Name / Team Member 1]
- **Prompt Engineering & Pedagogical Design:** [Team Member 2]
- **Frontend / UI-UX Designer:** [Team Member 3]
- **QA & Test Automation Specialist:** [Team Member 4]

---

## 11. License & Academic Integrity

This project is developed for educational purposes under the MIT License. It is intended to foster independent computational thinking in academic institutions.
