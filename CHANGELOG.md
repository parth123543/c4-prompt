# Changelog — C4 Code Review Assistant

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-11-21

### Added
- **Core Streamlit Dashboard**: Dark-themed modern interface with language selector (Python, Java, C, C++, JavaScript), code editor, task description input, and model selector.
- **AI Integrations**:
  - OpenAI provider supporting `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo`.
  - Anthropic provider supporting `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`.
  - Google Gemini provider supporting `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`.
- **Pedagogical Prompt Engine**:
  - Implementation of 3 prompt versions: V1 Baseline, V2 Improved, V3 Final.
  - Strict enforcement of 9 negative constraints against full code leakage.
  - Standardized 6-section structured output format.
- **Solution Shield Auditor**: Automated check verifying that mentor responses do not leak complete replacement functions.
- **Progressive Hint Disclosure**: Interactive step-by-step reveal of Hint 1 (Conceptual), Hint 2 (Specific Guidance), and Hint 3 (Strongest Clue).
- **Multi-Model Comparison Tab**: Side-by-side analysis of ChatGPT, Claude, and Gemini with systematic comparison matrix.
- **Prompt Experiments Tab**: Comparative prompt laboratory with real-time prompt text inspector and evolution comparison table.
- **Automated Test Suite**: 12 pre-configured test scenarios with transparent pass/fail logging and CSV export.
- **Demo / Offline Fallback Mode**: Intelligent simulated mentor responses when API keys are not supplied.
- **Automated Unit Tests**: 15 pytest unit tests covering prompt formatting, input validation, and provider fallback behavior.
- **Documentation**: Comprehensive `README.md`, `docs/architecture.md`, and `docs/workflow.md`.
